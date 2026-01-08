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
        self.panel_map: Dict[str, customtkinter.CTkFrame] = {}
        self.depth_map: Dict[str, int] = {}
        self.pack_targets: Dict[str, customtkinter.CTkBaseClass] = {}
        self.pack_options: Dict[str, dict] = {}
        self.rendered_items: set = set()  # Track which config keys are rendered in this tab

        self._build_ui()

    @property
    def widgets(self) -> Dict[str, customtkinter.CTkBaseClass]:
        """Alias for widget_map for consistency with validation code."""
        return self.widget_map

    def _build_ui(self):
        """Build the tab UI with all items in priority order, using indentation for hierarchy.

        Uses tree-walking logic from store_view_model.py to ensure items appear in the
        correct priority-based order with proper visual hierarchy through indentation.
        """
        scrollable_frame = customtkinter.CTkScrollableFrame(
            self.parent_frame,
            fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._bind_mousewheel(scrollable_frame)

        # Get all items for this tab with depth information (already sorted by priority)
        items = self._get_tab_items()

        # Render all items in tree order with depth-based indentation
        section_index = -1
        section_content = None

        for key, item, depth in items:
            # Calculate indentation based on depth in tree
            # Base padding: 10px, each level adds 20px
            left_padding = 10 + (depth * 20)

            if depth == 0:
                section_index += 1
                section_bg = self._section_bg_color(section_index)
                section_frame = customtkinter.CTkFrame(
                    scrollable_frame,
                    fg_color=section_bg,
                    bg_color=section_bg,
                    corner_radius=8,
                    border_width=1,
                    border_color=self._section_border_color(section_index),
                )
                section_frame.pack(fill="x", padx=6, pady=6)
                section_content = customtkinter.CTkFrame(section_frame, fg_color="transparent")
                section_content.pack(fill="x", padx=8, pady=6)

            parent_frame = section_content if section_content else scrollable_frame

            # Children render inside a panel with a distinct background
            if depth > 0:
                panel_bg = self._panel_bg_color(depth, enabled=True)
                panel = customtkinter.CTkFrame(
                    parent_frame,
                    fg_color=panel_bg,
                    bg_color=panel_bg,
                    corner_radius=6,
                    border_width=1,
                    border_color=self._panel_border_color(depth, enabled=True),
                )
                panel.pack(fill="x", padx=(left_padding, 10), pady=5)
                self.pack_targets[key] = panel
                self.pack_options[key] = panel.pack_info()
                widget_container = self._create_config_widget(panel, key, item)
                if not widget_container:
                    panel.destroy()
                    continue
                widget_container.pack(fill="x", padx=10, pady=6)
                self.panel_map[key] = panel
            else:
                widget_container = self._create_config_widget(parent_frame, key, item)
                if widget_container:
                    widget_container.pack(fill="x", padx=(left_padding, 10), pady=5)
                    self.pack_targets[key] = widget_container
                    self.pack_options[key] = widget_container.pack_info()
                else:
                    continue

            if widget_container:
                self.widget_map[key] = widget_container
                self.depth_map[key] = depth
                self.rendered_items.add(key)  # Track that this key is rendered in this tab

                # Set initial enabled/disabled state based on visibility
                is_visible = self.malcolm_config.is_item_visible(key)
                self._set_widget_state_recursive(
                    widget_container,
                    "normal" if is_visible else "disabled"
                )
                self._update_panel_style(key, is_visible)

                # Observe changes to update enabled/disabled state
                self.malcolm_config.observe(
                    key,
                    lambda _value, k=key: self._update_widget_visibility(k)
                )

    def _get_tab_items(self) -> List[Tuple[str, object, int]]:
        """Get all ConfigItems that belong to this tab with depth information.

        Uses tree-walking logic adapted from store_view_model.py to maintain
        proper parent-child hierarchy and sorting.

        Returns:
            List of (key, item, depth) tuples in display order
        """
        # Build item lookup including both ConfigItems and MenuItems
        item_by_key = {}

        # Add all ConfigItems
        for key, item in self.malcolm_config.get_all_config_items().items():
            item_by_key[key] = item

        # Add all MenuItems
        for key, item in self.malcolm_config.get_all_menu_items().items():
            item_by_key[key] = item

        # Build parent → children map
        children = {}
        for key, item in item_by_key.items():
            parent = item.ui_parent
            if parent and parent in item_by_key:
                children.setdefault(parent, []).append(key)

        # Helper to sort keys by priority then alphabetically
        def _sorted_keys(keys: List[str]) -> List[str]:
            def sort_key(k: str):
                item = item_by_key.get(k)
                if not item:
                    return (999999, k.lower())
                priority = getattr(item, 'sort_priority', None)
                label = (item.label or k).lower()
                return (priority if priority is not None else 999999, label)
            return sorted(keys, key=sort_key)

        # Collect items via recursive tree walk
        result = []

        def walk(key: str, depth: int) -> None:
            """Recursively walk tree and collect items with depth."""
            item = item_by_key.get(key)
            if not item:
                return

            # Only add ConfigItems to result (MenuItems are just for organization)
            from scripts.installer.core.menu_item import MenuItem
            is_menu_item = isinstance(item, MenuItem)

            if not is_menu_item:
                result.append((key, item, depth))

            # Recursively walk children in priority order
            # MenuItems don't contribute to depth since they're not rendered
            child_depth = depth if is_menu_item else depth + 1

            child_keys = children.get(key, [])
            sorted_children = _sorted_keys(child_keys)
            for child_key in sorted_children:
                walk(child_key, child_depth)

        # Start from this tab's root
        # If tab key is a ConfigItem, start with it at depth 0
        # If tab key is a MenuItem, start with its children at depth 0
        root_item = item_by_key.get(self.menu_item_key)
        if root_item:
            from scripts.installer.core.menu_item import MenuItem
            if isinstance(root_item, MenuItem):
                # Start with children of this MenuItem at depth 0
                child_keys = children.get(self.menu_item_key, [])
                sorted_children = _sorted_keys(child_keys)
                for child_key in sorted_children:
                    walk(child_key, 0)
            else:
                # Tab key is a ConfigItem, start with it
                walk(self.menu_item_key, 0)

        return result

    def _create_config_widget(
        self,
        parent: customtkinter.CTkFrame,
        key: str,
        item: object
    ) -> Optional[customtkinter.CTkFrame]:
        """Create widget for a ConfigItem using the factory."""
        return create_config_item_widget(parent, key, item, self.malcolm_config)

    def _update_widget_visibility(self, key: str):
        """Update widget enabled/disabled state based on MalcolmConfig visibility.

        Items are always shown (packed) but disabled when their visibility condition is false.
        This keeps all options visible with a clear disabled state.

        Args:
            key: The ConfigItem key
        """
        from tkinter import TclError

        if key not in self.widget_map:
            return

        container = self.widget_map[key]
        is_visible = self.malcolm_config.is_item_visible(key)

        # Get the item to check if it has dependencies
        item = self.malcolm_config.get_item(key)
        if not item:
            return

        # Enable or disable based on visibility condition
        if is_visible:
            # Enable all child widgets recursively
            self._set_widget_state_recursive(container, "normal")
        else:
            # Disable all child widgets recursively (grey them out)
            self._set_widget_state_recursive(container, "disabled")
        self._update_panel_style(key, is_visible)

        hide_when_invisible = bool(item.metadata.get("iso_only"))
        target = self.pack_targets.get(key)
        if hide_when_invisible and target:
            if is_visible:
                if not target.winfo_ismapped():
                    target.pack(**self.pack_options.get(key, {}))
            else:
                if target.winfo_ismapped():
                    target.pack_forget()

    def _set_widget_state_recursive(self, widget, state: str):
        """Recursively set state for all child widgets that support it.

        Args:
            widget: Parent widget to process
            state: State to set ("normal" or "disabled")
        """
        from tkinter import TclError

        # Try to set state on this widget
        try:
            widget.configure(state=state)
        except (AttributeError, TclError, ValueError):
            # Widget doesn't support state configuration (e.g., CTkFrame, CTkLabel)
            pass

        # Recursively process children
        try:
            for child in widget.winfo_children():
                self._set_widget_state_recursive(child, state)
        except (AttributeError, TclError):
            # Widget doesn't have children
            pass

    def _panel_bg_color(self, depth: int, enabled: bool) -> tuple:
        """Get panel background color for depth and enabled state."""
        is_nested = depth > 1
        if enabled:
            return ("gray92", "gray17") if is_nested else ("gray94", "gray18")
        return ("gray88", "gray22") if is_nested else ("gray90", "gray21")

    def _panel_border_color(self, depth: int, enabled: bool) -> tuple:
        """Get panel border color for depth and enabled state."""
        is_nested = depth > 1
        if enabled:
            return ("gray80", "gray30") if is_nested else ("gray82", "gray28")
        return ("gray75", "gray40") if is_nested else ("gray78", "gray38")

    def _section_bg_color(self, index: int) -> tuple:
        """Get alternating section background color."""
        return ("gray96", "gray14") if index % 2 == 0 else ("gray94", "gray16")

    def _section_border_color(self, index: int) -> tuple:
        """Get alternating section border color."""
        return ("gray85", "gray28") if index % 2 == 0 else ("gray83", "gray30")

    def _bind_mousewheel(self, scrollable_frame: customtkinter.CTkScrollableFrame) -> None:
        """Bind mouse wheel to the scrollable frame for cross-platform scrolling."""
        canvas = getattr(scrollable_frame, "_parent_canvas", None)
        if canvas is None:
            return

        def on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_linux_scroll(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def bind_events(_event):
            scrollable_frame.bind_all("<MouseWheel>", on_mousewheel)
            scrollable_frame.bind_all("<Button-4>", on_linux_scroll)
            scrollable_frame.bind_all("<Button-5>", on_linux_scroll)

        def unbind_events(_event):
            scrollable_frame.unbind_all("<MouseWheel>")
            scrollable_frame.unbind_all("<Button-4>")
            scrollable_frame.unbind_all("<Button-5>")

        scrollable_frame.bind("<Enter>", bind_events)
        scrollable_frame.bind("<Leave>", unbind_events)

    def _update_panel_style(self, key: str, is_visible: bool) -> None:
        """Update child panel style to reflect enabled/disabled state."""
        panel = self.panel_map.get(key)
        if not panel:
            return
        depth = self.depth_map.get(key, 1)
        panel.configure(
            fg_color=self._panel_bg_color(depth, enabled=is_visible),
            bg_color=self._panel_bg_color(depth, enabled=is_visible),
            border_color=self._panel_border_color(depth, enabled=is_visible),
        )
