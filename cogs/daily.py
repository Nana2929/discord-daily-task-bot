# %%
from datetime import datetime, timedelta
from typing import Dict, List
from discord.ext import commands
from discord.ext.commands import Context
from api import checks
import discord
from discord import ui
from discord import app_commands
from discord.ext.forms import Form, Validator, ReactionForm, ReactionMenu
import math
import api.daily as daily_adapter
import api.user as user_adapter
import api.subscribe as subscribe_adapter
import pytz
from helpers.utils import get_current_time, is_the_same_date





class DailyDoneView(ui.View):

    def __init__(self, ctx: Context, **kwargs):

        super().__init__(**kwargs)
        tasks = daily_adapter.get_task({"server_id": str(ctx.guild.id)})
        task_id_to_task = {task["id"]: task for task in tasks}

        select_options = ui.Select(
            placeholder="請選擇要簽到的每日任務",
            min_values=1,
            max_values=len(tasks))

        for task in tasks:
            select_options.add_option(
                label=f"📌 {task['name']} {task['description'][:10]}",
                value=task["id"]
            )

        async def callback(interaction: discord.Interaction):

            # list of int task id
            selected_values = [int(v) for v in select_options.values]

            user_histories = daily_adapter.get_history(
                {
                    "user_id": str(ctx.author.id),
                    "server_id": str(ctx.guild.id)
                }
            )

            task_id_to_history = {
                user_history["task_id"]["id"]: user_history for user_history in user_histories}

            now = get_current_time()
            today = now.strftime("%Y-%m-%d")
            yesterday = (now - timedelta(days=1)
                         ).strftime("%Y-%m-%d")

            embed = discord.Embed(
                title="簽到紀錄",
                color=discord.Color.green()
            )

            for task_id in selected_values:

                task = task_id_to_task[task_id]
                ok = False
                # if history exists, history will be updated
                history = task_id_to_history.get(
                    task_id,
                    {
                        "user_id": str(ctx.author.id),
                        "task_id": str(task_id),
                        "server_id": str(ctx.guild.id),
                        "last_check": now,
                        "accumulate": 1,
                        "consecutive": 1
                    }
                )
                if "id" in history.keys():

                    if is_the_same_date(history["last_check"], today):
                        embed.add_field(
                            name=f"您今天已經簽到過 {task['name']} 了",
                            value=f"累計簽到 {history['accumulate']} 天\n連續簽到 {history['consecutive']} 天",
                            inline=False
                        )
                        continue

                    history["accumulate"] += 1
                    if is_the_same_date(history["last_check"], yesterday()):
                        history["consecutive"] += 1
                    else:
                        history["consecutive"] = 1
                    ok = daily_adapter.update_history(**history)
                else:
                    ok = daily_adapter.add_history(**history)

                if ok:
                    embed.add_field(
                        name=f"簽到 {task['name']} 成功",
                        value=f"累計簽到 {history['accumulate']} 天\n連續簽到 {history['consecutive']} 天",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"簽到 {task['name']} 失敗",
                        value="請聯絡管理員",
                        inline=False
                    )

            await interaction.response.send_message(embed=embed)

        select_options.callback = callback
        self.add_item(select_options)


class DailyAddModal(ui.Modal):
    def __init__(self, title="新增 daily", **kwargs):

        super().__init__(title=title)

        self.add_item(ui.TextInput(
            label="Name",
            required=True,
            max_length=127
        ))
        self.add_item(ui.TextInput(
            label="Description",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=255
        ))

    async def on_submit(self, interaction: discord.Interaction):

        name = self.children[0].value
        description = self.children[1].value
        user_id = interaction.user.id
        server_id = interaction.guild.id

        print(name, description, user_id, server_id)

        if daily_adapter.add_task(
            user_id=str(user_id),
            server_id=str(server_id),
            name=str(name),
            description=str(description)
        ):
            embed = discord.Embed(
                title="新增 daily 成功",
                description=f"Name: {name}\nDescription: {description}",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(
                content=None, view=None, embed=embed)
        else:
            await interaction.response.edit_message(
                content=f"新增 daily 失敗", view=None)


class DailySubscribeView(ui.View):

    def __init__(self, ctx: Context) -> None:
        super().__init__()

        self.tasks = daily_adapter.get_task({"server_id": str(ctx.guild.id)})

        if len(self.tasks) == 0:
            return

        user_info = user_adapter.get_user(user_id=ctx.author.id)

        task_id_to_task = {task["id"]: task for task in self.tasks}
        select_options = ui.Select(
            placeholder="請選擇要訂閱的每日任務",
            min_values=1,
            max_values=len(self.tasks))

        for task in self.tasks:
            select_options.add_option(
                label=f"📌 {task['name']} {task['description'][:10]}",
                value=task["id"]
            )

        async def callback(interaction: discord.Interaction):
            # list of int task id
            selected_task_ids = [int(v) for v in select_options.values]
            selected_task_infos = {task_id: task_id_to_task[task_id]
                                   for task_id in selected_task_ids}

            modal = SubscribeAddModal(
                selected_task_infos=selected_task_infos, user_time_zone=user_info["time_zone"])
            await interaction.response.send_modal(modal)

        select_options.callback = callback

        self.add_item(select_options)


class DailyUnsubscribeView(ui.View):
    def __init__(self, ctx: Context) -> None:
        super().__init__()

        subscribes = subscribe_adapter.get_subscribe(
            user_id=str(ctx.author.id), server_id=str(ctx.guild.id))

        subscribe_id_to_subscribe = {
            sub["id"]: sub for sub in subscribes}

        if len(subscribes) == 0:
            return

        options = ui.Select(
            placeholder="請選擇要取消訂閱的每日任務",
            min_values=1,
            max_values=len(subscribes)
        )

        print("==================", subscribes)

        for sub in subscribes:
            options.add_option(
                label=f"📌 {sub['task_id']['name']} {sub['task_id']['description'][:10]}",
                value=sub["id"]
            )

        async def callback(interaction: discord.Interaction):

            embed = discord.Embed(
                title="以下是取消訂閱的項目",
                color=discord.Colour.lighter_gray()
            )

            for value in options.values:
                if subscribe_adapter.delete_subscribe(id=value):
                    embed.add_field(
                        name=f"🔕 取消訂閱 {subscribe_id_to_subscribe[int(value)]['task_id']['name']} 成功",
                        value="",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"🔕 取消訂閱 {subscribe_id_to_subscribe[int(value)]['task_id']['name']} 失敗",
                        value="請聯絡管理員",
                        inline=False
                    )

            await interaction.response.edit_message(
                content=None, view=None, embed=embed)

        options.callback = callback
        self.add_item(options)


class SubscribeAddModal(ui.Modal):
    def __init__(self, selected_task_infos: Dict[int, Dict], user_time_zone: int, title="設定譴責及提醒時間 📆", **kwargs):
        super().__init__(title=title)

        self.add_item(ui.TextInput(
            label="譴責時間(0~23)",
            required=True,
            min_length=1,
            max_length=2
        ))
        self.add_item(ui.TextInput(
            label="提醒時間(0~23)",
            min_length=1,
            required=True,
            max_length=2
        ))
        self.user_time_zone = user_time_zone
        self.selected_task_infos = selected_task_infos

    async def on_submit(self, interaction: discord.Interaction):

        remind_time, condemn_time = self.children[0].value, self.children[1].value

        if not remind_time.isdigit() or not condemn_time.isdigit():
            await interaction.response.edit_message(
                content=f"格式錯誤!請輸入數字 0~23", view=None)
            return

        remind_time, condemn_time = int(remind_time), int(condemn_time)

        if remind_time not in range(24) or condemn_time not in range(24):
            await interaction.response.edit_message(
                content=f"格式錯誤!請輸入數字 0~23", view=None)
            return

        user_subscribes = {
            subscribe["task_id"]['id']: subscribe for subscribe in
            subscribe_adapter.get_subscribe(
                user_id=interaction.user.id,
                server_id=interaction.guild.id
            )
        }

        embed = discord.Embed(
            title=f"提醒時間: {remind_time}點\n譴責時間: {condemn_time}點",
            color=discord.Color.yellow()
        )

        for task_id in self.selected_task_infos.keys():

            subscribe = user_subscribes.get(
                task_id,
                {
                    "task_id": task_id,
                    "user_id": interaction.user.id,
                    "server_id": interaction.guild.id,
                }
            )

            subscribe["remind_time"] = (
                remind_time - self.user_time_zone + 24) % 24
            subscribe["condemn_time"] = (
                condemn_time - self.user_time_zone + 24) % 24

            if "id" in subscribe:  # update
                if subscribe_adapter.update_subscribe(**subscribe):
                    embed.add_field(
                        name=f"🔄 更新 {self.selected_task_infos[task_id]['name']} 成功",
                        value="",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"🔄 更新 {self.selected_task_infos[task_id]['name']} 失敗",
                        value="窩不知道...",
                        inline=False
                    )
            else:
                if subscribe_adapter.add_subscribe(**subscribe):
                    embed.add_field(
                        name=f"🔔 訂閱 {self.selected_task_infos[task_id]['name']} 成功",
                        value="",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"🔔 訂閱 {self.selected_task_infos[task_id]['name']} 失敗",
                        value="窩不知道...",
                        inline=False
                    )
        return await interaction.response.edit_message(
            content=None, view=None, embed=embed)


class Daily(commands.Cog, name="daily", description=""):

    def __init__(self, bot):
        self.bot = bot

    @ commands.hybrid_group(
        name="daily",
        description="",
    )
    @ checks.user_registered()
    async def daily(self, ctx: Context):

        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed...")

    @ daily.command(
        name="add",
        description="新增 daily task",
    )
    @ checks.user_registered()
    async def daily_add(self, ctx: Context):

        view = ui.View()
        open_button = ui.Button(
            label="點我新增 daily", style=discord.ButtonStyle.primary)

        async def callback(interaction: discord.Interaction):
            modal = DailyAddModal()
            await interaction.response.send_modal(modal)

        open_button.callback = callback
        view.add_item(open_button)

        await ctx.send(view=view)

    @ daily.command(
        name="listall",
        description="列出所有 daily task",
    )
    @ checks.user_registered()
    async def daily_listall(self, ctx: Context):

        tasks_in_server = daily_adapter.get_task(
            {"server_id": str(ctx.guild.id)})

        embed = discord.Embed(
            title="所有 daily task",
            description=f"共有 {len(tasks_in_server)} 個 task",
            color=discord.Color.green()
        )

        for task in tasks_in_server:

            user = await self.bot.fetch_user(int(task["created_by"]))
            embed.add_field(
                name=f"{task['name']}: {task['description']}",
                value=f"建立者: {user.mention}",
                inline=False
            )
        await ctx.send(embed=embed)

    @ daily.command(
        name="listmine",
        description="列出自己的 daily task",
    )
    @ checks.user_registered()
    async def daily_listmine(self, ctx: Context):

        tasks = daily_adapter.get_task(
            {
                "created_by": str(ctx.author.id),
                "server_id": str(ctx.guild.id)
            }
        )

        embed = discord.Embed(
            title="以下是您建立的 daily task",
            description=f"共有 {len(tasks)} 個 task",
            color=discord.Color.green()
        )

        for task in tasks:

            user = await self.bot.fetch_user(int(task["created_by"]))

            embed.add_field(
                name=f"{task['name']}: {task['description']}",
                value=f"建立者: {user.mention}",
                inline=False
            )
        await ctx.send(embed=embed)

    @ daily.command(
        name="done",
        description="簽到任務",
    )
    @ checks.user_registered()
    async def daily_done(self, ctx: Context):
        await ctx.send(view=DailyDoneView(ctx=ctx))

    @ daily.command(
        name="subscribe",
        description="訂閱每日任務通知",
    )
    @ checks.user_registered()
    async def daily_suscribe(self, ctx: Context):

        view = DailySubscribeView(ctx=ctx)

        if len(view.tasks) == 0:
            await ctx.send("目前沒有任何任務可以訂閱")
        else:
            await ctx.send(view=DailySubscribeView(ctx=ctx))

    @ daily.command(
        name="unsubscribe",
        description="取消訂閱每日任務通知",
    )
    @ checks.user_registered()
    async def daily_unsuscribe(self, ctx: Context):

        view = DailyUnsubscribeView(ctx=ctx)

        await ctx.send(view=view)

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.


async def setup(bot):
    await bot.add_cog(Daily(bot))
