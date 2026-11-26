# Lunch Menu Scraper

A Python web scraper that fetches and displays lunch menus from multiple restaurants in a clean, formatted output.

## Supported Restaurants

- **Laszlos Krog** - Fetches weekly menu from their website
- **La Luna** - Scrapes daily lunch menu with Swedish dishes and pizzas
- **Don Luigi** - Uses OCR to extract menu from images on their website

## Features

- **Multi-restaurant support** - Get menus from all restaurants at once
- **Modular design** - Each restaurant has its own module
- **OCR capability** - Extracts text from menu images using EasyOCR
- **Current week detection** - Automatically finds the current week's menu
- **Clean formatting** - Well-structured, readable output
- **Individual execution** - Run each restaurant scraper independently
- **Website generation** - Renders all menus as a static HTML page

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Get All Restaurant Menus

```bash
python main.py
```

### Get Individual Restaurant Menus

```bash
# Laszlos Krog only
python laszlos_krog.py

# La Luna only
python la_luna.py

# Don Luigi only
python don_luigi.py
```

### Generate the Website

Render all restaurant menus as a static `index.html` page:

```bash
python generate_website.py
```

## Dependencies

- **requests** - HTTP requests for fetching web pages
- **beautifulsoup4** - HTML parsing and content extraction
- **Pillow** - Image processing for OCR functionality
- **easyocr** - Optical Character Recognition for menu images

## How It Works

### Laszlos Krog
- Fetches the restaurant's webpage
- Finds the current week's menu section
- Extracts and formats daily menu items

### La Luna
- Navigates to the lunch page
- Parses HTML content with complex text processing
- Formats Swedish menu items with proper indentation

### Don Luigi
- Downloads menu images from the website
- Uses EasyOCR to extract text from images
- Processes and formats the extracted menu text
- Supports Swedish and English text recognition

## Output Format

Each restaurant's menu is displayed with:
- Clear restaurant headers
- Proper indentation for menu items
- Daily organization (where applicable)
- Clean, readable formatting

## Error Handling

- Network request failures are handled gracefully
- Missing menu content is reported clearly
- OCR processing errors are caught and reported
- Warning messages from dependencies are suppressed

## Contributing

Feel free to add support for additional restaurants by:
1. Creating a new module following the existing pattern
2. Adding the restaurant function to `main.py`
3. Updating this README with the new restaurant information

## License

This project is for educational and personal use. Please respect the terms of service of the restaurant websites being scraped.
