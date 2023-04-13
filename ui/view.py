import api.daily as daily_adapter
from discord import ui
from discord.ext.commands import Context
import discord
from helpers.utils import get_current_time, is_the_same_date, ButtonCheck
from datetime import datetime, timedelta
import api.subscribe as subscribe_adapter
import api.user as user_adapter
from .modal import SubscribeAddModal


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
                label=f"📌 {sub['task_id']['name']} {sub['task_id']['description'][:10]}",
                value=sub["id"])

        async def callback(interaction: discord.Interaction):

            embed = discord.Embed(title="以下是取消訂閱的項目",
                                  color=discord.Colour.lighter_gray())

            for value in options.values:
                if subscribe_adapter.delete_subscribe(id=value):
                    embed.add_field(
                        name=f"🔕 取消訂閱 {subscribe_id_to_subscribe[int(value)]['task_id']['name']} 成功",
                        value="",
                        inline=False)
                else:
                    embed.add_field(
                        name=f"🔕 取消訂閱 {subscribe_id_to_subscribe[int(value)]['task_id']['name']} 失敗",
                        value="請聯絡管理員",
                        inline=False)

            await interaction.response.edit_message(content=None,
                                                    view=None,
                                                    embed=embed)

        options.callback = callback
        self.add_item(options)
