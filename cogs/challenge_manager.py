""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""
import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks, handler


# Here we name the cog and create a new class for the cog.
class Challenge_Manager(commands.Cog,
                        name="challenge-manager"):
    def __init__(self, bot):
        self.bot = bot
        challenge_map = {
            "leetcode-daily": [
                "lc-daily", "lc-d", "leetcode-daily-challenge", "lc-daily-challenge", "lc-daily-challenges", "lcd"
            ]
        }
        self.inverted_challenge_map = self.invert_map(challenge_map)

    @staticmethod
    def invert_map(challenge_map: dict) -> dict:
        inverted_challenge_map = {}
        for k, vs in challenge_map.items():
            for v in vs:
                inverted_challenge_map[v] = k
        return inverted_challenge_map

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.
    @commands (
        name = "daily",
        description = "Check in to the specified challenge",
    )
    @checks.not_blacklisted()
    async def check_in(self, context: Context, *,
                        challenge: str="leetcode-daily") -> None:

        challenge = self.inverted_challenge_map.get(challenge, challenge)
        consecutive, total = handler.check_in(context.author.id, challenge)
        embed = discord.Embed(
            description=f"Successfully checked in to {challenge}. You have checked in {consecutive} times in a row and {total} times in total.",
            color=0x9C84EF)
        await context.send(embed=embed)
        return True




    @commands.hybrid_command(
        name="testcommand",
        description="This is a testing command that does nothing.",
    )
    # This will only allow non-blacklisted members to execute the command
    @checks.not_blacklisted()
    # This will only allow owners of the bot to execute the command -> config.json
    @checks.is_owner()
    async def testcommand(self, context: Context):
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        # Do your stuff here

        # Don't forget to remove "pass", I added this just because there's no content in the method.
        pass


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Challenge_Manager(bot))
