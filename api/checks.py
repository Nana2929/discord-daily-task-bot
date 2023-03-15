from .user import check_user_exists
from typing import Callable, TypeVar
from discord.ext import commands
T = TypeVar("T")

def user_registered() -> Callable[[T], T]:
    """Check if user is registered."""
    async def predicate(context: commands.Context) -> bool:
        ok = check_user_exists(context.author.id)
        if not ok:
            await context.send("您尚未註冊，請先註冊")
        return ok
    return commands.check(predicate)
