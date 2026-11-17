"""The app's look: colours, fonts and a few text helpers, from the style guide."""

import flet as ft

# --- Palette (warm dark) ---
BG = "#131110"
SURFACE = "#1c1816"
SURFACE_HIGH = "#25201d"
BORDER = "#322b26"
TEXT = "#ece6df"
MUTED = "#8c8178"
ACCENT = "#cf7a5c"  # buttons, selection
ACCENT_TEXT = "#e0764f"  # amounts, active labels
ON_ACCENT = "#1a1210"
GREEN = "#6fd1a3"
AMBER = "#e0b15a"
SLATE = "#8fa3b8"

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
        error="#e57373",
    )
    theme = ft.Theme(color_scheme=scheme, font_family=BODY_FONT)
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = theme
    page.dark_theme = theme
    page.bgcolor = BG


def heading(text: str, size: int = 28) -> ft.Text:
    """A serif heading."""
    return ft.Text(text, size=size, font_family=HEADING_FONT, color=TEXT)


def label_style() -> ft.TextStyle:
    """Small spaced-out uppercase labels, for table headers and tile captions."""
    return ft.TextStyle(
        size=11,
        letter_spacing=1.2,
        weight=ft.FontWeight.W_600,
        color=MUTED,
    )


def label(text: str) -> ft.Text:
    return ft.Text(text.upper(), style=label_style())


def tinted(color: str, opacity: float = 0.15) -> str:
    return ft.Colors.with_opacity(opacity, color)
