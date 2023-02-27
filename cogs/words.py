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

from api import words as words_adapter

import logging

logging.basicConfig(level=logging.INFO)

GUILD_ID = 1073536462924025937
class WordAddModal(ui.Modal, title="Modal to add words"):

    def __init__(self, title, type_, *args, **kwargs):
        super().__init__(title=title)
        content = ui.TextInput(
            label="話語",
            placeholder="別再廢了！",
            min_length=1,
            max_length=100,
            style=discord.TextStyle.long,
            required=True,
        )
        self.type_ = type_
        self.add_item(content)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="新增話語成功 ✅",
                              timestamp=datetime.now(),
                              color=discord.Colour.blue())
        content = self.children[0].value
        embed.set_author(name=interaction.user,
                         icon_url=interaction.user.avatar)
        create_time = datetime.now()

        words_adapter.add_one_word(
            content=content,
            style=self.type_,
            user_id=interaction.user.id,  # member_id
            server_id=interaction.guild.id,  # server_id
            created_at=create_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  #  TODO: strftime (datetime.strftime("%Y-%m-%d %H:%M:%S"))
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Words(commands.Cog, name="words", description="❤️ 新增/刪除鼓勵或譴責的話！"):

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
            embed = discord.Embed(title="Words",
                                  description=description,
                                  color=discord.Color.blurple())
            await context.send(embed=embed)

    @words.command(name="add", description="新增一句鼓勵或譴責的話語。")
    @checks.not_blacklisted()
    async def add(self, context: Context):
        view = ui.View()
        str_options = ["提醒", "譴責"]
        select_ui = ui.Select(
            placeholder="選擇欲新增話語類別",
            options=[
                discord.SelectOption(label=x, value=x) for x in str_options
            ],
            min_values=1,
            max_values=max(len(str_options), 1),
        )

        async def callback(interaction: discord.Interaction):
            type_ = select_ui.values[0]
            modal = WordAddModal(title=f"新增{type_}話語", type_=type_)
            await interaction.response.send_modal(modal)

        select_ui.callback = callback
        view.add_item(select_ui)

        await context.send(view=view)

        # remove users message
        await context.message.delete()

    @words.command(name="delete", description="刪除（你自己創建的）一句鼓勵或譴責的話語。")
    @checks.not_blacklisted()
    async def delete(self, context: Context):
        pass

    @words.command(name="listall", description="列出所有鼓勵或譴責的話語。")
    @checks.not_blacklisted()
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def listall(self, context: Context):
        server_words = words_adapter.get_all_words()

        logging.info(server_words)
        embed = discord.Embed(title="所有話語", color=discord.Colour.blue())
        for word in server_words:
            if word['content'] is not None:

                # user = await self.bot.fetch_user(int(word['user_id']))
                try:
                    user  = await context.guild.fetch_member(int(word['user_id']))
                except Exception as e:
                    logging.info(e) 
                    user = None

                # user2 = None if not user2 else user2
                logging.info(f'{user}')
                user_mention = word['user_id'] if not user else user.name
                style = word['style'] if ('style' in word and word['style']) else "Unknown"
                embed.add_field(name=f"🍊 「{style}」" + word['content'],
                                value=f"加入者: {user_mention}",
                                inline=False)

        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Words(bot))
