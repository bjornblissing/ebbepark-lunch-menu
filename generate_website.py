#!/usr/bin/env python3

"""
Generate a static HTML webpage showing today's lunch menus.

Runs every restaurant scraper and renders the results as a page of
restaurant tiles, each with a header linking back to the scraped page.
"""

import html
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from laszlos_krog import laszlos_krog
from la_luna import laluna
from don_luigi import don_luigi

OUTPUT_FILE = "index.html"
LOCAL_TIMEZONE = ZoneInfo("Europe/Stockholm")

_SWEDISH_WEEKDAYS = [
    "måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag",
]
_SWEDISH_MONTHS = [
    "januari", "februari", "mars", "april", "maj", "juni",
    "juli", "augusti", "september", "oktober", "november", "december",
]


def _format_swedish_datetime(moment):
    """Format a datetime using Swedish weekday/month names, e.g.

    "torsdag 4 september 2025, 14:30".
    """
    weekday = _SWEDISH_WEEKDAYS[moment.weekday()]
    month = _SWEDISH_MONTHS[moment.month - 1]
    return f"{weekday} {moment.day} {month} {moment.year}, {moment.strftime('%H:%M')}"


STYLE = """
    :root {
        color-scheme: light;
        --bg: #f4efe6;
        --card-bg: #ffffff;
        --accent: #d9534f;
        --heading: #2f2f2f;
        --text: #4a4a4a;
        --muted: #9a9a9a;
        --border: #ece3d6;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 2.5rem 1.5rem;
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        background: linear-gradient(180deg, #fbf8f2 0%, var(--bg) 100%);
        color: var(--text);
    }
    header.page-header {
        text-align: center;
        margin-bottom: 2.5rem;
    }
    header.page-header h1 {
        font-size: 2.4rem;
        margin: 0 0 0.4rem;
        color: var(--heading);
    }
    header.page-header p {
        margin: 0;
        color: var(--muted);
        font-size: 0.95rem;
    }
    .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .tile {
        background: var(--card-bg);
        border-radius: 14px;
        border: 1px solid var(--border);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
        overflow: hidden;
        display: flex;
        flex-direction: column;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.1);
    }
    .tile-header {
        background: var(--accent);
        padding: 1rem 1.25rem;
    }
    .tile-header a {
        color: #ffffff;
        text-decoration: none;
        font-size: 1.25rem;
        font-weight: 600;
    }
    .tile-header a:hover {
        text-decoration: underline;
    }
    .tile-body {
        padding: 1.1rem 1.25rem 1.4rem;
        flex: 1;
    }
    .menu-heading {
        font-weight: 700;
        color: var(--heading);
        margin: 0.9rem 0 0.3rem;
    }
    .menu-heading:first-child {
        margin-top: 0;
    }
    .menu-item {
        margin: 0.15rem 0 0.15rem 0.4rem;
    }
    .menu-subitem {
        margin: 0.1rem 0 0.1rem 1.2rem;
        color: var(--muted);
        font-size: 0.92rem;
    }
    .no-menu {
        color: var(--muted);
        font-style: italic;
    }
    .tile-laszlos-krog .menu-item {
        font-weight: 700;
        color: var(--heading);
        margin-top: 0.9rem;
    }
    .tile-laszlos-krog .menu-item:first-of-type {
        margin-top: 0.15rem;
    }
    footer.page-footer {
        text-align: center;
        margin-top: 2.5rem;
        color: var(--muted);
        font-size: 0.85rem;
    }
"""


def _menu_to_html(menu_text):
    """Convert plain-text menu content (tab-indented) into HTML markup."""
    if not menu_text or not menu_text.strip():
        return '<p class="no-menu">Ingen meny tillgänglig.</p>'

    parts = []
    for raw_line in menu_text.split("\n"):
        line = raw_line.rstrip()
        stripped = line.lstrip("\t")
        if not stripped.strip():
            continue

        indent_level = len(line) - len(stripped)
        text = html.escape(stripped.strip())

        if indent_level == 0:
            parts.append(f'<div class="menu-heading">{text}</div>')
        elif indent_level == 1:
            parts.append(f'<div class="menu-item">{text}</div>')
        else:
            parts.append(f'<div class="menu-subitem">{text}</div>')

    return "\n".join(parts) if parts else '<p class="no-menu">Ingen meny tillgänglig.</p>'


def _slugify(name):
    """Turn a restaurant name into a CSS-class-friendly slug."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def _tile_html(restaurant):
    raw_name = restaurant.get("name") or "Unknown restaurant"
    name = html.escape(raw_name)
    url = html.escape(restaurant.get("url") or "#", quote=True)
    menu_html = _menu_to_html(restaurant.get("menu"))
    slug = _slugify(raw_name)

    return f"""
      <article class="tile tile-{slug}">
        <header class="tile-header">
          <a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>
        </header>
        <div class="tile-body">
          {menu_html}
        </div>
      </article>"""


def generate_website(restaurants, output_file=OUTPUT_FILE):
    """Render the collected restaurant menus as a static HTML page."""
    tiles_html = "\n".join(_tile_html(restaurant)
                           for restaurant in restaurants)
    generated_at = _format_swedish_datetime(datetime.now(LOCAL_TIMEZONE))

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dagens Lunch i Ebbepark</title>
  <style>{STYLE}</style>
</head>
<body>
  <header class="page-header">
    <h1>Dagens Lunch i Ebbepark</h1>
    <p>Senast uppdaterad {html.escape(generated_at)}</p>
  </header>
  <main class="tiles">{tiles_html}
  </main>
  <footer class="page-footer">
    <p>Automatiskt genererade ifrån restaurangernas hemsidor.</p>
  </footer>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"\nWebsite generated: {output_file}")


def main():
    """Fetch all restaurant menus and generate the static webpage."""
    restaurants = [
        laluna(),
        laszlos_krog(),
        don_luigi(),
    ]
    generate_website(restaurants)


if __name__ == "__main__":
    main()
