#!/usr/bin/env python3

"""
Main entry point for the lunch menu scraper.
This script fetches and displays lunch menus from multiple restaurants.
"""

from laszlos_krog import laszlos_krog
from la_luna import laluna
from don_luigi import don_luigi


def main():
    """Fetch and display lunch menus from all restaurants."""
    laszlos_krog()
    laluna()
    don_luigi()


if __name__ == "__main__":
    main()
