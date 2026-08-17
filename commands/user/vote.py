"""
Vote command and vote-gate UI.

Handles /vote (standalone command) and the gate shown when a user tries to use
a feature that requires a vote. Includes a shame mechanic (honor mode only) that
detects if they claimed to vote without clicking any link.
"""
import discord
from discord.ui import View, Button

import config
from core import votes as vote_core
from core.logging import get_logger

logger = get_logger(__name__)

# Plug in a gif URL here to show a thumbnail on the shame embed.
# Must be a stable public URL (e.g. host it in web/static/).
SHAME_GIF_URL = None  # e.g. "https://yourdomain.com/static/clippy.gif"


# =============================================================================
# Helpers
# =============================================================================

def _tracking_enabled() -> bool:
    """Click tracking requires a public WEB_BASE_URL (not localhost)."""
    return (
        not config.VERIFY_VOTE
        and "localhost" not in config.WEB_BASE_URL
        and "127.0.0.1" not in config.WEB_BASE_URL
    )


def _vote_url(user_id: int, site: str) -> str:
    if _tracking_enabled():
        return f"{config.WEB_BASE_URL}/vote/redirect?user_id={user_id}&site={site}"
    return config.TOPGG_VOTE_URL if site == "topgg" else config.DISCORDBOTS_VOTE_URL


# =============================================================================
# Embeds
# =============================================================================

def _gate_embed(user_id: int) -> discord.Embed:
    embed = discord.Embed(
        title="🗳️ One quick vote unlocks this!",
        description=(
            "This feature is free for everyone — it just needs a vote on a bot listing site.\n"
            "Takes about 5 seconds, and it helps Overlap reach more servers!\n\n"
            "Your vote is good for **12 hours**."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Voting helps Overlap reach more servers — thanks for the support!")
    return embed


def _shame_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🗒️ Excuse me. Hi. Hello.",
        description=(
            "It appears the links above are still in their original, "
            "factory-fresh, completely untouched state.\n\n"
            "We're not accusing you of anything. We're just saying the buttons "
            "look a little... *lonely*. Unvisited. Sealed. Like a letter that was never opened.\n\n"
            "The vote websites are still there. They're waiting. They believe in you."
        ),
        color=discord.Color.yellow(),
    )
    if SHAME_GIF_URL:
        embed.set_thumbnail(url=SHAME_GIF_URL)
    embed.set_footer(text="Are you suuure you voted? 👀")
    return embed


def _vote_command_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🗳️ Vote for Overlap!",
        description=(
            "Voting is free and takes about 5 seconds. It helps us get discovered by more servers!\n\n"
            "**What voting unlocks (free tier):**\n"
            "• 📅 Export events to `.ics` (Google Calendar, Outlook)\n"
            "• 🔔 Custom notification preferences\n\n"
            "Votes reset every **12 hours**."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Voting helps Overlap reach more servers — appreciate the support!")
    return embed


# =============================================================================
# Views
# =============================================================================

class VoteGateView(View):
    """Shown when a user hits the vote gate. Handles the shame mechanic."""

    def __init__(self, user_id: int, feature: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.feature = feature
        self._build(shame=False)

    def _build(self, shame: bool):
        self.clear_items()

        prefix = "🔗 [UNOPENED] " if shame else ""
        self.add_item(Button(
            label=f"{prefix}Vote on top.gg",
            style=discord.ButtonStyle.link,
            url=_vote_url(self.user_id, "topgg"),
            row=0,
        ))
        self.add_item(Button(
            label=f"{prefix}Vote on discordbotlist.com",
            style=discord.ButtonStyle.link,
            url=_vote_url(self.user_id, "discordbots"),
            row=0,
        ))

        if config.VERIFY_VOTE:
            # Verified mode: votes are auto-detected via webhook, no button needed
            self.add_item(Button(
                label="✅ Votes are detected automatically",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=1,
            ))
        elif shame:
            btn = Button(
                label="I Definitely Voted (For Real This Time)",
                style=discord.ButtonStyle.success,
                row=1,
            )
            btn.callback = self._i_voted_final
            self.add_item(btn)
        else:
            btn = Button(label="✅ I Voted!", style=discord.ButtonStyle.success, row=1)
            btn.callback = self._i_voted
            self.add_item(btn)

    async def _i_voted(self, interaction: discord.Interaction):
        if _tracking_enabled() and not vote_core.get_vote_state(self.user_id)["link_clicked"]:
            vote_core.mark_shame_shown(self.user_id)
            self._build(shame=True)
            await interaction.response.edit_message(embed=_shame_embed(), view=self)
        else:
            vote_core.record_vote(self.user_id)
            await interaction.response.edit_message(
                content=f"✅ **Thanks for voting!** Run the command again — you're good for 12 hours.",
                embed=None,
                view=None,
            )

    async def _i_voted_final(self, interaction: discord.Interaction):
        vote_core.record_vote(self.user_id)
        embed = discord.Embed(
            title="📋 Noted. *Definitely.*",
            description=(
                "Your vote has been logged in our **completely real and official voting ledger**.\n\n"
                "There is absolutely a ledger. It has your name in it. "
                "Everything is accounted for. We trust you.\n\n"
                "🙄 Run the command again — you're good."
            ),
            color=discord.Color.green(),
        )
        await interaction.response.edit_message(embed=embed, view=None)


class VoteCommandView(View):
    """Shown by /vote — same links but no feature-gate context."""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

        self.add_item(Button(
            label="Vote on top.gg",
            style=discord.ButtonStyle.link,
            url=_vote_url(user_id, "topgg"),
            row=0,
        ))
        self.add_item(Button(
            label="Vote on discordbotlist.com",
            style=discord.ButtonStyle.link,
            url=_vote_url(user_id, "discordbots"),
            row=0,
        ))

        if not config.VERIFY_VOTE:
            btn = Button(label="✅ I Voted!", style=discord.ButtonStyle.success, row=1)
            btn.callback = self._i_voted
            self.add_item(btn)

    async def _i_voted(self, interaction: discord.Interaction):
        if _tracking_enabled() and not vote_core.get_vote_state(self.user_id)["link_clicked"]:
            vote_core.mark_shame_shown(self.user_id)
            await interaction.response.edit_message(
                embed=_shame_embed(),
                view=VoteGateView(self.user_id, "vote"),
            )
        else:
            vote_core.record_vote(self.user_id)
            await interaction.response.edit_message(
                content="✅ **Vote recorded!** You're good for the next 12 hours. Thanks for the support!",
                embed=None,
                view=None,
            )


# =============================================================================
# Public API
# =============================================================================

async def check_vote_gate(interaction: discord.Interaction, feature: str) -> bool:
    """
    Returns True if the user can proceed (premium guild or valid recent vote).
    If False, the gate message has already been sent to the user.
    """
    from core import entitlements
    if entitlements.is_premium(interaction.guild_id):
        return True

    if vote_core.has_voted(interaction.user.id):
        return True

    user_id = interaction.user.id
    state = vote_core.get_vote_state(user_id)

    if not state["vote_prompted"]:
        vote_core.mark_prompted(user_id)
        embed = _gate_embed(user_id)
        view = VoteGateView(user_id, feature)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        msg = f"🗳️ **{feature}** requires a vote. Run `/vote` for links."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    return False


async def show_vote_command(interaction: discord.Interaction):
    """Handler for /vote command."""
    embed = _vote_command_embed()
    view = VoteCommandView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
