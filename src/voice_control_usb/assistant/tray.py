"""Branded Windows notification-area integration for the visible assistant."""

from __future__ import annotations

from typing import Callable


def create_brand_icon(size: int = 64):
    """Create the VC neon console mark as a Pillow image."""

    from PIL import Image, ImageDraw, ImageFont

    scale = max(size, 32)
    image = Image.new("RGBA", (scale, scale), "#060A12")
    draw = ImageDraw.Draw(image)
    margin = max(3, scale // 16)
    radius = max(6, scale // 7)
    draw.rounded_rectangle(
        (margin, margin, scale - margin - 1, scale - margin - 1),
        radius=radius,
        fill="#0D1526",
        outline="#22D3A7",
        width=max(2, scale // 18),
    )
    inset = margin + max(4, scale // 10)
    draw.line(
        (inset, scale - inset, scale // 2, inset),
        fill="#38BDF8",
        width=max(2, scale // 14),
    )
    draw.line(
        (scale // 2, inset, scale - inset, scale - inset),
        fill="#F472B6",
        width=max(2, scale // 14),
    )
    center = scale // 2
    draw.ellipse(
        (center - scale // 12, center - scale // 12, center + scale // 12, center + scale // 12),
        fill="#E8F1FF",
    )
    if scale >= 96:
        try:
            font = ImageFont.truetype("consola.ttf", scale // 8)
        except OSError:
            font = ImageFont.load_default()
        draw.text(
            (center, scale - inset - scale // 16),
            "VC",
            fill="#E8F1FF",
            font=font,
            anchor="mm",
        )
    return image.resize((size, size))


class TrayController:
    """Own the notification-area icon without coupling callbacks to Tk."""

    def __init__(
        self,
        on_open: Callable[[], None],
        on_exit: Callable[[], None],
        status_text: Callable[[], str],
    ) -> None:
        self.on_open = on_open
        self.on_exit = on_exit
        self.status_text = status_text
        self.icon: object | None = None

    def start(self) -> None:
        try:
            import pystray
        except ImportError as error:
            raise ImportError(
                "The Windows tray icon requires pystray. Install the Windows extras."
            ) from error

        menu = pystray.Menu(
            pystray.MenuItem(
                "Open Voice Control",
                lambda _icon, _item: self.on_open(),
                default=True,
            ),
            pystray.MenuItem(
                lambda _item: self.status_text(),
                lambda _icon, _item: None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Voice Control", lambda _icon, _item: self.on_exit()),
        )
        self.icon = pystray.Icon(
            "voice-control-usb",
            create_brand_icon(64),
            "Voice Control USB",
            menu,
        )
        self.icon.run_detached()

    def refresh(self) -> None:
        if self.icon is not None:
            self.icon.update_menu()

    def stop(self) -> None:
        if self.icon is not None:
            self.icon.stop()
            self.icon = None
