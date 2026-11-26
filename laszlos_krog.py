#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
from datetime import date
from utils import strip_trailing_empty_lines


def get_lazlos_week_menu(week_tag):
    """Extract the weekly menu for Laszlos Krog and return it as formatted text."""
    lunch_menu = week_tag.find_next(id=re.compile(r'^fdm-menu-\d+$'))

    if not lunch_menu:
        return None

    days = lunch_menu.find_all("ul")
    lines = []

    for day in days:
        day_name_tag = day.find("h3")
        if day_name_tag:
            if lines:
                lines.append("")
            lines.append(day_name_tag.get_text(strip=True))

        food_items = day.find_all("li", class_="fdm-item")
        for item in food_items:
            food_title_tag = item.find("p", class_="fdm-item-title")
            if food_title_tag:
                lines.append(f"\t{food_title_tag.get_text(strip=True)}")

            food_content_div = item.find("div", class_="fdm-item-content")
            if food_content_div:
                subtitles = food_content_div.find_all("p")
                for subtitle in subtitles:
                    subtitle_text = subtitle.get_text(strip=True)
                    if subtitle_text:
                        lines.append(f"\t\t{subtitle_text}")

    return strip_trailing_empty_lines("\n".join(lines))


def laszlos_krog():
    """Fetch and display the lunch menu for Laszlos Krog.

    Returns a dict with the restaurant name, source URL and the menu text
    (or None if the menu could not be retrieved).
    """
    name = "Laszlos Krog"
    url = "https://www.laszloskrog.se/ebbepark/"

    print("\n=============")
    print(name)
    print("=============")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return {"name": name, "url": url, "menu": None}

    soup = BeautifulSoup(response.content, "html.parser")
    week_tags = soup.find_all("p", class_="vecka")

    current_week_num = date.today().isocalendar().week

    for week_tag in week_tags:
        strong_tag = week_tag.find("strong")
        if not strong_tag:
            continue

        week_text = strong_tag.get_text(strip=True)
        match = re.match(r"VECKA\s+(\d+)", week_text, flags=re.IGNORECASE)

        if match:
            week_num = int(match.group(1))
            if week_num == current_week_num:
                menu = get_lazlos_week_menu(week_tag)
                if menu:
                    print(menu)
                else:
                    print("Could not find lunch menu on the page.")

                menu_url = url
                lunch_menu = week_tag.find_next(
                    id=re.compile(r'^fdm-menu-\d+$'))
                if lunch_menu:
                    pdf_link = lunch_menu.find_next(
                        "a", href=re.compile(r'\.pdf$', re.IGNORECASE))
                    if pdf_link and pdf_link.get("href"):
                        menu_url = pdf_link["href"]

                return {"name": name, "url": menu_url, "menu": menu}

    print("Current week's menu not found.")
    return {"name": name, "url": url, "menu": None}


if __name__ == "__main__":
    laszlos_krog()
