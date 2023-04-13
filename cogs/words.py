from typing import List, Dict, Any
from datetime import datetime

from discord.ext import commands
from discord.ext.commands import Context
import discord
from discord import ui
from discord import app_commands
from discord.ext.forms import Form, Validator, ReactionForm, ReactionMenu
import logging

from helpers.utils import ButtonCheck, get_current_time
from api import words as words_adapter
from api import checks

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
        embed = discord.Embed(title="🍊 新增話語成功",
                              timestamp=get_current_time(),
                              color=discord.Colour.blue())
        content = self.children[0].value
        embed.set_author(name=interaction.user,
                         icon_url=interaction.user.avatar)
        create_time = get_current_time()

        words_adapter.add_one_word(
            content=content,
            style=self.type_,
            user_id=interaction.user.id,  # member_id
            server_id=interaction.guild.id,  # server_id
            created_at=create_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Words(commands.Cog, name="words", description="❤️ 新增/刪除鼓勵或譴責的話！"):

    def __init__(self, bot):
        self.bot = bot
        self.embed_per_page = 3

    @commands.hybrid_group(
        name="words",
        description="❤️ Share your words!",
    )
    async def words(self, context: Context):
        """
        entry point for `words`
        """
        if not context.invoked_subcommand:
            description = """
                Please specify a subcommand.\n
                `add` - 新增一句鼓勵或譴責的話語。\n
                `delete` - 刪除你所創建的鼓勵或譴責的話語。\n
                `listall` - 列出所有鼓勵或譴責的話語。\n
                `listmine` - 列出你所創建的鼓勵或譴責的話語。\n
            """
            embed = discord.Embed(title="Words",
                                  description=description,
                                  color=discord.Color.blurple())
            await context.send(embed=embed)

    @words.command(name="add", description="新增一句鼓勵或譴責的話語。")
    @checks.is_fully_registered()
    async def add(self, context: Context):
        view = ui.View()
        str_options = ["提醒", "譴責", "完成"]
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

    async def create_embed_list(self, words, guild, embed_per_page=10):
        embed_list = []
        for i in range(0, len(words), embed_per_page):
            embed = discord.Embed(title="所有話語", color=0xF9C543)
            for word in words[i:i + embed_per_page]:
                if word['user_id'] in [None, 'admin']:
                    continue
                user_id = int(word['user_id'])
                user = await self.recognize_user(user_id, guild)
                user_mention = word['user_id'] if not user else user.name
                embed.add_field(
                    name=f"🍊 「{word['style']}」" + word['content'],
                    value=f"加入者: {user_mention}\n加入時間: {word['created_at']}",
                    inline=False)
            embed_list.append(embed)
        return embed_list

    async def recognize_user(self, user_id, guild):
        try:
            user = guild.get_member(user_id) or await guild.fetch_member(
                user_id)
        except Exception as e:
            logging.info(e)
            user = None
        return user

    @words.command(name="listall", description="列出所有鼓勵或譴責的話語。")
    @checks.is_fully_registered()
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def listall(self, context: Context):
        server_words = words_adapter.get_all_words()
        embed = discord.Embed(title="所有話語", color=discord.Colour.blue())
        if len(server_words) <= self.embed_per_page:
            for word in server_words:
                if word['content'] is not None:
                    # user = await self.bot.fetch_user(int(word['user_id']))
                    user_id = int(word['user_id'])
                    user = self.recognize_user(user_id, context.guild)
                    user_mention = word['user_id'] if not user else user.name
                    style = word['style'] if ('style' in word
                                              and word['style']) else "Unknown"
                    embed.add_field(
                        name=f"🍊 「{style}」" + word['content'],
                        value=
                        f"加入者: {user_mention}\n加入時間: {word['created_at']}",
                        inline=False)

            await context.send(embed=embed)
        else:
            embed_list = await self.create_embed_list(server_words,
                                                      context.guild,
                                                      self.embed_per_page)
            form = ReactionMenu(context, embed_list)
            await form.start()

    @words.command(name="listmine", description="列出你創建的鼓勵或譴責的話語。")
    @checks.is_fully_registered()
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def listmine(self, context: Context):
        server_words = words_adapter.get_all_words()
        my_words = [
            word for word in server_words
            if word['user_id'] == str(context.author.id)
        ]
        embed = discord.Embed(title="我的話語", color=discord.Colour.blue())
        if len(my_words) <= self.embed_per_page:
            for word in my_words:
                if word['content'] is not None:
                    style = word['style'] if ('style' in word
                                              and word['style']) else "Unknown"
                    embed.add_field(
                        name=f"🍊 「{style}」" + word['content'],
                        value=
                        f"加入者: {context.author.name}\n加入時間: {word['created_at']}",
                        inline=False)
            await context.send(embed=embed)
        else:
            embed_list = await self.create_embed_list(my_words, context.guild,
                                                      self.embed_per_page)
            form = ReactionMenu(context, embed_list)
            await form.start()

    @words.command(name="delete", description="刪除你創建的一句鼓勵或譴責的話語。")
    @checks.is_fully_registered()
    async def delete(self, context: Context):
        user_words = words_adapter.get_words_by_user(context.author.id)
        if not user_words:
            await context.send("🧐 你沒有創建任何話語。")
            return
        options = [discord.SelectOption(label="取消", value="cancel")]

        def format_label(i: int, uw: Dict[str, Any]):
            content_display = uw["content"][:20] + "..." if len(
                uw["content"]) > 20 else uw["content"]
            formatted_label = f'{i}. {content_display}'
            return formatted_label

        print(user_words)

        options.extend([
            discord.SelectOption(
                label=format_label(i, uw),
                value=uw["id"],
            ) for i, uw in enumerate(user_words, start=1)
        ])

        view = ui.View()
        select_ui = ui.Select(placeholder="請選擇要刪除的話語",
                              options=options,
                              min_values=1,
                              max_values=max(len(options), 1))

        async def callback(interaction: discord.Interaction):

            word_ids_to_delete = select_ui.values
            logging.info(word_ids_to_delete)
            if "cancel" in word_ids_to_delete:
                await interaction.message.edit(content="取消刪除", view=None)
                return

            double_check_ui = ButtonCheck()  # TODO: add a button check

            await interaction.response.edit_message(content="確認刪除？",
                                                    view=double_check_ui)
            await double_check_ui.wait()

            if double_check_ui.value == "yes":
                words_adapter.delete_word_by_ids(word_ids_to_delete)
                await interaction.message.edit(content="刪除成功！",
                                               view=None,
                                               embed=None)
            elif double_check_ui.value == "no":
                await interaction.message.edit(content="取消刪除",
                                               view=None,
                                               embed=None)

            double_check_ui.stop()

        select_ui.callback = callback
        view.add_item(select_ui)

        await context.send(view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Words(bot))
