"""The 'Categories' page: what each expense type cost, month by month."""

import datetime
import decimal

from collections.abc import Callable

import flet as ft

from expynses.ui import theme
from expynses.ui.charts import Bar, Group, Line, Segment, bar_chart, category_color, legend, line_chart, sparkline
from expynses.ui.expense_type_icons import icon_for_type
from expynses.ui.report_widgets import empty_state, page_header, period_switcher, segmented, stat_tile
from expynses.ui.reports_data import (
    ZERO,
    CategorySpending,
    add_months,
    all_category_names,
    category_spending,
    months_ending,
)

RANGES = {"3 months": 3, "6 months": 6, "12 months": 12}
CHART_STYLES = ["Bars", "Lines"]
TREND_WIDTH = 96


def _default_style(range_name: str) -> str:
    # Three points barely make a trend, so short ranges start as bars.
    return "Bars" if RANGES[range_name] <= 3 else "Lines"


def _month_label(month: datetime.date, count: int) -> str:
    # Show the year on January (and on the first column) so long ranges stay readable.
    return month.strftime("%b %y") if count > 3 and month.month == 1 else month.strftime("%b")


# SERVICE CANDIDATE: comparing a type's latest month to its earlier average is
# reporting logic; could be part of expenses.spending_by_type's result.
def _biggest_jump(data: CategorySpending) -> tuple[str, decimal.Decimal] | None:
    """The category whose latest month is furthest above its earlier average."""
    if len(data.months) < 2:
        return None
    last, earlier = data.months[-1], data.months[:-1]
    best: tuple[str, decimal.Decimal] | None = None
    for name in data.categories:
        average = sum((data.amount(name, m) for m in earlier), ZERO) / len(earlier)
        jump = data.amount(name, last) - average
        if jump > 0 and (best is None or jump > best[1]):
            best = (name, jump)
    return best


def _stats(data: CategorySpending) -> ft.Control:
    count = len(data.months)
    top = data.categories[0] if data.categories else None
    jump = _biggest_jump(data)
    last = data.months[-1]
    spending_months = sum(1 for m in data.months if data.month_total(m))
    return ft.Row(
        [
            stat_tile(ft.Icons.RECEIPT_LONG_OUTLINED, theme.ACCENT_TEXT, "Spent", theme.money(data.total),
                      f"Over {count} month{'s' if count > 1 else ''}, card spending included"),
            stat_tile(ft.Icons.SHOW_CHART, theme.SLATE, "Monthly average",
                      theme.money(data.total / spending_months) if spending_months else "—",
                      f"Across the {spending_months} month{'s' if spending_months != 1 else ''} with spending"),
            stat_tile(
                icon_for_type(top) if top else ft.Icons.CATEGORY,
                category_color(top, data.categories) if top else theme.MUTED,
                "Biggest category",
                top or "—",
                f"{theme.money(data.category_total(top))} · {data.category_total(top) / data.total:.0%} of spending"
                if top and data.total
                else None,
            ),
            stat_tile(
                ft.Icons.TRENDING_UP,
                theme.RED if jump else theme.GREEN,
                f"Up in {last:%B}",
                jump[0] if jump else "Nothing",
                f"{theme.money(jump[1])} above its usual" if jump else "No category above its average",
            ),
        ],
        spacing=14,
    )


def _bars(data: CategorySpending, groups: list[Group], names: list[str], focus: str | None) -> ft.Control:
    count = len(data.months)
    grouped = count <= 3  # side by side for a few months, stacked beyond that

    def color(c: str) -> str:
        # With a category focused, the others fade back.
        base = category_color(c, names)
        return theme.tinted(base, 0.22) if focus is not None and c != focus else base

    with_bars = []
    for group, month in zip(groups, data.months):
        if grouped:
            bars = [Bar.single(data.amount(c, month), color(c), c) for c in data.categories]
        else:
            bars = [Bar([Segment(data.amount(c, month), color(c), c) for c in data.categories])]
        with_bars.append(Group(group.label, bars, group.faded, group.highlighted, group.footer))
    bar_width = 22 if grouped else {6: 46, 12: 30}.get(count, 30)
    return bar_chart(with_bars, height=300, bar_width=bar_width, bar_gap=4)


def _lines(data: CategorySpending, groups: list[Group], names: list[str], focus: str | None,
           this_month: datetime.date) -> ft.Control:
    lines = [
        Line(
            name=c,
            color=category_color(c, names),
            # Months that haven't happened yet leave a gap rather than dropping to £0.
            values=[None if m > this_month else data.amount(c, m) for m in data.months],
        )
        for c in data.categories
    ]
    return line_chart(groups, lines, height=300, focus=focus)


def _chart(
    data: CategorySpending,
    names: list[str],
    this_month: datetime.date,
    style: str,
    focus: str | None,
    on_style: Callable[[str], None],
    on_focus: Callable[[str], None],
) -> ft.Control:
    count = len(data.months)
    groups = [
        Group(
            label=_month_label(month, count),
            highlighted=month == this_month,
            faded=month > this_month,
            footer=ft.Text(theme.money(data.month_total(month)), size=11, color=theme.MUTED),
        )
        for month in data.months
    ]
    if style == "Lines":
        chart = _lines(data, groups, names, focus, this_month)
        hint = "Hover a month for every category's amount. Click a category to focus on it."
    else:
        chart = _bars(data, groups, names, focus)
        hint = ("Hover a bar for the amount." if count <= 3 else "Each bar is a month; hover it for the breakdown.") + \
            " Click a category to focus on it."
    return theme.card(
        ft.Column(
            [
                theme.card_title("Spending by category", segmented(CHART_STYLES, style, on_style)),
                ft.Text(hint, size=12, color=theme.MUTED),
                ft.Container(height=2),
                legend([(category_color(c, names), c) for c in data.categories], on_click=on_focus, focus=focus),
                ft.Container(height=8),
                chart,
            ],
            spacing=4,
        ),
        padding=ft.Padding.only(left=20, right=24, top=20, bottom=18),
    )


def _heatmap(data: CategorySpending, names: list[str], this_month: datetime.date) -> ft.Control:
    """A grid of categories × months, each cell tinted by how big it is."""
    count = len(data.months)
    biggest = max((data.amount(c, m) for c in data.categories for m in data.months), default=ZERO)
    name_width = 150
    total_width = 104

    def header_cell(text: str, highlighted: bool = False, width: float | None = None) -> ft.Control:
        return ft.Container(
            width=width,
            expand=None if width else 1,
            alignment=ft.Alignment.CENTER_RIGHT,
            padding=ft.Padding.only(right=8),
            content=ft.Text(
                text.upper(),
                style=theme.label_style(),
                color=theme.ACCENT_TEXT if highlighted else None,
            ),
        )

    def amount_cell(amount: decimal.Decimal, color: str) -> ft.Control:
        strength = float(amount / biggest) if biggest else 0.0
        return ft.Container(
            expand=1,
            height=34,
            border_radius=6,
            alignment=ft.Alignment.CENTER_RIGHT,
            padding=ft.Padding.only(right=8),
            bgcolor=theme.tinted(color, 0.08 + 0.5 * strength) if amount else None,
            content=ft.Text(
                theme.money(amount) if amount else "–",
                size=12,
                color=theme.TEXT if strength > 0.45 else (theme.TEXT_SOFT if amount else theme.MUTED),
                weight=ft.FontWeight.W_600 if strength > 0.45 else ft.FontWeight.W_400,
            ),
        )

    rows: list[ft.Control] = [
        ft.Row(
            [
                ft.Container(width=name_width, content=theme.label("Category")),
                *[header_cell(_month_label(m, count), m == this_month) for m in data.months],
                header_cell("Total", width=total_width),
                header_cell("Share", width=64),
                ft.Container(width=TREND_WIDTH, alignment=ft.Alignment.CENTER, content=theme.label("Trend")),
            ],
            spacing=4,
        )
    ]
    for name in data.categories:
        color = category_color(name, names)
        total = data.category_total(name)
        rows.append(
            ft.Row(
                [
                    ft.Container(
                        width=name_width,
                        content=ft.Row(
                            [
                                ft.Icon(icon_for_type(name), size=16, color=color),
                                ft.Text(name, size=13, color=theme.TEXT, no_wrap=True,
                                        overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                            ],
                            spacing=8,
                        ),
                    ),
                    *[amount_cell(data.amount(name, m), color) for m in data.months],
                    ft.Container(
                        width=total_width,
                        alignment=ft.Alignment.CENTER_RIGHT,
                        padding=ft.Padding.only(right=8),
                        content=ft.Text(theme.money(total), size=13, weight=ft.FontWeight.W_600, color=theme.TEXT),
                    ),
                    ft.Container(
                        width=64,
                        alignment=ft.Alignment.CENTER_RIGHT,
                        padding=ft.Padding.only(right=8),
                        content=ft.Text(f"{total / data.total:.0%}" if data.total else "—", size=12,
                                        color=theme.MUTED),
                    ),
                    sparkline([data.amount(name, m) for m in data.months if m <= this_month], color,
                              width=TREND_WIDTH),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            )
        )
    # Totals along the bottom.
    rows.append(ft.Divider(height=8, color=theme.BORDER))
    rows.append(
        ft.Row(
            [
                ft.Container(width=name_width, content=ft.Text("Total", size=13, weight=ft.FontWeight.W_600,
                                                               color=theme.TEXT)),
                *[
                    ft.Container(
                        expand=1,
                        alignment=ft.Alignment.CENTER_RIGHT,
                        padding=ft.Padding.only(right=8),
                        content=ft.Text(theme.money(data.month_total(m)), size=12, weight=ft.FontWeight.W_600,
                                        color=theme.TEXT_SOFT),
                    )
                    for m in data.months
                ],
                ft.Container(
                    width=total_width,
                    alignment=ft.Alignment.CENTER_RIGHT,
                    padding=ft.Padding.only(right=8),
                    content=ft.Text(theme.money(data.total), size=13, weight=ft.FontWeight.W_700,
                                    color=theme.ACCENT_TEXT),
                ),
                ft.Container(width=64),
                ft.Container(width=TREND_WIDTH),
            ],
            spacing=4,
        )
    )
    return theme.card(
        ft.Column(
            [
                theme.card_title("Month by month"),
                ft.Text("Darker cells are the bigger amounts.", size=12, color=theme.MUTED),
                ft.Container(height=4),
                *rows,
            ],
            spacing=6,
        )
    )




def categories_view(page: ft.Page) -> ft.Control:
    today = datetime.date.today()
    this_month = today.replace(day=1)
    state: dict = {
        "last": this_month,
        "range": "3 months",
        "style": _default_style("3 months"),
        "focus": None,  # the category brought forward, if any
        "data": None,  # the CategorySpending on screen, kept so the chart can redraw without a reload
    }

    title = theme.heading("", size=30)
    range_box = ft.Container()
    chart_box = ft.Container()
    body = ft.Column(spacing=20, expand=True, scroll=ft.ScrollMode.AUTO)

    def draw_chart():
        data: CategorySpending = state["data"]
        chart_box.content = _chart(
            data, all_category_names(), this_month, state["style"], state["focus"], pick_style, toggle_focus
        )

    def load():
        count = RANGES[state["range"]]
        months = months_ending(state["last"], count)
        first, last = months[0], months[-1]
        title.value = (
            f"{first:%b} – {last:%b %Y}" if first.year == last.year else f"{first:%b %Y} – {last:%b %Y}"
        )
        range_box.content = segmented(list(RANGES), state["range"], pick_range)
        data = category_spending(months)
        state["data"] = data
        if state["focus"] not in data.categories:
            state["focus"] = None
        if not data.categories:
            body.controls = [theme.card(empty_state(ft.Icons.PIE_CHART_OUTLINE, "No spending in these months"))]
            return
        draw_chart()
        body.controls = [_stats(data), chart_box, _heatmap(data, all_category_names(), this_month),
                         ft.Container(height=8)]

    def refresh():
        load()
        page.update()

    def redraw():
        draw_chart()
        chart_box.update()

    def pick_range(option: str):
        state["range"] = option
        state["style"] = _default_style(option)
        refresh()

    def pick_style(option: str):
        state["style"] = option
        redraw()

    def toggle_focus(category: str):
        state["focus"] = None if state["focus"] == category else category
        redraw()

    def shift(delta: int):
        state["last"] = add_months(state["last"], delta)
        refresh()

    def go_to_today():
        state["last"] = this_month
        refresh()

    load()

    header = page_header(
        "Category spending",
        title,
        [range_box, ft.Container(width=4), period_switcher(lambda: shift(-1), go_to_today, lambda: shift(1))],
    )
    return ft.Column([header, body], spacing=24, expand=True)
