"""
Constants and shared styling definitions for regression comparison modules.

This module provides centralized definitions for symbols, colors, and styling
configurations used across the regression comparison package to ensure consistency
and reduce code duplication.
"""

# File change symbols
FILE_CHANGE_SYMBOLS = {
    'unchanged': '•',
    'added': '+',
    'deleted': '-',
    'modified': '*',
    'not_present': '∅'
}

# Symbol mapping for display
SYMBOL_MAP = {
    'unchanged': FILE_CHANGE_SYMBOLS['unchanged'],
    'added': FILE_CHANGE_SYMBOLS['added'],
    'deleted': FILE_CHANGE_SYMBOLS['deleted'],
    'modified': FILE_CHANGE_SYMBOLS['modified'],
    'not_present': FILE_CHANGE_SYMBOLS['not_present']
}

# Color mapping for symbols
SYMBOL_COLORS = {
    FILE_CHANGE_SYMBOLS['unchanged']: 'blue',
    FILE_CHANGE_SYMBOLS['added']: 'green',
    FILE_CHANGE_SYMBOLS['deleted']: 'red',
    FILE_CHANGE_SYMBOLS['modified']: 'gold',
    FILE_CHANGE_SYMBOLS['not_present']: 'grey'
}

# Descriptions for legend
SYMBOL_DESCRIPTIONS = {
    FILE_CHANGE_SYMBOLS['unchanged']: 'unchanged',
    FILE_CHANGE_SYMBOLS['added']: 'added',
    FILE_CHANGE_SYMBOLS['deleted']: 'deleted',
    FILE_CHANGE_SYMBOLS['modified']: 'modified',
    FILE_CHANGE_SYMBOLS['not_present']: 'not present'
}

# ANSI color codes for terminal output
ANSI_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "gold": "\033[93m",  # Using yellow for gold
    "grey": "\033[90m",
    "reset": "\033[0m",
}

# DataFrame styling functions
def style_symbol_function(val):
    """Apply color and bold styling to symbols."""
    if val in SYMBOL_COLORS:
        return f'color: {SYMBOL_COLORS[val]}; font-weight: bold; font-size: 24px;'
    return ''

# Error messages
ERROR_MESSAGES = {
    "git_checkout_failed": "Failed to checkout commit: {commit}. Error: {error}",
    "git_diff_failed": "Failed to get diff for file {file} between commits {commit1} and {commit2}. Error: {error}",
    "file_not_found": "File not found: {file}",
    "repo_not_found": "Repository not found at {path}",
    "commit_info_failed": "Failed to get commit information for {commit}. Error: {error}"
}
