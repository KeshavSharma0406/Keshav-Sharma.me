"""Write info-card.svg, a neofetch-style card. Edit ROWS to change what it says."""
from xml.sax.saxutils import escape

from svg_common import BORDER, GREEN, MUTED, PALETTE, ROOT, TEXT, USERNAME, window

OUT = ROOT / "info-card.svg"

# Same height as ascii-portrait.svg so the two line up side by side in the README.
WIDTH, HEIGHT = 560, 480

ROWS = [
    ("Name", "Keshav Sharma"),
    ("Now", "Founder & CEO, Founders Growth Studio"),
    ("Also", "Freelance Web Developer"),
    ("Frontend", "React · Next.js · Tailwind"),
    ("Backend", "PHP / WordPress"),
    ("AI", "Gemini API"),
    ("Web", "keshavsharma.me"),
    ("GitHub", f"@{USERNAME}"),
]

LABEL_X = 28
VALUE_X = 128
LINE = 33
STAGGER_MS = 110


def render():
    css = (
        "@keyframes rise{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}"
        "@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}"
        ".l{animation:rise .5s ease-out both}"
        ".cur{animation:blink 1.1s step-end 8 both}"
        "@media (prefers-reduced-motion:reduce){.l,.cur{animation:none}}"
    )

    def line(index, content):
        return f'<g class="l" style="animation-delay:{index * STAGGER_MS}ms">{content}</g>'

    parts = []
    y = 78
    host = "keshav@github"
    parts.append(line(0, f'<text x="{LABEL_X}" y="{y}" font-size="17" font-weight="600" fill="{GREEN}">{host}</text>'))
    y += 16
    parts.append(line(1, f'<line x1="{LABEL_X}" y1="{y}" x2="{WIDTH - LABEL_X}" y2="{y}" stroke="{BORDER}"/>'))
    y += 34

    index = 2
    for label, value in ROWS:
        parts.append(
            line(
                index,
                f'<text x="{LABEL_X}" y="{y}" font-size="15" font-weight="600" fill="{GREEN}">{escape(label)}</text>'
                f'<text x="{VALUE_X}" y="{y}" font-size="15" fill="{TEXT}">{escape(value)}</text>',
            )
        )
        y += LINE
        index += 1

    y += 2
    swatches = "".join(
        f'<rect x="{LABEL_X + i * 34}" y="{y}" width="28" height="14" rx="3" fill="{color}"/>'
        for i, color in enumerate(PALETTE)
    )
    parts.append(line(index, swatches))
    index += 1

    y += 48
    delay = index * STAGGER_MS
    parts.append(
        line(
            index,
            f'<text x="{LABEL_X}" y="{y}" font-size="15" fill="{MUTED}">$</text>'
            f'<rect class="cur" style="animation-delay:{delay}ms" x="{LABEL_X + 18}" y="{y - 13}" '
            f'width="9" height="16" fill="{GREEN}"/>',
        )
    )
    return window(WIDTH, HEIGHT, "whoami", css, "\n".join(parts))


def main():
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
