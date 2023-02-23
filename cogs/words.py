from typing import List
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Context
from helpers import checks
import discord
from discord import ui
from discord import app_commands
from discord.ext.forms import Form, Validator, ReactionForm, ReactionMenu
import math

class WordAddModal(ui.Modal, title="Modal to add words"):

    def __init__(self, title="新增話語", *args, **kwargs):
        super().__init__(title = title)
        content = ui.TextInput(
            label="話語",
            placeholder="別再廢了！",
            min_length = 1,
            max_length = 100,
            style= discord.TextStyle.long,
            required = True,
        )
        self.add_item(content)


    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
           title = "新增話語成功 ✅",
           timestamp = datetime.now(),
           color = discord.Colour.blue())
        content = self.children[0].value
        # wordapi.add_word(
        #     content = content,
        #     user_id = interaction.user.id,     # member_id
        #     server_id = interaction.guild.id,  # server_id
        #     created_at = datetime.now(),
        # )
        embed.set_author(name = interaction.user, icon_url=interaction.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True)



class Words(commands.Cog, name = "words", description="❤️ 新增/刪除鼓勵或譴責的話！"):
    def __init__(self, bot):
        self.bot = bot
    @commands.hybrid_group(
        name="words",
        description="Share your words!",
    )
    async def words(self, context: Context):
        """
        entry point for `words`
        """
        if not context.invoked_subcommand:
            description = """
                Please specify a subcommand.\n\n
                `add` - 新增一句鼓勵或譴責的話語。\n\n
                `delete` - 刪除（你自己創建的）一句鼓勵或譴責的話語。\n\n
            """
            embed = discord.Embed(
                title="Words",
                description=description,
                color=discord.Color.blurple()
            )
            await context.send(embed=embed)

    @words.command(name="add", description="新增一句鼓勵或譴責的話語。")
    @checks.not_blacklisted()
    async def add(self, context: Context):
        view = ui.View()
        str_options = ["提醒", "譴責"]
        select_ui = ui.Select(
            placeholder="選擇欲新增話語類別",
            options = [
                discord.SelectOption(label=x, value=x) for x in str_options
            ],
            min_values = 1,
            max_values = max(len(str_options), 1),
        )


        async def callback(interaction: discord.Interaction):
            modal = WordAddModal(title = f"新增{interaction.data['values'][0]}話語")
            await interaction.response.send_modal(modal)
        select_ui.callback = callback
        view.add_item(select_ui)

        await context.send(view=view)

        # remove users message
        await context.message.delete()

async def setup(bot):
    await bot.add_cog(Words(bot))





