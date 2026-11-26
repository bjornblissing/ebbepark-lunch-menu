#!/usr/bin/env python3

import os
import warnings

# Suppress EasyOCR GPU warnings
os.environ['EASYOCR_VERBOSE'] = '0'
warnings.filterwarnings("ignore", category=UserWarning, module="torch")


def strip_trailing_empty_lines(s: str) -> str:
    """Remove trailing empty lines from a string."""
    lines = s.splitlines()
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines)
