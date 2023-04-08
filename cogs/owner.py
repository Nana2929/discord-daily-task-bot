from typing import Dict, List
from discord.ext import commands, tasks
from typing import Callable, TypeVar
import json
import os
import api.user as user_adapter
from discord.ext.forms import Form, Validator
import discord

T = TypeVar("T")


def is_owner() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is an owner of the bot.
    """

    async def predicate(context: commands.Context) -> bool:
        with open(
                f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
        ) as file:
            data = json.load(file)
        if context.author.id not in data["owners"]:
            await context.send("You are not the owner of the bot!")
        return True

    return commands.check(predicate)


class Owner(commands.Cog, name="owner", description="Owner commands."):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="owner",
        description="Owner commands.",
    )
    async def owner(self, context: commands.Context) -> None:
        ...

    @owner.command(
        name="broadcast",
        description="Broadcast a message to all users",
    )
    @is_owner()
    async def broadcast(self, context: commands.Context) -> None:
        """Broadcast a message to all users"""

        form = Form(context, 'Type your message below')
        form.add_question('請輸入標題', 'title')
        form.add_question('請輸入想發送的資訊', 'message')
        form.add_question('確認要發送嗎? (y/n)', 'check')
        form.set_timeout(60)
        result = await form.start()

        if result.check != 'y':
            await context.send('已取消發送')
            return

        users_info = user_adapter.get_all_users()
        embed = discord.Embed(title='📢 系統公告', color=discord.Color.yellow())
        embed.add_field(name=result.title, value=result.message, inline=False)

        for info in users_info:
            user_id = info['id']
            user = await self.bot.fetch_user(int(user_id))
            await user.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))
