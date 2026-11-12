import logging

import discord

log = logging.getLogger(__name__)


class OwnerView(discord.ui.View):
    """Зөвхөн командыг дуудсан хүн ашиглаж чадах цэс."""

    def __init__(self, owner_id: int, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Энэ цэс таных биш. Өөрөө команд ажиллуулна уу.", ephemeral=True
            )
            return False
        return True

    async def on_error(self, interaction, error, item):
        log.exception("Цэсийн алдаа", exc_info=error)
        msg = "❌ Алдаа гарлаа. Дахин оролдоно уу."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass

    def disable_all(self):
        for child in self.children:
            child.disabled = True

    async def on_timeout(self):
        self.disable_all()
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


def nav_button(label: str, callback, style=None, disabled: bool = False, row: int | None = None):
    btn = discord.ui.Button(
        label=label,
        style=style or discord.ButtonStyle.secondary,
        disabled=disabled,
        row=row,
    )
    btn.callback = callback
    return btn


async def safe_edit(interaction, **kw):
    """3 секундээс удаан бол «didn't respond» гарахаас сэргийлж эхлээд defer хийнэ."""
    if not interaction.response.is_done():
        await interaction.response.defer()
    await interaction.edit_original_response(**kw)
