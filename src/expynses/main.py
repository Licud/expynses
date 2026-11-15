import flet as ft


def main(page: ft.Page):
    page.title = "expynses"
    page.add(ft.Text("Hello, world!", size=32))


if __name__ == "__main__":
    ft.run(main)
