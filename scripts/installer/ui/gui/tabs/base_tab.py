#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import customtkinter

from scripts.installer.ui.gui.widgets.config_item_widget import create_config_item_widget

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig


class BaseTab:
    """Base class for configuration tabs with dynamic MenuItem rendering.

    This class reads MenuItems and ConfigItems dynamically from MalcolmConfig
    to render tab contents. Nested MenuItems are rendered as bordered sections.
    """

    def __init__(
        self,
        parent_frame: customtkinter.CTkFrame,
        malcolm_config: "MalcolmConfig",
        menu_item_key: str,
    ):
        self.parent_frame = parent_frame
        self.malcolm_config = malcolm_config
        self.menu_item_key = menu_item_key
        self.widget_map: Dict[str, customtkinter.CTkBaseClass] = {}
        self.section_frames: Dict[str, customtkinter.CTkFrame] = {}

        self._build_ui()

    def _build_ui(self):
        """Build the tab UI by grouping items by nested MenuItems."""
        scrollable_frame = customtkinter.CTkScrollableFrame(
            self.parent_frame,
            fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        items = self._get_tab_items()
        sections = self._group_by_menu_items(items)

        for section_key, section_items in sections:
            section_frame = self._create_section(scrollable_frame, section_key)

            for key, item in section_items:
                widget_container = self._create_config_widget(section_frame, key, item)
                if widget_container:
                    self.widget_map[key] = widget_container

                    if self.malcolm_config.is_item_visible(key):
                        widget_container.pack(fill="x", padx=10, pady=5)

                    self.malcolm_config.observe(
                        key,
                        lambda _value, k=key: self._update_widget_visibility(k)
                    )

    def _get_tab_items(self) -> List[Tuple[str, object]]:
        """Get all ConfigItems that belong to this tab.

        Returns items whose ui_parent is either this MenuItem or any nested MenuItem
        under this MenuItem.
        """
        items = []
        menu_item_keys = {self.menu_item_key}
        menu_item = self.malcolm_config.get_menu_item(self.menu_item_key)

        if not menu_item:
            config_item = self.malcolm_config.get_item(self.menu_item_key)
            if config_item:
                items.append((self.menu_item_key, config_item))

        for key, menu_item in self.malcolm_config.get_visible_menu_items().items():
            if menu_item.ui_parent == self.menu_item_key:
                menu_item_keys.add(key)

        for key, item in self.malcolm_config.get_all_config_items().items():
            if item.ui_parent in menu_item_keys:
                items.append((key, item))

        items.sort(key=lambda x: (
            x[1].sort_priority if x[1].sort_priority is not None else 999999,
            x[1].label.lower()
        ))

        return items

    def _group_by_menu_items(self, items: List[Tuple[str, object]]) -> List[Tuple[Optional[str], List[Tuple[str, object]]]]:
        """Group ConfigItems by their nested MenuItem parent.

        Returns list of (menu_item_key, items) tuples in sorted order.
        """
        groups: Dict[Optional[str], List[Tuple[str, object]]] = {}

        for key, item in items:
            parent = item.ui_parent

            if parent is None and key == self.menu_item_key:
                parent = self.menu_item_key

            if parent not in groups:
                groups[parent] = []
            groups[parent].append((key, item))

        sorted_groups = []

        if self.menu_item_key in groups:
            sorted_groups.append((self.menu_item_key, groups[self.menu_item_key]))

        nested_menus = []
        for key, menu_item in self.malcolm_config.get_visible_menu_items().items():
            if menu_item.ui_parent == self.menu_item_key and key in groups:
                nested_menus.append((
                    menu_item.sort_priority if menu_item.sort_priority is not None else 999999,
                    menu_item.label.lower(),
                    key,
                    groups[key]
                ))

        nested_menus.sort()
        for _, _, key, group_items in nested_menus:
            sorted_groups.append((key, group_items))

        return sorted_groups

    def _create_section(
        self,
        parent: customtkinter.CTkFrame,
        section_key: Optional[str]
    ) -> customtkinter.CTkFrame:
        """Create a bordered section for a nested MenuItem.

        If section_key matches this tab's MenuItem, render items directly.
        Otherwise, create a bordered frame with header.
        """
        if section_key == self.menu_item_key:
            section_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
            section_frame.pack(fill="x", padx=5, pady=5)
            self.section_frames[section_key] = section_frame
            return section_frame

        menu_item = self.malcolm_config.get_menu_item(section_key)
        if not menu_item:
            section_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
            section_frame.pack(fill="x", padx=5, pady=5)
            self.section_frames[section_key] = section_frame
            return section_frame

        border_frame = customtkinter.CTkFrame(
            parent,
            corner_radius=8,
            border_width=2,
            border_color=("gray70", "gray30")
        )
        border_frame.pack(fill="x", padx=5, pady=10)

        header = customtkinter.CTkLabel(
            border_frame,
            text=menu_item.label,
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=15, pady=(10, 5))

        section_frame = customtkinter.CTkFrame(border_frame, fg_color="transparent")
        section_frame.pack(fill="x", padx=5, pady=(0, 10))

        self.section_frames[section_key] = border_frame
        return section_frame

    def _create_config_widget(
        self,
        parent: customtkinter.CTkFrame,
        key: str,
        item: object
    ) -> Optional[customtkinter.CTkFrame]:
        """Create widget for a ConfigItem using the factory."""
        return create_config_item_widget(parent, key, item, self.malcolm_config)

    def _update_widget_visibility(self, key: str):
        """Update widget visibility based on MalcolmConfig state."""
        from tkinter import TclError
        from scripts.installer.utils.logger_utils import InstallerLogger

        if key not in self.widget_map:
            return

        widget = self.widget_map[key]
        is_visible = self.malcolm_config.is_item_visible(key)

        # Instead of hiding invisible items, keep them visible but disabled/grayed
        # This provides better UX - users can see all options even if some are disabled
        if is_visible:
            # Enable the widget
            try:
                widget.configure(state="normal")
            except (AttributeError, TclError):
                # Widget doesn't support state configuration (e.g., CTkLabel, CTkFrame)
                # This is expected for container widgets
                pass
        else:
            # Disable the widget and gray it out
            try:
                widget.configure(state="disabled")
            except (AttributeError, TclError):
                # Widget doesn't support state configuration
                pass

            # Also gray out the appearance for visual feedback
            try:
                # For CTkFrame containers, adjust color to indicate disabled state
                widget.configure(fg_color=("gray85", "gray25"))
            except (AttributeError, TclError):
                # Widget doesn't support fg_color (e.g., CTkEntry already grays when disabled)
                pass
