import random
from typing import List
import discord
from datetime import datetime
import pytz


class ButtonCheck(discord.ui.View):

    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="✅", style=discord.ButtonStyle.secondary)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "yes"
        self.stop()

    @discord.ui.button(label="❌", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "no"
        self.stop()


def get_current_time():
    return datetime.now(tz=pytz.UTC)


def is_the_same_date(date1: str, date2: str):
    """date1 and date2 are is in format of "YYYY-MM-DD"""
    return date1[:10] == date2[:10]





