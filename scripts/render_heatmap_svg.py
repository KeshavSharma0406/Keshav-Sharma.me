"""Render data/contributions.json as contrib-heatmap.svg."""
import json
from datetime import date, timedelta

from svg_common import BAR_HEIGHT, GREEN, MUTED, PALETTE, ROOT, window

DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

WIDTH, HEIGHT = 860, 242
CELL, GAP = 12, 3
STEP = CELL + GAP
GRID_X = 50
GRID_Y = BAR_HEIGHT + 32
MAX_WEEKS = 53
STAGGER_MS = 18


def build_grid(days):
    """Return (week, weekday, day) tuples, Sunday-first, for the last 53 weeks."""
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    cells = []
    for day in days:
        delta = (date.fromisoformat(day["date"]) - start).days
        cells.append((delta // 7, delta % 7, day))
    drop = max(0, max(c[0] for c in cells) + 1 - MAX_WEEKS)
    return [(w - drop, d, day) for w, d, day in cells if w >= drop]


def month_labels(cells):
    labels = []
    seen = None
    for week, weekday, day in sorted(cells, key=lambda c: (c[0], c[1])):
        month = day["date"][:7]
        if month != seen and weekday == 0:
            labels.append((week, date.fromisoformat(day["date"]).strftime("%b")))
            seen = month
    # Skip a label that would collide with the one after it.
    return [
        label
        for i, label in enumerate(labels)
        if i + 1 == len(labels) or labels[i + 1][0] - label[0] >= 3
    ]


def stat(x, value, label):
    return (
        f'<g class="foot"><text x="{x}" y="{GRID_Y + 136}" font-size="18" font-weight="600" '
        f'fill="{GREEN}">{value}</text>'
        f'<text x="{x}" y="{GRID_Y + 154}" font-size="11" fill="{MUTED}">{label}</text></g>'
    )


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def render(payload):
    stats = payload["stats"]
    cells = build_grid(payload["days"])
    best_date = stats["best_day"]["date"] if stats["best_day"]["count"] else None

    max_diagonal = max(w + d for w, d, _ in cells)
    css = (
        "@keyframes cell{from{opacity:0;transform:translate(-8px,-4px)}to{opacity:1;transform:none}}"
        "@keyframes foot{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}"
        ".c{animation:cell .42s ease-out both}"
        f".foot{{animation:foot .5s ease-out both;animation-delay:{max_diagonal * STAGGER_MS + 200}ms}}"
        + "".join(f".d{i}{{animation-delay:{i * STAGGER_MS}ms}}" for i in range(max_diagonal + 1))
        + "@media (prefers-reduced-motion:reduce){.c,.foot{animation:none}}"
    )

    parts = []
    for week, label in month_labels(cells):
        parts.append(
            f'<text x="{GRID_X + week * STEP}" y="{GRID_Y - 9}" font-size="11" fill="{MUTED}">{label}</text>'
        )
    for weekday, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{GRID_X - 8}" y="{GRID_Y + weekday * STEP + 10}" text-anchor="end" '
            f'font-size="10" fill="{MUTED}">{label}</text>'
        )

    for week, weekday, day in cells:
        fill = PALETTE[5] if day["date"] == best_date else PALETTE[day["level"]]
        parts.append(
            f'<rect class="c d{week + weekday}" x="{GRID_X + week * STEP}" y="{GRID_Y + weekday * STEP}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{fill}"/>'
        )

    best = "none yet"
    if best_date:
        best = f"{stats['best_day']['count']} on {date.fromisoformat(best_date).strftime('%b %d').replace(' 0', ' ')}"
    columns = [
        (GRID_X, f"{stats['total']:,}", "contributions, last year"),
        (GRID_X + 205, plural(stats["current_streak"], "day"), "current streak"),
        (GRID_X + 325, plural(stats["longest_streak"], "day"), "longest streak"),
        (GRID_X + 445, best, "best day"),
    ]
    parts.extend(stat(x, value, label) for x, value, label in columns)

    legend_right = GRID_X + (MAX_WEEKS * STEP) - GAP
    legend_x = legend_right - 5 * STEP - 30
    legend_y = GRID_Y + 124
    parts.append(
        f'<g class="foot"><text x="{legend_x - 8}" y="{legend_y + 10}" text-anchor="end" '
        f'font-size="11" fill="{MUTED}">Less</text>'
    )
    for i in range(5):
        parts.append(
            f'<rect x="{legend_x + i * STEP}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{PALETTE[i]}"/>'
        )
    parts.append(
        f'<text x="{legend_x + 5 * STEP + 5}" y="{legend_y + 10}" font-size="11" '
        f'fill="{MUTED}">More</text></g>'
    )

    updated = "updated " + payload["fetched_at"][:10]
    return window(WIDTH, HEIGHT, "contributions.sh", css, "\n".join(parts), right_note=updated)


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(render(payload), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
