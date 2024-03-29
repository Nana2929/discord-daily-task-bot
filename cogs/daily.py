# %%
from collections import defaultdict
from datetime import datetime
import random
from discord.ext import commands, tasks
from discord.ext.commands import Context
from api import checks
import discord
from discord import ui
from helpers.utils import get_current_time, ButtonCheck
import api.daily as daily_adapter
import api.subscribe as subscribe_adapter
import api.words as words_adapter
from dataclasses import dataclass
from ui.modal import DailyAddModal
from ui.view import DailyDoneView, DailySubscribeView, DailyUnsubscribeView


@dataclass
class style:
    done: str = "完成"
    condemn: str = "譴責"
    remind: str = "提醒"


class DailyDoneView(ui.View):

    def __init__(self, ctx: Context, **kwargs):
        self.done_word_footer = kwargs.pop("done_word")
        super().__init__(**kwargs)
        tasks = daily_adapter.get_task({"server_id": str(ctx.guild.id)})
        task_id_to_task = {task["id"]: task for task in tasks}

        select_options = ui.Select(placeholder="請選擇要簽到的每日任務",
                                   min_values=1,
                                   max_values=len(tasks))

        for task in tasks:
            select_options.add_option(label=f"📌 {task['name']}",
                                      value=task["id"])

        async def callback(interaction: discord.Interaction):

            # list of int task id
            selected_values = [int(v) for v in select_options.values]

            user_histories = daily_adapter.get_history({
                "user_id":
                str(ctx.author.id),
                "server_id":
                str(ctx.guild.id)
            })
            # daily_adapter.clean_history(ctx.author.id, ctx.guild.id)
            task_id_to_history = {
                user_history["task_id"]["id"]: user_history
                for user_history in user_histories
            }

            now = get_current_time()
            today = now.strftime("%Y-%m-%d")
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

            embed = discord.Embed(title="簽到紀錄", color=discord.Color.green())

            for task_id in selected_values:

                task = task_id_to_task[task_id]
                ok = False
                # if history exists, history will be updated
                history = task_id_to_history.get(
                    task_id, {
                        "user_id": str(ctx.author.id),
                        "task_id": str(task_id),
                        "server_id": str(ctx.guild.id),
                        "last_check": now,
                        "accumulate": 1,
                        "consecutive": 1
                    })
                if "id" in history.keys():

                    if is_the_same_date(history["last_check"], today):
                        embed.add_field(name=f"您今天已經簽到過 {task['name']} 了",
                                        value=f"""
                            📝 累計簽到 {history['accumulate']} 天
                            📝 連續簽到 {history['consecutive']} 天
                            """,
                                        inline=False)
                        continue

                    history["accumulate"] += 1
                    if is_the_same_date(history["last_check"], yesterday):
                        history["consecutive"] += 1
                    else:
                        history["consecutive"] = 1
                    # print('!!', history)
                    history["last_check"] = now
                    ok = daily_adapter.update_history(**history)

                else:
                    ok = daily_adapter.add_history(**history)

                if ok:
                    embed.add_field(name=f"簽到 {task['name']} 成功",
                                    value=f"""
                        📝 累計簽到 {history['accumulate']} 天
                        📝 連續簽到 {history['consecutive']} 天""",
                                    inline=False)  # set footer
                else:
                    embed.add_field(name=f"簽到 {task['name']} 失敗",
                                    value="請聯絡管理員",
                                    inline=False)
            embed.set_footer(text=self.done_word_footer)
            await interaction.response.edit_message(view=None, embed=embed)

        select_options.callback = callback
        self.add_item(select_options)


class DailyAddModal(ui.Modal):

    def __init__(self, title="新增 daily", **kwargs):

        super().__init__(title=title)

        self.add_item(ui.TextInput(label="Name", required=True,
                                   max_length=127))
        self.add_item(
            ui.TextInput(label="Description",
                         required=False,
                         style=discord.TextStyle.paragraph,
                         max_length=255))

    async def on_submit(self, interaction: discord.Interaction):

        name = self.children[0].value
        description = self.children[1].value
        user_id = interaction.user.id
        server_id = interaction.guild.id

        print(name, description, user_id, server_id)

        if daily_adapter.add_task(user_id=str(user_id),
                                  server_id=str(server_id),
                                  name=str(name),
                                  description=str(description)):
            embed = discord.Embed(
                title="新增 daily 成功",
                description=f"Name: {name}\nDescription: {description}",
                color=discord.Color.green())
            await interaction.response.edit_message(content=None,
                                                    view=None,
                                                    embed=embed)
        else:
            await interaction.response.edit_message(content=f"新增 daily 失敗",
                                                    view=None)


class DailySubscribeView(ui.View):

    def __init__(self, ctx: Context) -> None:
        super().__init__()

        self.tasks = daily_adapter.get_task({"server_id": str(ctx.guild.id)})

        if len(self.tasks) == 0:
            return

        user_info = user_adapter.get_user(user_id=ctx.author.id)

        task_id_to_task = {task["id"]: task for task in self.tasks}
        select_options = ui.Select(placeholder="請選擇要訂閱的每日任務",
                                   min_values=1,
                                   max_values=len(self.tasks))

        for task in self.tasks:
            select_options.add_option(
                label=f"📌 {task['name']} {task['description'][:10]}",
                value=task["id"])

        async def callback(interaction: discord.Interaction):
            # list of int task id
            selected_task_ids = [int(v) for v in select_options.values]
            selected_task_infos = {
                task_id: task_id_to_task[task_id]
                for task_id in selected_task_ids
            }

            modal = SubscribeAddModal(selected_task_infos=selected_task_infos,
                                      user_time_zone=user_info["time_zone"])
            await interaction.response.send_modal(modal)

        select_options.callback = callback

        self.add_item(select_options)


class DailyUnsubscribeView(ui.View):

    def __init__(self, ctx: Context) -> None:
        super().__init__()

        self.subscribes = subscribe_adapter.get_subscribe({
            "user_id":
            str(ctx.author.id),
            "server_id":
            str(ctx.guild.id)
        })

        subscribe_id_to_subscribe = {sub["id"]: sub for sub in self.subscribes}
        # print(self.subscribes)
        if len(self.subscribes) == 0:
            return

        options = ui.Select(placeholder="請選擇要取消訂閱的每日任務",
                            min_values=1,
                            max_values=len(self.subscribes))

        for sub in self.subscribes:
            options.add_option(
                label=
                f"📌 {sub['task_id']['name']} {sub['task_id']['description'][:10]}",
                value=sub["id"])

        async def callback(interaction: discord.Interaction):

            embed = discord.Embed(title="以下是取消訂閱的項目",
                                  color=discord.Colour.lighter_gray())

            for value in options.values:
                if subscribe_adapter.delete_subscribe(id=value):
                    embed.add_field(
                        name=
                        f"🔕 取消訂閱 {subscribe_id_to_subscribe[int(value)]['task_id']['name']} 成功",
                        value="",
                        inline=False)
                else:
                    embed.add_field(
                        name=
                        f"🔕 取消訂閱 {subscribe_id_to_subscribe[int(value)]['task_id']['name']} 失敗",
                        value="請聯絡管理員",
                        inline=False)

            await interaction.response.edit_message(content=None,
                                                    view=None,
                                                    embed=embed)

        options.callback = callback
        self.add_item(options)


class SubscribeAddModal(ui.Modal):

    def __init__(self,
                 selected_task_infos: Dict[int, Dict],
                 user_time_zone: int,
                 title="設定譴責及提醒時間 📆",
                 **kwargs):
        super().__init__(title=title)

        self.add_item(
            ui.TextInput(label="提醒時間（0~23）",
                         required=True,
                         min_length=1,
                         max_length=2))
        self.add_item(
            ui.TextInput(label="譴責時間（0~23），勿和提醒時間相同",
                         min_length=1,
                         required=True,
                         max_length=2))
        self.user_time_zone = user_time_zone
        self.selected_task_infos = selected_task_infos

    async def on_submit(self, interaction: discord.Interaction):

        remind_time, condemn_time = self.children[0].value, self.children[
            1].value

        if not remind_time.isdigit() or not condemn_time.isdigit():
            await interaction.response.edit_message(content=f"格式錯誤！請輸入數字 0~23",
                                                    view=None)
            return

        remind_time, condemn_time = int(remind_time), int(condemn_time)

        if remind_time not in range(24) or condemn_time not in range(24):
            await interaction.response.edit_message(content=f"格式錯誤！請輸入數字 0~23",
                                                    view=None)
            return

        user_subscribes = {
            subscribe["task_id"]['id']: subscribe
            for subscribe in subscribe_adapter.get_subscribe(
                {
                    "user_id": interaction.user.id,
                    "server_id": interaction.guild.id
                })
        }

        embed = discord.Embed(
            title=f"提醒時間: {remind_time}點\n譴責時間: {condemn_time}點",
            color=discord.Color.yellow())

        for task_id in self.selected_task_infos.keys():

            subscribe = user_subscribes.get(
                task_id, {
                    "task_id": task_id,
                    "user_id": interaction.user.id,
                    "server_id": interaction.guild.id,
                    "channel_id": interaction.channel.id
                })

            subscribe["remind_time"] = (remind_time - self.user_time_zone +
                                        24) % 24
            subscribe["condemn_time"] = (condemn_time - self.user_time_zone +
                                         24) % 24

            embed_name, embed_value = "", ""

            if "id" in subscribe:  # update

                if subscribe_adapter.update_subscribe(**subscribe):
                    embed_name = f"🔄 更新 {self.selected_task_infos[task_id]['name']} 成功"
                else:
                    embed_name = f"🔄 更新 {self.selected_task_infos[task_id]['name']} 失敗"
                    embed_value = "請連絡管理員",
            else:
                if subscribe_adapter.add_subscribe(**subscribe):
                    embed_name = f"🔔 訂閱 {self.selected_task_infos[task_id]['name']} 成功"
                else:
                    embed_name = f"🔔 訂閱 {self.selected_task_infos[task_id]['name']} 失敗"
                    embed_value = "請連絡管理員"

            embed.add_field(name=embed_name, value=embed_value, inline=False)

        return await interaction.response.edit_message(content=None,
                                                       view=None,
                                                       embed=embed)


class Daily(commands.Cog,
            name="daily",
            description="🥰 Your daily task manager"):

    def __init__(self, bot):

        self.remind_words = words_adapter.get_words_by_style(style.remind)
        self.done_words = words_adapter.get_words_by_style(style.done)
        self.condemn_words = words_adapter.get_words_by_style(style.condemn)
        self.bot = bot

    @commands.hybrid_group(
        name="daily",
        description="🥰 Your daily task manager",
    )
    @checks.is_fully_registered()
    async def daily(self, ctx: Context):

        if ctx.invoked_subcommand is None:
            description = """
                Please specify a subcommand.\n
                `add` - 新增一個每日任務。\n
                `delete` - 刪除你所創建的每日任務。\n
                `listall` - 列出所有每日任務。\n
                `listmine` - 列出你所創建的每日任務。\n
                =========================\n
                `subscribe` - 訂閱，即開啟每日任務提醒功能\n
                `unsubscribe` - 取消訂閱，即關閉每日任務功能。\n
                =========================\n
                `done` - 簽到一個每日任務。\n
                `listdone` - 列出你今日簽到的每日任務。\n
            """
            embed = discord.Embed(title="Daily",
                                  description=description,
                                  color=discord.Color.blurple())
            await ctx.send(embed=embed)

    @daily.command(
        name="add",
        description="新增每日任務",
    )
    @checks.is_fully_registered()
    async def daily_add(self, ctx: Context):

        view = ui.View()
        open_button = ui.Button(label="點我新增 daily",
                                style=discord.ButtonStyle.primary)

        async def callback(interaction: discord.Interaction):
            modal = DailyAddModal()
            await interaction.response.send_modal(modal)

        open_button.callback = callback
        view.add_item(open_button)

        await ctx.send(view=view)

    @daily.command(
        name="listall",
        description="列出所有每日任務",
    )
    @checks.is_fully_registered()
    async def daily_listall(self, ctx: Context):

        tasks_in_server = daily_adapter.get_task(
            {"server_id": str(ctx.guild.id)})

        embed = discord.Embed(title="所有每日任務",
                              description=f"共有 {len(tasks_in_server)} 個任務",
                              color=discord.Color.green())

        for task in tasks_in_server:

            user = await self.bot.fetch_user(int(task["created_by"]))
            embed.add_field(name=f"{task['name']}: {task['description']}",
                            value=f"建立者: {user.mention}",
                            inline=False)
        await ctx.send(embed=embed)

    @daily.command(
        name="listmine",
        description="列出自己的每日任務",
    )
    @checks.is_fully_registered()
    async def daily_listmine(self, ctx: Context):

        tasks = daily_adapter.get_task({
            "created_by": str(ctx.author.id),
            "server_id": str(ctx.guild.id)
        })

        embed = discord.Embed(title="以下是您在此伺服器建立的每日任務",
                              description=f"共有 {len(tasks)} 個任務",
                              color=discord.Color.green())

        for task in tasks:
            embed.add_field(name=f"📜 {task['name']}",
                            value=f"{task['description']}",
                            inline=False)
        await ctx.send(embed=embed)

    @daily.command(
        name="done",
        description="簽到任務",
    )
    @checks.is_fully_registered()
    async def daily_done(self, ctx: Context):
        await ctx.send(view=DailyDoneView(
            ctx=ctx, done_word=random.choice(self.done_words)))

    @daily.command(
        name="subscribe",
        description="訂閱每日任務通知",
    )
    @checks.is_fully_registered()
    async def daily_subscribe(self, ctx: Context):
        view = DailySubscribeView(ctx=ctx)
        if len(view.tasks) == 0:
            await ctx.send("目前沒有任何任務可以訂閱")
        else:
            await ctx.send(view=DailySubscribeView(ctx=ctx))

    @daily.command(name="listdone", description="列出簽到的每日任務")
    @checks.is_fully_registered()
    async def daily_listdone(self, context: Context, top_n: int = 3):

        now = get_current_time()
        done_tasks = [
            his for his in daily_adapter.get_history(
                {
                    "user_id": str(context.author.id),
                    "server_id": str(context.guild.id),
                })
        ]

        def str2iso(s):
            return datetime.fromisoformat(s)

        done_tasks = sorted(done_tasks,
                            key=lambda i: str2iso(i['last_check']),
                            reverse=True)
        n = min(top_n, len(done_tasks))
        done_tasks = done_tasks[:n]
        embed = discord.Embed(title=f"最近簽到的{n}個每日任務",
                              description="",
                              color=discord.Color.green())

        for task in done_tasks:
            try:
                name = f"📍{task['task_id']['name']}"
                message = f" 你已經連續簽到 {task['consecutive']} 日，累計簽到 {task['accumulate']} 日，再接再厲！"
                embed.add_field(name=name, value=message, inline=False)
            except Exception as e:
                print(e)
        await context.send(embed=embed)

    @daily.command(
        name="unsubscribe",
        description="取消訂閱每日任務通知",
    )
    @checks.is_fully_registered()
    async def daily_unsubscribe(self, ctx: Context):

        view = DailyUnsubscribeView(ctx=ctx)
        if len(view.subscribes) == 0:
            await ctx.send("目前沒有任何任務可以取消訂閱")
        else:
            await ctx.send(view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        self.daily_remind.start()
        self.daily_condemn.start()

    @tasks.loop(minutes=1)
    async def daily_remind(self):
        """Remind user of their todos every day."""
        now = get_current_time()

        # check if n:00
        if now.minute != 0:
            return

        to_remind_list = subscribe_adapter.get_subscribe(
            {"remind_time": int(now.strftime("%H"))})
        user_to_remind_tasks = defaultdict(list)
        for remind in to_remind_list:
            user_to_remind_tasks[remind["user_id"]].append(remind["task_id"])

        for user_id, tasks in user_to_remind_tasks.items():
            done_task_ids = [
                int(his["task_id"]["id"]) for his in daily_adapter.get_history(
                    {
                        "user_id": user_id,
                        "last_check": now.strftime("%Y-%m-%d")
                    })
            ]
            # exclude done tasks
            to_remind_tasks = [
                task for task in tasks if int(task["id"]) not in done_task_ids
            ]

            if len(to_remind_tasks) == 0:
                print(f"no task to remind for {user_id} at {now}.")
                continue

            user = await self.bot.fetch_user(int(user_id))
            embed = discord.Embed(title=f"📢 你今天還有以下任務沒有完成喔，堅持下去!",
                                  color=discord.Color.blurple())

            embed.set_footer(text=self.remind_words[random.randint(
                0,
                len(self.remind_words) - 1)])
            # 2023.04.08 bugfix: naming issue of lists
            for task in to_remind_tasks:
                embed.add_field(name=f"{task['name']}",
                                value=f"{task['description']}",
                                inline=False)

            await user.send(embed=embed)

    @tasks.loop(minutes=1)
    async def daily_condemn(self):
        """Remind user of their todos every day."""
        now = get_current_time()

        # check if n:00
        if now.minute != 0:
            return

        to_condemn_list = subscribe_adapter.get_subscribe(
            {"condemn_time": int(now.strftime("%H"))})

        channel_to_condemn_tasks = defaultdict(list)

        for condemn in to_condemn_list:
            channel_to_condemn_tasks[condemn["channel_id"]].append(condemn)

        for channel_id, tasks in channel_to_condemn_tasks.items():
            task_name_to_user_ids = defaultdict(list)

            for task in tasks:
                # get user done task
                user_done_task_names = [
                    hist["task_id"]["name"]
                    for hist in daily_adapter.get_history(
                        {
                            "user_id": task["user_id"],
                            "last_check": now.strftime("%Y-%m-%d")
                        })
                ]
                # 2023.04.08 bugfix: condemning done tasks bug
                if task["task_id"]["name"] in user_done_task_names:
                    continue
                task_name_to_user_ids[task["task_id"]["name"]].append(
                    task["user_id"])

            if len(task_name_to_user_ids) == 0:
                continue

            channel = self.bot.get_channel(int(channel_id))

            embed = discord.Embed(
                title=f"👿 譴責時間到！",
                description=self.condemn_words[random.randint(
                    0,
                    len(self.condemn_words) - 1)],
                color=discord.Color.fuchsia())

            # img = random.sample(os.listdir("imgs/condemn"), 1)
            # file = discord.File(os.path.join("imgs/condemn", img[0]),
            #                     filename="image.png")
            # embed.set_image(url="attachment://image.png")

            for task_name, user_ids in task_name_to_user_ids.items():
                embed.add_field(
                    name=f"📝 {task_name}",
                    value=
                    f"{' '.join([f'<@{user_id}>' for user_id in user_ids])}",
                    inline=False)

            await channel.send(embed=embed)

    @daily.command(name="delete", description="刪除每日任務")
    async def daily_delete(self, context: Context):
        user_created_tasks = daily_adapter.get_task(
            {'created_by': context.author.id})
        subscribed_tasks = subscribe_adapter.get_subscribe(
            {"user_id": context.author.id})

        diffset = [
            task for task in user_created_tasks if task not in subscribed_tasks
        ]

        if len(user_created_tasks) == 0:
            await context.send("你沒有創建任何每日任務")
            return
        if len(diffset) == 0:
            await context.send("你創建的每日任務正被訂閱中，請取消所有訂閱後再刪除。")
            return
        options = [discord.SelectOption(label="取消", value="cancel")]
        options.extend([
            discord.SelectOption(label=task["name"], value=task["id"])
            for task in diffset
        ])
        view = ui.View()
        select_ui = ui.Select(placeholder="請選擇要刪除的每日任務",
                              options=options,
                              min_values=1,
                              max_values=max(len(options), 1))

        async def callback(interaction: discord.Interaction):

            task_ids_to_delete = select_ui.values
            if "cancel" in task_ids_to_delete:
                await interaction.message.edit(content="取消刪除", view=None)
                return
            print('Task ids to delete:', task_ids_to_delete)
            double_check_ui = ButtonCheck()

            await interaction.response.edit_message(content="確認刪除？",
                                                    view=double_check_ui)
            await double_check_ui.wait()
            message = await interaction.original_response()
            if double_check_ui.value == "yes":
                daily_adapter.delete_task_by_ids(task_ids_to_delete)
                # clean the user;s history to remove the ghost tasks
                daily_adapter.clean_history(context.author.id,
                                            context.guild.id)
                await message.edit(content="刪除成功！", view=None, embed=None)
            elif double_check_ui.value == "no":
                await message.edit(content="取消刪除", view=None, embed=None)

            double_check_ui.stop()
            # !!BUG!!: should delete history as well, otherwise it causes error when trying to get the history tasks

        select_ui.callback = callback
        view.add_item(select_ui)

        await context.send(view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Daily(bot))
