import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import ui
from api import user as user_adapter
from api import checks
from exceptions import get_error


class UserAddModal(ui.Modal, title="modal to add the user"):

    def __init__(self, **kwargs):
        super().__init__()
        content = ui.TextInput(
            label="時區（UTC 時區）",
            placeholder="+8",
            min_length=1,
            max_length=3,
        )
        self.add_item(content)

    async def on_submit(self, interaction: discord.Interaction):
        timezone = self.children[0].value
        if not checks.is_utc_legal(timezone):
            await interaction.response.edit_message(
                content=f"時區不合法，請輸入範圍為 -12 到 14 的數字。", view=None)
            return
        converted_timezone = int(
            timezone) if not timezone.startswith("+") else int(timezone[1:])
        formatted_timezone = f"+{converted_timezone}" if converted_timezone > 0 else f"{converted_timezone}"
        embed = discord.Embed(title="註冊成功",
                              description=f"\n \
                              時區：UTC {formatted_timezone}",
                              color=discord.Color.green())
        user_exists = user_adapter.check_user_exists(interaction.user.id)
        if user_exists:
            msg = user_adapter.update_user(
                user_id=str(interaction.user.id),
                time_zone= converted_timezone
            )
            content = f"你的註冊時區已經變更為 UTC {converted_timezone}。"
        else:
            content = None
            msg = user_adapter.add_one_user(user_id=str(interaction.user.id),
                                     time_zone=converted_timezone)
        if "errors" in msg:
            content = f"註冊或修改失敗，請稍後再試。錯誤訊息：{get_error(msg)}"

        await interaction.response.edit_message(content=content,
                                                view=None,
                                                embed=embed)


# Here we name the cog and create a new class for the cog.
class Register(commands.Cog, name="register"):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="register",
        description="User registration to the bot (⏲️ with timezone!)",
    )
    async def register(self, context: Context):
        view = ui.View()
        register_button = ui.Button(label="🦄 點我註冊",
                                    style=discord.ButtonStyle.primary)

        async def callback(interaction: discord.Interaction):
            modal = UserAddModal(title=f"新增使用者")
            await interaction.response.send_modal(modal)

        register_button.callback = callback
        view.add_item(register_button)
        await context.send(view=view)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Register(bot))