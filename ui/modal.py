from discord import ui
import discord
import api.daily as daily_adapter
from typing import Dict
import api.subscribe as subscribe_adapter


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
