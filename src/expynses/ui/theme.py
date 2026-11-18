"""The app's look: colours, fonts and small building blocks shared by every page."""

import decimal

from collections.abc import Callable

import flet as ft

# --- Palette (warm dark) ---
BG = "#121010"
SURFACE = "#1a1715"
SURFACE_HIGH = "#231f1c"
SURFACE_HOVER = "#2a2522"
BORDER = "#2c2622"
TEXT = "#ece6df"
TEXT_SOFT = "#bfb5ab"
MUTED = "#857a71"
ACCENT = "#cf7a5c"  # buttons, selection
ACCENT_TEXT = "#e0764f"  # amounts, active labels
ON_ACCENT = "#1a1210"
GREEN = "#6fd1a3"
AMBER = "#e0b15a"
SLATE = "#8fa3b8"
RED = "#e57373"

# --- Shape ---
RADIUS = 14  # cards
RADIUS_SM = 10  # buttons, icon tiles, inputs
CONTROL_HEIGHT = 36  # buttons and the month switcher

# --- Fonts ---
# System fonts for now. Georgia gives the serif headings from the style guide.
BODY_FONT = "Segoe UI"
HEADING_FONT = "Georgia"


def apply_theme(page: ft.Page) -> None:
    scheme = ft.ColorScheme(
        primary=ACCENT,
        on_primary=ON_ACCENT,
        secondary=ACCENT,
        on_secondary=ON_ACCENT,
        secondary_container="#3a2b25",
        on_secondary_container=TEXT,
        surface=SURFACE,
        on_surface=TEXT,
        on_surface_variant=MUTED,
        outline="#4a4039",
        outline_variant=BORDER,
        surface_container_lowest=BG,
        surface_container_low=SURFACE,
        surface_container=SURFACE,
        surface_container_high=SURFACE_HIGH,
        surface_container_highest=SURFACE_HIGH,
        inverse_surface=TEXT,
        on_inverse_surface=BG,
        error=RED,
    )
    theme = ft.Theme(color_scheme=scheme, font_family=BODY_FONT)
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = theme
    page.dark_theme = theme
    page.bgcolor = BG


# --- Text ---


def heading(text: str, size: int = 28, color: str = TEXT) -> ft.Text:
    """A serif heading."""
    return ft.Text(text, size=size, font_family=HEADING_FONT, color=color)


def label_style() -> ft.TextStyle:
    """Small spaced-out uppercase labels, for captions and column headers."""
    return ft.TextStyle(
        size=11,
        letter_spacing=1.2,
        weight=ft.FontWeight.W_600,
        color=MUTED,
    )


def label(text: str) -> ft.Text:
    return ft.Text(text.upper(), style=label_style())


def money(amount: decimal.Decimal) -> str:
    sign = "−" if amount < 0 else ""
    return f"{sign}£{abs(amount):,.2f}"


def tinted(color: str, opacity: float = 0.15) -> str:
    return ft.Colors.with_opacity(opacity, color)


# --- Building blocks ---

_HOVER_ANIMATION = ft.Animation(140, ft.AnimationCurve.EASE_OUT)


def hoverable(control: ft.Container, hover_color: str = SURFACE_HIGH) -> ft.Container:
    """Give a container a soft background on mouse-over."""
    resting = control.bgcolor

    def on_hover(e: ft.Event[ft.Container]):
        e.control.bgcolor = hover_color if e.data else resting
        e.control.update()

    control.on_hover = on_hover
    control.animate = _HOVER_ANIMATION
    return control


def card(content: ft.Control, padding: ft.PaddingValue = 20, **kwargs) -> ft.Container:
    """A flat surface with a hairline edge."""
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=SURFACE,
        border=ft.Border.all(1, BORDER),
        border_radius=RADIUS,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        **kwargs,
    )


def card_title(text: str, trailing: ft.Control | None = None) -> ft.Control:
    """A card's heading line, with an optional control on the right."""
    controls: list[ft.Control] = [
        ft.Text(text, size=15, weight=ft.FontWeight.W_600, color=TEXT)
    ]
    if trailing is not None:
        controls += [ft.Container(expand=True), trailing]
    return ft.Row(controls, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def icon_tile(icon: ft.IconData, color: str, size: int = 34) -> ft.Control:
    """An icon on a tinted rounded square."""
    return ft.Container(
        content=ft.Icon(icon, size=size * 0.5, color=color),
        width=size,
        height=size,
        bgcolor=tinted(color, 0.13),
        border_radius=RADIUS_SM,
        alignment=ft.Alignment.CENTER,
    )


def dot(color: str, size: int = 8) -> ft.Control:
    return ft.Container(width=size, height=size, bgcolor=color, border_radius=size)


def badge(text: str, color: str = MUTED) -> ft.Control:
    """A small rounded count or tag."""
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color),
        bgcolor=tinted(color, 0.14),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=7, vertical=2),
    )


def bar(parts: list[tuple[float, str]], height: int = 6, track: str = SURFACE_HOVER) -> ft.Control:
    """A rounded horizontal bar split into coloured parts.

    parts are (fraction, colour) pairs; whatever is left over shows the track.
    """
    segments: list[ft.Control] = []
    used = 0
    for fraction, color in parts:
        flex = round(max(fraction, 0) * 1000)
        if flex:
            segments.append(ft.Container(bgcolor=color, expand=flex, height=height))
            used += flex
    if used < 1000:
        segments.append(ft.Container(expand=1000 - used, height=height))
    return ft.Container(
        content=ft.Row(segments, spacing=2 if len(parts) > 1 else 0),
        bgcolor=track,
        border_radius=height,
        height=height,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def action_button(
    text: str,
    icon: ft.IconData,
    on_click: Callable[[], None],
    primary: bool = True,
) -> ft.Control:
    """A compact header button: solid accent for the main action, ghost otherwise."""
    fg = ON_ACCENT if primary else TEXT_SOFT
    content = ft.Row(
        [
            ft.Icon(icon, size=16, color=fg),
            ft.Text(text, size=13, weight=ft.FontWeight.W_600, color=fg),
        ],
        spacing=6,
        tight=True,
    )
    button = ft.Container(
        content=content,
        height=CONTROL_HEIGHT,
        padding=ft.Padding.symmetric(horizontal=14),
        alignment=ft.Alignment.CENTER,
        border_radius=RADIUS_SM,
        bgcolor=ACCENT if primary else SURFACE,
        border=None if primary else ft.Border.all(1, BORDER),
        on_click=lambda _: on_click(),
        tooltip=None,
    )
    return hoverable(button, "#dc8a6c" if primary else SURFACE_HIGH)


def icon_button(icon: ft.IconData, tooltip: str, on_click: Callable[[], None], size: int = 32) -> ft.Control:
    """A small square icon-only button with a hover background."""
    return hoverable(
        ft.Container(
            content=ft.Icon(icon, size=18, color=TEXT_SOFT),
            width=size,
            height=size,
            border_radius=8,
            alignment=ft.Alignment.CENTER,
            tooltip=tooltip,
            on_click=lambda _: on_click(),
        ),
        SURFACE_HOVER,
    )
