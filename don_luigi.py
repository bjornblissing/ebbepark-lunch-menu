#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
from PIL import Image
import easyocr
import io
import sys
from io import StringIO
from utils import strip_trailing_empty_lines


def don_luigi():
    """Fetch and display the lunch menu for Don Luigi.

    Returns a dict with the restaurant name, source URL and the menu text
    (or None if the menu could not be retrieved).
    """
    name = "Don Luigi"
    url = "https://www.donluigi.se/lunchmeny/"

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

    # Find the entry-content div
    entry_content = soup.find("div", class_="entry-content")
    if not entry_content:
        print("Could not find entry-content div.")
        return {"name": name, "url": url, "menu": None}

    # Find the image within the entry-content div
    img_tag = entry_content.find("img")
    if not img_tag:
        print("Could not find image in entry-content div.")
        return {"name": name, "url": url, "menu": None}

    img_src = img_tag.get("src")
    if not img_src:
        print("Could not find image source.")
        return {"name": name, "url": url, "menu": None}

    # Make sure we have the full URL
    if img_src.startswith("//"):
        img_src = "https:" + img_src
    elif img_src.startswith("/"):
        img_src = "https://www.donluigi.se" + img_src

    try:
        # Download the image
        img_response = requests.get(img_src)
        img_response.raise_for_status()

        # Open the image with PIL
        image = Image.open(io.BytesIO(img_response.content))

        # Use EasyOCR to extract text from the image
        # Initialize EasyOCR reader with Swedish and English languages
        # Suppress the GPU warning by redirecting stdout temporarily
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            # Swedish and English
            reader = easyocr.Reader(['sv', 'en'], verbose=False)
        finally:
            sys.stdout = old_stdout

        # Extract text from the image
        results = reader.readtext(img_response.content)

        # Combine all detected text
        text_parts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.5:  # Only include text with reasonable confidence
                text_parts.append(text)

        text = ' '.join(text_parts)

        if not text.strip():
            print("Could not extract text from the menu image.")
            return {"name": name, "url": url, "menu": None}

        # Clean up the extracted text
        # Replace multiple spaces with single spaces and clean up
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove everything from "Det går bra att beställa" onwards. OCR
        # sometimes misreads the leading bullet (e.g. "*" as "#") and the
        # word "att" (e.g. as "alt"), so match loosely on the stable part
        # of the sentence.
        match = re.search(r'[#*]?\s*Det går bra', text)
        if match:
            text = text[:match.start()].strip()
            text += "\nDet går bra att beställa från hela menyn."

        # Fix common OCR artifacts
        # OCR sometimes reads commas as underscores or semicolons
        text = text.replace('_', ', ')
        text = text.replace(';', ',')
        # OCR often garbles "Falafel" (e.g. "Falaíel")
        text = re.sub(r'\bFala\S*el\b', 'Falafel', text)

        # Try to identify and format different sections
        formatted_text = text

        # Remove prices (3 or more digits)
        formatted_text = re.sub(r'\b\d{3,}\b', '', formatted_text)

        # The "Sallad" section header is followed by its protein options
        # (Kyckling/Räkor/Falafel) before the actual dish description
        # ("Ceasarsallad..."). Keep the options on the header line,
        # joined with " - ".
        formatted_text = re.sub(
            r'Sallad\s+Kyckling\s+Räkor\s+Falafel\s+',
            'Sallad - Kyckling Räkor Falafel\n\t', formatted_text)

        # Add line breaks before key sections
        formatted_text = re.sub(
            r'(LUNCHMENY|Veckans|Pasta|Sallad|Husman)', r'\n\1', formatted_text)
        formatted_text = re.sub(r'(MAN - FRE|MÅN FRE)',
                                r'\n\1', formatted_text)

        # Add line breaks after specific headers and indent the following content
        formatted_text = re.sub(
            r'(Veckans Pinsa)\s+([A-ZÅÄÖ])', r'\1\n\t\2', formatted_text)
        formatted_text = re.sub(
            r'(Pasta)\s+(Pasta|[A-ZÅÄÖ])', r'\1\n\t\2', formatted_text)
        formatted_text = re.sub(
            r'(Sallad)\s+([A-ZÅÄÖ])', r'\1\n\t\2', formatted_text)
        formatted_text = re.sub(
            r'(Husman)\s+([A-ZÅÄÖ])', r'\1\n\t\2', formatted_text)

        # Clean up multiple newlines
        formatted_text = re.sub(r'\n\s*\n', '\n', formatted_text)

        # Split into lines for further processing
        lines = formatted_text.split('\n')
        final_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # Check if this is a main section header (should not be indented)
                if any(keyword in line.upper() for keyword in ['LUNCHMENY', 'MAN - FRE', 'MÅN FRE']):
                    # This is a main section header
                    # Add spacing before headers (except first)
                    if final_lines:
                        final_lines.append("")
                    final_lines.append(line)
                # Check if this is a menu item header (should not be indented)
                elif line in ['Veckans Pinsa', 'Pasta', 'Sallad', 'Husman',
                              'Det går bra att beställa från hela menyn.'] or \
                        line.startswith('Sallad - '):
                    # Add spacing before headers (except first)
                    if final_lines:
                        final_lines.append("")
                    final_lines.append(line)
                else:
                    # Regular text, indent if not already indented
                    if not line.startswith('\t'):
                        final_lines.append(f"\t{line}")
                    else:
                        final_lines.append(line)

        final_text = '\n'.join(final_lines)

        if final_text.strip():
            print(final_text)
            return {"name": name, "url": url, "menu": final_text}
        else:
            print("No readable menu content found in the image.")
            return {"name": name, "url": url, "menu": None}

    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return {"name": name, "url": url, "menu": None}
    except Exception as e:
        print(f"Error processing image: {e}")
        return {"name": name, "url": url, "menu": None}


if __name__ == "__main__":
    don_luigi()
