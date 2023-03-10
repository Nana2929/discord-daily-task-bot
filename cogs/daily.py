# %%
from typing import List
from datetime import datetime

from discord.ext import commands
from discord.ext.commands import Context
from helpers import checks
from helpers.utils import ButtonCheck
import discord
from discord import ui
from discord import app_commands
from discord.ext.forms import Form, Validator, ReactionForm, ReactionMenu
import math
import api.daily as daily_adapter

# %%
# from utils.logger import L


def time_conversion(t: str):
    return datetime.fromisoformat(t)


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


class Daily(commands.Cog, name="daily", description=""):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="daily",
        description="每日任務",
    )
    @checks.not_blacklisted()
    async def daily(self, context: Context):

        if context.invoked_subcommand is None:
            description = """
                Please specify a subcommand.\n
                `add` - 新增一個每日任務。\n
                `delete` - 刪除你所創建的每日任務。\n
                `listall` - 列出所有每日任務。\n
                `listmine` - 列出你所創建的每日任務。\n
                =========================\n
                `subscribe` - 訂閱，即開啟每日任務提醒功能\n
                `unsubscribe` - 取消訂閱，即關閉每日任務功能。\n
                `listsub` - 列出所有自己訂閱的每日任務。\n
                =========================\n
                `done` - 簽到一個每日任務。\n
                `listdone` - 列出你今日簽到的每日任務。\n
            """
            embed = discord.Embed(title="Daily",
                                  description=description,
                                  color=discord.Color.blurple())
            await context.send(embed=embed)

    @daily.command(
        name="add",
        description="新增每日任務",
    )
    @checks.not_blacklisted()
    async def daily_add(self, ctx: Context):

        view = ui.View()
        open_button = ui.Button(label="點我新增每日任務", style=discord.ButtonStyle.primary)

        async def callback(interaction: discord.Interaction):
            modal = DailyAddModal()
            await interaction.response.send_modal(modal)

        open_button.callback = callback
        view.add_item(open_button)

        await ctx.send(view=view)

    @daily.command(
        name="listall",
        description="列出所有 daily task",
    )
    @checks.not_blacklisted()
    async def daily_listall(self, ctx: Context):

        tasks_in_server = daily_adapter.get_task(
            {"server_id": str(ctx.guild.id)}
        )

        embed = discord.Embed(
            title="所有 daily task",
            description=f"共有 {len(tasks_in_server)} 個 task",
            color=discord.Color.green()
        )

        for task in tasks_in_server:

            user = await self.bot.fetch_user(int(task["created_by"]))
            embed.add_field(
                name=f"{task['name']} ",
                value=f"{user.mention}\n{task['description']}\n-----",
                inline=False
            )
        await ctx.send(embed=embed)

    @daily.command(
        name="listmine",
        description="列出自己的 daily task",
    )
    @checks.not_blacklisted()
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
                name=f"{task['name']} ",
                value=f"{user.mention}\n{task['description']}\n-----",
                inline=False
            )
        await ctx.send(embed=embed)

    @daily.command(
        name="done",
        description="簽到任務",
    )
    @checks.not_blacklisted()
    async def daily_done(self, ctx: Context):

        tasks = daily_adapter.get_task(
            {
                "server_id": str(ctx.guild.id)
            }
        )

        view = ui.View()
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

            selected_values = select_options.values  # list of task id

            user_historys = daily_adapter.get_history(
                {
                    "user_id": str(ctx.author.id),
                    "server_id": str(ctx.guild.id)
                }
            )

            id_to_history =





            # for selected_value in selected_values:

            #     if str(selected_value) in user_historys:
            # #

            print(selected_values)

        select_options.callback = callback
        view.add_item(select_options)

        await ctx.send(view=view)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.


    @daily.command(name="delete", description="刪除每日任務")
    @checks.not_blacklisted()
    async def daily_delete(self, context: Context):
        user_created_tasks = daily_adapter.get_tasks_by_user_id(context.author.id)
        if len(user_created_tasks) == 0:
            await context.send("你沒有創建任何每日任務")
            return
        options = [discord.SelectOption(label="取消", value="cancel")]
        options.extend([
            discord.SelectOption(label=task["name"], value=task["id"])
            for task in user_created_tasks
        ])
        view = ui.View()
        select_ui = ui.Select(placeholder="請選擇要刪除的每日任務",
                              options=options,
                              min_values=1,
                              max_values=max(len(options), 1))

        async def callback(interaction: discord.Interaction):

            task_ids_to_delete = select_ui.values
            logging.info(task_ids_to_delete)
            if "cancel" in task_ids_to_delete:
                await interaction.message.edit(content="取消刪除", view=None)
                return

            double_check_ui = ButtonCheck()

            await interaction.response.edit_message(content="確認刪除？", view=double_check_ui)
            await double_check_ui.wait()

            if double_check_ui.value == "yes":
                daily_adapter.delete_task_by_ids(task_ids_to_delete)
                await interaction.message.edit(content="刪除成功！", view=None, embed=None)
            elif double_check_ui.value == "no":
                await interaction.message.edit(content="取消刪除", view=None, embed=None)

            double_check_ui.stop()

        select_ui.callback = callback
        view.add_item(select_ui)

        await context.send(view=view, ephemeral=True)

    @daily.command(name="listdone", description="列出簽到的每日任務")
    @checks.not_blacklisted()
    async def daily_listdone(self, context: Context, top_n: int = 1):
        user_id = context.author.id
        tasks = daily_adapter.get_tasks_by_user_id(user_id)
        if len(tasks) == 0:
            await context.send("你沒有簽到過任何每日任務")
            return
        tasks = sorted(tasks, key=lambda x: time_conversion(x["last_check"]), reverse=True)
        if len(tasks) > top_n:
            tasks = tasks[:top_n]

        embed = discord.Embed(title=f"最近 {top_n} 個簽到的每日任務",
                              description="",
                              color="#edf6e5")
        for task in tasks:
            name = task["name"]
            name_decorated = f"📍{name}"
            consecutive, accumulate = task["consecutive"], task["accumulate"]
            message = f" 你已經連續簽到 {consecutive} 日，累計簽到 {accumulate} 日，再接再厲！"
            embed.add_field(name=name_decorated, value=message, inline=False)
        await context.send(embed=embed)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Daily(bot))
