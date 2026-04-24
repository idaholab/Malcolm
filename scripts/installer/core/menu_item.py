#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Menu item class for Malcolm installer UI grouping.

This module provides the MenuItem class that serves as a UI grouping mechanism
for configuration items. Unlike ConfigItem, MenuItems do not write configuration
and are used solely for organizing and controlling visibility of related items.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MenuItem:
    """
    Base class for menu items used for UI grouping and visibility control.

    This class represents a menu group that organizes related configuration items.
    Unlike ConfigItem, MenuItems do not store values or write to configuration files.

    Attributes:
        key: Unique identifier for the menu item (should always be a KEY_MENU_ITEM_... constant)
        label: Human-readable display name for the menu group
        sort_priority: Optional integer for sorting order (lower values appear first)
        ui_parent: Optional parent menu item key for hierarchical grouping
        is_visible: Whether the menu item should be visible in the UI
    """

    key: str
    label: str
    sort_priority: Optional[int] = None
    ui_parent: Optional[str] = None
    is_visible: bool = True
    is_expanded: bool = False  # Whether this menu item is expanded to show children

    def set_visible(self, visible: bool):
        """Set the visibility of the menu item.

        Args:
            visible: The new visibility state
        """
        self.is_visible = visible

    def set_expanded(self, expanded: bool):
        """Set the expanded state of the menu item.

        Args:
            expanded: Whether the menu item is expanded to show its children
        """
        self.is_expanded = expanded

    def toggle_expanded(self):
        """Toggle the expanded state of the menu item."""
        self.is_expanded = not self.is_expanded

