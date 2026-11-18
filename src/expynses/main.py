from pathlib import Path

import flet as ft

from expynses.db import init_db
from expynses.ui.shell import app_shell
from expynses.ui.theme import apply_theme

ASSETS_DIR = Path(__file__).parent / "assets"


def main(page: ft.Page):
    page.title = "expynses"
    page.window.icon = "icon.ico"  # looked up in ASSETS_DIR
    page.window.maximized = True
    page.window.width = 1360
    page.window.height = 820
    page.window.min_width = 1100
    page.window.min_height = 640
    apply_theme(page)
    page.padding = 0
    page.add(app_shell(page))


if __name__ == "__main__":
    init_db()
    ft.run(main, assets_dir=str(ASSETS_DIR))
