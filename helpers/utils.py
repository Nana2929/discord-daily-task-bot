import discord
import pytz
from datetime import datetime

def get_current_time():
    return datetime.now(tz=pytz.UTC)

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