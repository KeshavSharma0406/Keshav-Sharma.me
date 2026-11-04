"""Shared settings and terminal-window chrome for the profile SVGs."""
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "KeshavSharma0406"
ROOT = Path(__file__).resolve().parent.parent

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#39d353"
# Heatmap levels 0-4, then the highlight used for the best day.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

FONT = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace'
BAR_HEIGHT = 34


def window(width, height, title, css, body, right_note=""):
    """Wrap body in a terminal window. All animation stays inside the SVG
    because GitHub strips scripts and external CSS from READMEs."""
    note = ""
    if right_note:
        note = (
            f'<text x="{width - 16}" y="22" text-anchor="end" font-size="11" '
            f'fill="{MUTED}">{escape(right_note)}</text>'
        )
    dots = "".join(
        f'<circle cx="{18 + i * 16}" cy="17" r="4.5" fill="{BORDER}"/>' for i in range(3)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family=\'{FONT}\' role="img" '
        f'aria-label="{escape(title)}">\n'
        f"<style>{css}</style>\n"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>\n'
        f'<line x1="1" y1="{BAR_HEIGHT}" x2="{width - 1}" y2="{BAR_HEIGHT}" stroke="{BORDER}"/>\n'
        f"{dots}\n"
        f'<text x="{width / 2}" y="22" text-anchor="middle" font-size="12" '
        f'fill="{MUTED}">{escape(title)}</text>\n'
        f"{note}\n{body}\n</svg>\n"
    )
