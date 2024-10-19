import disnake
from disnake.ext import commands
from utils.ClientUser import ClientUser

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot: ClientUser = bot

    @commands.command(name="help", description="Hiển thị tin nhắn này", aliases=["h"])
    async def help(self, ctx: disnake.ApplicationCommandInteraction):
        list_cmds: list = []
        embed = disnake.Embed()
        embed.title = f"Trợ giúp lệnh - prefix của bot: {self.bot.environ.get('PREFIX', default='?')}"
        txt = ""
        extra = ""

        for cmd in self.bot.commands:
            list_cmds.append(cmd)

        for cmd in list_cmds:
            if cmd.aliases:
                items: list[str] = []
                for item in cmd.aliases:
                    items.append(item)
                extra = f"- Aliases: `{items}`"
            txt += f"**{cmd.name.capitalize()} {extra}**\n```{cmd.description}```\n"

        embed.description = txt
        await ctx.send(embed=embed)

def setup(bot: ClientUser):
    bot.add_cog(Help(bot))