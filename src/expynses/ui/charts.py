"""Small bar, line and sparkline charts built from plain Flet controls.

Drawn by hand to avoid the separate `flet-charts` dependency and to match the app theme.
A chart is a row of groups (usually months); each group holds bars, each bar holds stacked segments.
"""

import decimal
import math

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import flet as ft
import flet.canvas as cv

from expynses.ui import theme

AXIS_WIDTH = 58
COLUMN_GAP = 4  # space between groups; the line chart relies on it to line up


@dataclass(frozen=True)
class Segment:
    value: decimal.Decimal
    color: str
    name: str  # shown in the hover tooltip


@dataclass(frozen=True)
class Bar:
    segments: list[Segment]

    @property
    def total(self) -> decimal.Decimal:
        return sum((s.value for s in self.segments), decimal.Decimal(0))

    @staticmethod
    def single(value: decimal.Decimal, color: str, name: str) -> "Bar":
        return Bar([Segment(value, color, name)])


@dataclass(frozen=True)
class Group:
    label: str
    bars: list[Bar] = field(default_factory=list)
    faded: bool = False  # e.g. months that haven't happened yet
    highlighted: bool = False  # e.g. the current month
    footer: ft.Control | None = field(default=None)  # a small control under the label


@dataclass(frozen=True)
class Line:
    name: str
    color: str
    values: list[decimal.Decimal | None]  # one per group; None leaves a gap (e.g. future months)


# --- Shared scaffolding ---


def _nice_step(span: float, ticks: int = 4) -> float:
    """A round gridline step (1, 2, 2.5 or 5 × 10ⁿ) that splits `span` into about `ticks` parts."""
    if span <= 0:
        return 100.0
    raw = span / ticks
    power = 10 ** math.floor(math.log10(raw))
    for nice in (1, 2, 2.5, 5, 10):
        if raw <= nice * power:
            return nice * power
    return 10 * power


def axis_money(value: float) -> str:
    """Short money for axis labels: £800, £1.5k, £20k."""
    sign = "−" if value < 0 else ""
    value = abs(value)
    if value >= 1000:
        text = f"{value / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{sign}£{text}k"
    return f"{sign}£{value:,.0f}"


def _axis(lowest: float, highest: float, height: int) -> tuple[float, float, list[ft.Control], list[ft.Control]]:
    """Work out the vertical scale for a value range.

    Returns (pixels per £, y of the zero line, gridline controls, axis label controls).
    """
    highest, lowest = max(highest, 0.0), min(lowest, 0.0)
    step = _nice_step(highest - lowest)
    top = math.ceil(highest / step) * step if highest > 0 else (step if lowest == 0 else 0.0)
    bottom = math.ceil(-lowest / step) * step if lowest < 0 else 0.0
    scale = height / (top + bottom)
    zero_y = top * scale

    grid: list[ft.Control] = []
    labels: list[ft.Control] = []
    ticks = round((top + bottom) / step)
    for i in range(ticks + 1):
        value = -bottom + i * step
        y = zero_y - value * scale
        is_zero = abs(value) < step / 1000
        grid.append(
            ft.Container(
                top=min(max(y, 0), height - 1),
                left=0,
                right=0,
                height=1,
                bgcolor=theme.MUTED if is_zero else theme.BORDER,
                opacity=0.6 if is_zero else 1.0,
            )
        )
        labels.append(
            ft.Container(
                top=min(max(y - 8, -8), height - 8),
                right=8,
                content=ft.Text(axis_money(value), size=11, color=theme.MUTED),
            )
        )
    return scale, zero_y, grid, labels


def _footers(groups: Sequence[Group]) -> ft.Control:
    return ft.Row(
        [
            ft.Container(
                expand=1,
                content=ft.Column(
                    [
                        ft.Text(
                            g.label,
                            size=12,
                            weight=ft.FontWeight.W_600 if g.highlighted else ft.FontWeight.W_500,
                            color=theme.ACCENT_TEXT if g.highlighted else (theme.MUTED if g.faded else theme.TEXT_SOFT),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        *([g.footer] if g.footer is not None else []),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            for g in groups
        ],
        spacing=COLUMN_GAP,
    )


def _frame(axis_labels: list[ft.Control], plot: ft.Control, groups: Sequence[Group], height: int) -> ft.Control:
    """Axis on the left, plot on the right, group labels underneath."""
    axis = ft.Stack(axis_labels, width=AXIS_WIDTH, height=height, clip_behavior=ft.ClipBehavior.NONE)
    return ft.Column(
        [
            ft.Row([axis, plot], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([ft.Container(width=AXIS_WIDTH), ft.Container(content=_footers(groups), expand=True)], spacing=0),
        ],
        spacing=8,
    )


def _highlight_row(groups: Sequence[Group], height: int) -> ft.Control:
    """A soft background behind highlighted groups (the current month)."""
    return ft.Row(
        [
            ft.Container(
                expand=1,
                height=height,
                border_radius=8,
                bgcolor=theme.tinted(theme.ACCENT, 0.06) if g.highlighted else None,
            )
            for g in groups
        ],
        spacing=COLUMN_GAP,
    )


def _fill(control: ft.Control) -> ft.Control:
    """Stretch a control over the whole of a Stack."""
    return ft.Container(left=0, right=0, top=0, bottom=0, content=control)


# --- Bars ---


def _tooltip(group: Group, bar: Bar) -> str:
    lines = [group.label]
    if len(bar.segments) > 1:
        lines += [f"{s.name}: {theme.money(s.value)}" for s in bar.segments if s.value]
        lines.append(f"Total: {theme.money(bar.total)}")
    else:
        s = bar.segments[0]
        lines.append(f"{s.name}: {theme.money(s.value)}")
    return "\n".join(lines)


def _bar_control(group: Group, bar: Bar, width: float, scale: float, zero_y: float, height: float) -> ft.Control:
    total = float(bar.total)
    bar_height = abs(total) * scale
    upwards = total >= 0
    # Positive bars stack bottom-up (first segment at the bottom); negative ones top-down.
    segments = [s for s in bar.segments if s.value]
    pieces = [
        ft.Container(height=max(abs(float(s.value)) * scale, 0), bgcolor=s.color, width=width)
        for s in (reversed(segments) if upwards else segments)
    ]
    radius = min(4, width / 2)
    shape = ft.Container(
        content=ft.Column(pieces, spacing=0),
        width=width,
        height=bar_height,
        border_radius=ft.BorderRadius.only(top_left=radius, top_right=radius)
        if upwards
        else ft.BorderRadius.only(bottom_left=radius, bottom_right=radius),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        tooltip=_tooltip(group, bar),
        opacity=0.35 if group.faded else 1.0,
    )
    return ft.Column(
        [
            ft.Container(
                height=zero_y,
                width=width,
                alignment=ft.Alignment.BOTTOM_CENTER,
                content=shape if upwards and segments else None,
            ),
            ft.Container(
                height=height - zero_y,
                width=width,
                alignment=ft.Alignment.TOP_CENTER,
                content=shape if not upwards and segments else None,
            ),
        ],
        spacing=0,
    )


def bar_chart(
    groups: Sequence[Group],
    height: int = 280,
    bar_width: float = 14,
    bar_gap: float = 3,
) -> ft.Control:
    """Draw the groups as bars over a light grid, with money on the left axis."""
    highest = max((float(b.total) for g in groups for b in g.bars), default=0.0)
    lowest = min((float(b.total) for g in groups for b in g.bars), default=0.0)
    scale, zero_y, grid, labels = _axis(lowest, highest, height)

    columns = [
        ft.Container(
            expand=1,
            height=height,
            content=ft.Row(
                [_bar_control(group, b, bar_width, scale, zero_y, height) for b in group.bars],
                spacing=bar_gap,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        for group in groups
    ]
    plot = ft.Stack(
        [_fill(_highlight_row(groups, height)), *grid, _fill(ft.Row(columns, spacing=COLUMN_GAP))],
        height=height,
        expand=True,
    )
    return _frame(labels, plot, groups, height)


# --- Lines ---


def _column_centres(width: float, count: int) -> list[float]:
    """x of the middle of each group, matching the Row(spacing=COLUMN_GAP) the labels use."""
    column = (width - COLUMN_GAP * (count - 1)) / count
    return [i * (column + COLUMN_GAP) + column / 2 for i in range(count)]


def _stroke(color: str, width: float) -> ft.Paint:
    return ft.Paint(
        color=color,
        stroke_width=width,
        style=ft.PaintingStyle.STROKE,
        stroke_cap=ft.StrokeCap.ROUND,
        stroke_join=ft.StrokeJoin.ROUND,
    )


def _line_shapes(
    lines: Sequence[Line], xs: list[float], scale: float, zero_y: float, focus: str | None
) -> list[cv.Shape]:
    shapes: list[cv.Shape] = []
    # Draw the focused line last so it sits on top of the faded ones.
    for line in sorted(lines, key=lambda line: line.name == focus):
        focused = line.name == focus
        dimmed = focus is not None and not focused
        color = theme.tinted(line.color, 0.2) if dimmed else line.color
        elements: list[cv.Path.PathElement] = []
        points: list[tuple[float, float]] = []
        pen_down = False
        for x, value in zip(xs, line.values):
            if value is None:
                pen_down = False
                continue
            y = zero_y - float(value) * scale
            elements.append(cv.Path.LineTo(x, y) if pen_down else cv.Path.MoveTo(x, y))
            points.append((x, y))
            pen_down = True
        shapes.append(cv.Path(elements, paint=_stroke(color, 3 if focused else 2)))
        if dimmed:
            continue
        # Hollow dots on each point: a surface-coloured fill, then a ring.
        radius = 4.5 if focused else 3.5
        for x, y in points:
            shapes.append(cv.Circle(x, y, radius, paint=ft.Paint(color=theme.SURFACE)))
            shapes.append(cv.Circle(x, y, radius, paint=_stroke(color, 2)))
    return shapes


def _line_tooltip(group: Group, lines: Sequence[Line], index: int) -> str | None:
    values = [(line.name, line.values[index]) for line in lines if line.values[index] is not None]
    if not values:
        return None
    spent = sorted(((name, v) for name, v in values if v), key=lambda pair: pair[1], reverse=True)
    if not spent:
        return f"{group.label}\nNothing spent"
    return "\n".join([group.label, *(f"{name}: {theme.money(v)}" for name, v in spent)])


def line_chart(
    groups: Sequence[Group],
    lines: Sequence[Line],
    height: int = 280,
    focus: str | None = None,
) -> ft.Control:
    """One line per series across the groups, drawn on a canvas.

    `focus` names a line to bring forward; the others fade back. Hovering a
    group shows every line's value there.
    """
    values = [float(v) for line in lines for v in line.values if v is not None]
    scale, zero_y, grid, labels = _axis(min(values, default=0.0), max(values, default=0.0), height)

    def on_resize(e: cv.CanvasResizeEvent):
        # The canvas only learns its width once laid out, so draw from here.
        canvas.shapes = _line_shapes(lines, _column_centres(e.width, len(groups)), scale, zero_y, focus)
        canvas.update()

    canvas = cv.Canvas(left=0, right=0, top=0, bottom=0, on_resize=on_resize, resize_interval=50)

    # Invisible columns on top of the lines, one per group, carrying the tooltips.
    hover_columns = ft.Row(
        [
            theme.hoverable(
                ft.Container(expand=1, height=height, border_radius=8, tooltip=_line_tooltip(g, lines, i)),
                theme.tinted(theme.TEXT, 0.04),
            )
            for i, g in enumerate(groups)
        ],
        spacing=COLUMN_GAP,
    )
    plot = ft.Stack(
        [_fill(_highlight_row(groups, height)), *grid, canvas, _fill(hover_columns)],
        height=height,
        expand=True,
    )
    return _frame(labels, plot, groups, height)


def sparkline(values: Sequence[decimal.Decimal], color: str, width: float = 96, height: float = 26) -> ft.Control:
    """A tiny trend line with no axis, scaled from zero to the biggest value."""
    biggest = max((float(v) for v in values), default=0.0)
    if len(values) < 2 or biggest <= 0:
        return ft.Container(width=width, height=height)
    pad = 3
    step = (width - 2 * pad) / (len(values) - 1)
    points = [(pad + i * step, height - pad - float(v) / biggest * (height - 2 * pad)) for i, v in enumerate(values)]
    outline: list[cv.Path.PathElement] = [cv.Path.MoveTo(*points[0]), *(cv.Path.LineTo(x, y) for x, y in points[1:])]
    area = [*outline, cv.Path.LineTo(points[-1][0], height), cv.Path.LineTo(points[0][0], height), cv.Path.Close()]
    last_x, last_y = points[-1]
    return cv.Canvas(
        [
            cv.Path(area, paint=ft.Paint(color=theme.tinted(color, 0.12))),
            cv.Path(outline, paint=_stroke(color, 1.5)),
            cv.Circle(last_x, last_y, 2.5, paint=ft.Paint(color=color)),
        ],
        width=width,
        height=height,
    )


# --- Legend ---


def legend(
    items: Sequence[tuple[str, str]],
    on_click: Callable[[str], None] | None = None,
    focus: str | None = None,
) -> ft.Control:
    """A row of (colour, name) keys.

    With `on_click`, each key becomes a button (used to focus one series); the
    `focus`ed key stays bright and the rest dim.
    """
    keys: list[ft.Control] = []
    for color, name in items:
        dimmed = focus is not None and name != focus
        key = ft.Row(
            [
                theme.dot(theme.tinted(color, 0.35) if dimmed else color, 9),
                ft.Text(
                    name,
                    size=12,
                    color=theme.MUTED if dimmed else theme.TEXT_SOFT,
                    weight=ft.FontWeight.W_600 if name == focus else None,
                ),
            ],
            spacing=6,
            tight=True,
        )
        if on_click is None:
            keys.append(key)
            continue
        keys.append(
            theme.hoverable(
                ft.Container(
                    key,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                    border_radius=6,
                    bgcolor=theme.SURFACE_HIGH if name == focus else None,
                    on_click=lambda _, n=name: on_click(n),
                    tooltip="Show all again" if name == focus else f"Focus on {name}",
                ),
                theme.SURFACE_HOVER,
            )
        )
    return ft.Row(keys, spacing=10 if on_click else 16, wrap=True)


# --- Category colours ---

# Warm, distinct colours per expense type, matched by name like the icons are.
_CATEGORY_COLORS = {
    "Eating Out": "#e0764f",
    "Grocery": "#e0b15a",
    "Travel": "#6fd1a3",
    "Games": "#b0644a",
    "Bills": "#8fa3b8",
    "Shopping": "#7fae6b",
    "Car": "#f0a789",
    "Withdrawal": "#c49aa8",
    "Other": "#a39486",
}
_SPARE_COLORS = ["#d4c06a", "#7cc4c4", "#d98c9e", "#9f8fd1", "#c9a27e"]


def category_color(name: str, all_names: Sequence[str]) -> str:
    """A colour for an expense type; types without one get a spare, stably."""
    if name in _CATEGORY_COLORS:
        return _CATEGORY_COLORS[name]
    unknown = [n for n in all_names if n not in _CATEGORY_COLORS]
    index = unknown.index(name) if name in unknown else len(unknown)
    return _SPARE_COLORS[index % len(_SPARE_COLORS)]
