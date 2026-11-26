#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
from utils import strip_trailing_empty_lines

_TRAILING_DOT_RE = re.compile(r"[ \t]+\.[ \t]*$")
_FLOATING_DOT_RE = re.compile(r"[ \t]+\.[ \t]*(?=\S)")


def _split_floating_dish(text):
    """Split a dish line on a stray "." that separates two dishes.

    Some dishes on the page are only separated by a period with a space
    before it but not attached to the preceding word (e.g.
    "... bearnaisesås . Högrevsburgare ..."). This drops that stray period
    and, if more text follows it, splits the line so each dish becomes its
    own row.
    """
    text = _TRAILING_DOT_RE.sub("", text)
    return [part.strip() for part in _FLOATING_DOT_RE.split(text) if part.strip()]


def laluna():
    """Fetch and display the lunch menu for La Luna.

    Returns a dict with the restaurant name, source URL and the menu text
    (or None if the menu could not be retrieved).
    """
    name = "La Luna"
    base_url = "http://www.lalunat1.se"

    print("\n=============")
    print(name)
    print("=============")

    # First, get the main page to find the lunch link
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching main page: {e}")
        return {"name": name, "url": base_url, "menu": None}

    soup = BeautifulSoup(response.content, "html.parser")

    # Find the lunch link in the navigation
    lunch_link = None

    # Look for links containing "Lunch" text
    for link in soup.find_all("a", href=True):
        if link.get_text(strip=True).lower() == "lunch":
            lunch_link = link["href"]
            break

    if not lunch_link:
        print("Could not find lunch page link.")
        return {"name": name, "url": base_url, "menu": None}

    # Construct full URL if it's a relative link
    if lunch_link.startswith("/"):
        lunch_url = base_url + lunch_link
    elif lunch_link.startswith("http"):
        lunch_url = lunch_link
    else:
        lunch_url = base_url + "/" + lunch_link

    # Now get the lunch page
    try:
        response = requests.get(lunch_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching lunch page: {e}")
        return {"name": name, "url": lunch_url, "menu": None}

    soup = BeautifulSoup(response.content, "html.parser")

    # First, handle double <br> tags as dish separators
    # Convert <br><br> patterns to dish separators, but only if followed by a capital letter
    html_content = str(soup)
    html_content = re.sub(r"<br[^>]*>\s*<br[^>]*>\s*([A-ZÅÄÖ])",
                          r"__DISH_SEPARATOR__\1", html_content, flags=re.IGNORECASE)
    soup = BeautifulSoup(html_content, "html.parser")

    # Replace remaining single <br> tags with spaces
    for br in soup.find_all(["br", "br/"]):
        br.replace_with(" ")

    # Also handle self-closing br tags and other potential line break elements
    for element in soup.find_all():
        if element.name in ["br", "hr"] or (element.name and element.name.lower() == "br"):
            element.replace_with(" ")

    # Replace dish separator spans with a special marker
    # Look for spans with class "wysiwyg-font-size-24" that contain a <b> tag
    for span in soup.find_all("span", class_="wysiwyg-font-size-24"):
        if span.find("b"):  # Only if it contains a <b> tag
            # Check if the span text starts with a capital letter
            span_text = span.get_text(strip=True)
            if span_text and span_text[0].isupper():
                span.insert_before("__DISH_SEPARATOR__")
                # Keep the span content but mark it as a new dish

    # Try different selectors to find content
    selectors = [
        "div[class*='widget-content-']",
        ".widget-content",
        "div[class*='content']",
        "p", "div"
    ]

    lunch_text = ""

    for selector in selectors:
        elements = soup.select(selector)
        for element in elements:
            # Get text with separator to handle missing spaces between elements
            text = element.get_text(separator=" ", strip=True)
            if text and any(keyword in text.lower() for keyword in ["vecka", "måndag", "tisdag", "onsdag", "torsdag", "fredag", "dagens lunch", "special", "vegetarisk"]):
                if text not in lunch_text:  # Avoid duplicates
                    lunch_text += text + "\n"

        if lunch_text.strip():  # If we found content, break
            break

    if not lunch_text.strip():
        print("Could not find lunch menu content.")
        return {"name": name, "url": lunch_url, "menu": None}

    # Clean up string
    replacements = {
        u"\u00A0": " ",  # non-breaking space
        u"\u200B": " ",  # zero width space
    }

    for pattern, repl in replacements.items():
        lunch_text = lunch_text.replace(pattern, repl)

    # Drop the "Dagens lunch, Pris ..." price/coupon preamble line entirely;
    # we only want the week number and the pizza/raggmunk availability text.
    lunch_text = re.sub(r"^Dagens lunch.*(Pris|kupong).*$\n?", "",
                        lunch_text, flags=re.IGNORECASE | re.MULTILINE)

    # First, handle the dish separators
    lunch_text = re.sub(r"__DISH_SEPARATOR__",
                        r"\n__SECOND_DISH__", lunch_text)

    # Collapse lines with misplaced line breaks, but preserve important separators
    lunch_text = re.sub(
        r"(\S)[ \t]*\n[ \t]*(?!__SECOND_DISH__|Måndag|Tisdag|Onsdag|Torsdag|Fredag|Veckans)(\S)", r"\1 \2", lunch_text)
    lunch_text = re.sub(r"[ \t]{2,}", " ", lunch_text)
    lunch_text = re.sub(r"^[ ]+", "", lunch_text, flags=re.MULTILINE)

    # Normalize headers with a single newline after each day header
    day_headers = [
        "Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag",
        "Veckans sallad", "Veckans special", "Veckans vegetariska"
    ]

    for header in day_headers:
        lunch_text = re.sub(
            fr"{header}[\s:]*", f"\n{header}\n", lunch_text, flags=re.IGNORECASE)

    # Add new line after week number
    lunch_text = re.sub(r"(Vecka \d+)", r"\1\n",
                        lunch_text, flags=re.IGNORECASE)

    # Add newlines after "Dagens lunch"
    lunch_text = re.sub(r"(Dagens lunch)", r"\1\n",
                        lunch_text, flags=re.IGNORECASE)

    # Clean up extra line breaks that might have been introduced
    lunch_text = re.sub(r"\n\s*\n\s*__SECOND_DISH__",
                        r"\n__SECOND_DISH__", lunch_text)

    # Split additional info at the end and remove "Luncha med oss!"
    lunch_text = re.sub(r"(vegetarisk|sallad)(.*?)(Luncha med oss!)",
                        r"\1\2", lunch_text, flags=re.IGNORECASE)
    lunch_text = re.sub(r"(ris) (Luncha med oss!)", r"\1",
                        lunch_text, flags=re.IGNORECASE)
    lunch_text = re.sub(r"(Luncha med oss!)(.*?)(Alla ordinarie)",
                        r"\n\3", lunch_text, flags=re.IGNORECASE)
    lunch_text = re.sub(r"(lunchmenyn)(.*?)(Vi serverar)",
                        r"\1\n\3", lunch_text, flags=re.IGNORECASE)

    # Add line break before "Alla ordinarie pizzor" if it doesn't already have
    # one. Skip when directly preceded by "_" so we don't split a
    # "__SECOND_DISH__Alla ordinarie..." marker away from its own text.
    lunch_text = re.sub(r"([^\n_])(Alla ordinarie)",
                        r"\1\n\2", lunch_text, flags=re.IGNORECASE)

    # Insert a tab character before each non-day header line
    lunch_text = "".join(
        [s for s in lunch_text.splitlines(True) if s.strip("\r\n")])

    # Split into lines and process each line for consistent indentation
    lines = lunch_text.split('\n')
    processed_lines = []

    for line in lines:
        line = line.strip()
        if line:
            # Skip the "Luncha med oss!" line
            if line == "Luncha med oss!":
                continue
            # Check if this is a header line (should not be indented)
            elif re.match(r'^(Måndag|Tisdag|Onsdag|Torsdag|Fredag|Veckans sallad|Veckans special|Veckans vegetariska|(MENY\s+)?Vecka \d+|Dagens lunch)$', line, re.IGNORECASE):
                processed_lines.append(line)
            elif line.startswith('__SECOND_DISH__'):
                # Handle second dish marker - replace with tab and add any remaining text
                remaining_text = line.replace('__SECOND_DISH__', '').strip()
                if remaining_text:
                    for part in _split_floating_dish(remaining_text):
                        processed_lines.append(f'\t{part}')
            else:
                # This should be indented content
                content = line[1:] if line.startswith('\t') else line
                for part in _split_floating_dish(content):
                    processed_lines.append(f'\t{part}')

    lunch_text = '\n'.join(processed_lines)

    lunch_text = strip_trailing_empty_lines(lunch_text)
    print(lunch_text)
    return {"name": name, "url": lunch_url, "menu": lunch_text}


if __name__ == "__main__":
    laluna()
