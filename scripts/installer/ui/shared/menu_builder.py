#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.

"""Menu building utilities for TUI installer interface."""

from typing import List, Any

from scripts.installer.utils.summary_utils import format_scalar, normalize_display_string


class MenuBuilder:
    """Utility class for building consistent menu displays across TUI interfaces."""

    def __init__(self):
        """Initialize the menu builder."""
        self.menu_lines: List[str] = []

    def clear(self) -> None:
        """Clear the current menu content."""
        self.menu_lines.clear()

    def add_header(self, title: str, separator: str = "---") -> None:
        """Add a header section to the menu.

        Args:
            title: The header title
            separator: The separator characters to use
        """
        self.menu_lines.append(f"{separator} {title} {separator}")

    def add_description(self, description: str) -> None:
        """Add a description line to the menu.

        Args:
            description: The description text
        """
        self.menu_lines.append(description)

    def add_blank_line(self) -> None:
        """Add a blank line to the menu."""
        self.menu_lines.append("")

    def add_tree_item(
        self,
        prefix: str,
        number: int,
        label: str,
        current_value: Any,
        question: str = None,
        show_value: bool = True,
    ) -> None:
        """Add a tree-style menu item with prefix formatting.

        Args:
            prefix: The tree prefix (e.g., "├── ", "└── ")
            number: The item number
            label: The item label
            current_value: The current value to display (ignored if show_value is False)
            question: Question text to display below the item
            show_value: Whether to display the current value (False for MenuItems, True for ConfigItems)
        """
        if show_value:
            # ConfigItem - always show value, even if empty
            value_display = self._format_value_display(current_value)
            self.menu_lines.append(f"{prefix}{number}. {label} (current: {value_display})")
        else:
            # MenuItem - no value display
            self.menu_lines.append(f"{prefix}{number}. {label}")

        if question:
            # Adjust help text indentation based on prefix
            indent = " " * (len(prefix) + 2)
            self.menu_lines.append(f"{indent}{question}")

    def add_action_section(self, title: str = "Actions") -> None:
        """Add an actions section header.

        Args:
            title: The actions section title
        """
        self.menu_lines.append("")
        self.menu_lines.append(f"--- {title} ---")

    def add_action(self, key: str, description: str) -> None:
        """Add an action item to the menu.

        Args:
            key: The action key/letter
            description: The action description
        """
        self.menu_lines.append(f"  {key}. {description}")

    def add_separator(self, separator: str = "-", length: int = 33) -> None:
        """Add a separator line.

        Args:
            separator: The separator character
            length: The length of the separator line
        """
        self.menu_lines.append(separator * length)

    def build(self) -> str:
        """Build the complete menu as a single string.

        Returns:
            The complete menu as a multi-line string
        """
        return "\n".join(self.menu_lines)

    def display(self) -> None:
        """Display the menu using print."""
        print(self.build())

    def _format_value_display(self, value: Any) -> str:
        """Format a value for display in the menu."""
        return format_scalar(value, empty_label="empty")


class ValueFormatter:
    """Utility class for formatting values in menu displays."""

    normalize_display_string = staticmethod(normalize_display_string)

    @staticmethod
    def format_config_value(label: str, value: Any) -> str:
        """Format a configuration value for display, masking password/API-key fields."""
        if value and (("password" in label.lower()) or ("api key" in label.lower())):
            return "********"
        return format_scalar(value, empty_label="empty")
