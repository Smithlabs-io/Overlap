"""
/info command — bot metadata, links, and support info.
"""
import discord

BOT_INVITE_URL = "https://discord.com/api/oauth2/authorize?client_id=1359004428044079126&permissions=274878024768&scope=bot+applications.commands"
SUPPORT_EMAIL = "wrsmith865@gmail.com"
WEBSITE_URL = "https://overlap.smithlabs.io"
CREATOR_NAME = "Will Smith"
BOT_VERSION = "1.0.0"


async def show_bot_info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Overlap Bot",
        description="Schedule events without the back-and-forth.\nFind the time that works for everyone — automatically.",
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="📚 Library",
        value="[discord.py](https://discordpy.readthedocs.io/)",
        inline=True,
    )
    embed.add_field(name="👤 Creator", value=CREATOR_NAME, inline=True)
    embed.add_field(name="🔢 Version", value=BOT_VERSION, inline=True)

    embed.add_field(
        name="🔗 Links",
        value=(
            f"[Add to Server]({BOT_INVITE_URL})\n"
            f"[Website]({WEBSITE_URL})"
        ),
        inline=False,
    )
    embed.add_field(
        name="📧 Support",
        value=SUPPORT_EMAIL,
        inline=False,
    )

    embed.add_field(
        name="🗳️ Vote",
        value=(
            "Voting is free and helps us reach more servers!\n"
            "Use `/vote` to support Overlap!"
        ),
        inline=False,
    )

    embed.set_footer(text="Use /vote to support the bot · all features are free")

    await interaction.response.send_message(embed=embed, ephemeral=True)
