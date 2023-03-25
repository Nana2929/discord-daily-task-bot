from .user import check_user_exists
from .server import check_server_exists
from typing import Callable, TypeVar
from discord.ext import commands

T = TypeVar("T")


def is_fully_registered() -> Callable[[T], T]:
    """Check if user is registered."""

    async def predicate(context: commands.Context) -> bool:
        ok = check_user_exists(context.author.id) and check_server_exists(
            context.guild.id)
        if not ok:
            await context.send("您尚未在此伺服器註冊，請先註冊")
        return ok

    return commands.check(predicate)


def is_utc_legal(utc: str) -> bool:
    if utc.startswith("+"):
        utc = utc[1:]
    try:
        utc = int(utc)
    except:
        return False
    return utc in range(-12, 14)
