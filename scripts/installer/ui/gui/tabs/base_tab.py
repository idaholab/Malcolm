#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
import customtkinter

from scripts.installer.configs.constants.enums import (
    FileExtractionMode,
    NetboxMode,
    OpenPortsChoices,
    SearchEngineMode,
)
from scripts.installer.ui.gui.components.styles import (
    PANEL_BORDER_WIDTH,
    PANEL_COLORS,
    PANEL_CORNER_RADIUS,
    SECTION_COLORS,
    TAB_BG_FALLBACK,
)

from scripts.installer.ui.gui.widgets.config_item_widget import create_config_item_widget
from scripts.installer.ui.gui.components.collapsible_container import CollapsibleContainer

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig


# ENUM values that indicate children should be collapsed (feature disabled/minimal config)
COLLAPSE_ENUM_VALUES = {
    # Open Ports: NO/YES are presets, CUSTOMIZE shows children
    OpenPortsChoices.NO.value,
    OpenPortsChoices.YES.value,
    # NetBox: DISABLED means children not needed
    NetboxMode.DISABLED.value,
    # File Extraction: NONE means no children needed
    FileExtractionMode.NONE.value,
    # OpenSearch: LOCAL means no remote URL needed
    SearchEngineMode.OPENSEARCH_LOCAL.value,
}


class BaseTab:
    """Base class for configuration tabs with dynamic MenuItem rendering.

    This class reads MenuItems and ConfigItems dynamically from MalcolmConfig
    to render tab contents. Items with children are rendered in collapsible containers.
    """

    def __init__(
        self,
        parent_frame: customtkinter.CTkFrame,
        malcolm_config: "MalcolmConfig",
        menu_item_key: str,
        accent_colors: Optional[Dict[str, str]] = None,
    ):
        self.parent_frame = parent_frame
        self.malcolm_config = malcolm_config
        self.menu_item_key = menu_item_key
        self.accent_colors = accent_colors
        self.widget_map: Dict[str, customtkinter.CTkBaseClass] = {}
        self.panel_map: Dict[str, customtkinter.CTkFrame] = {}
        self.depth_map: Dict[str, int] = {}
        self.pack_targets: Dict[str, customtkinter.CTkBaseClass] = {}
        self.pack_options: Dict[str, dict] = {}
        self.rendered_items: set = set()  # Track which config keys are rendered in this tab

        # Collapsible container state tracking
        self._collapse_state: Dict[str, bool] = {}  # True = collapsed
        self._containers: Dict[str, CollapsibleContainer] = {}
        self._children_map: Dict[str, List[str]] = {}  # parent_key -> [child_keys]
        self._items_with_children: Set[str] = set()

        self._build_ui()

    @property
    def widgets(self) -> Dict[str, customtkinter.CTkBaseClass]:
        """Alias for widget_map for consistency with validation code."""
        return self.widget_map

    def _build_ui(self):
        """Build the tab UI with collapsible containers for items with children.

        Uses tree-walking logic to ensure items appear in the correct priority-based
        order. Items with children are wrapped in collapsible containers.
        """
        self._tab_bg = self._tab_bg_color()
        scrollable_frame = customtkinter.CTkScrollableFrame(
            self.parent_frame,
            fg_color=self._tab_bg,
            bg_color=self._tab_bg,
        )
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._bind_mousewheel(scrollable_frame)

        # Get all items with depth and children info
        items, children_map = self._get_tab_items_with_children()
        self._children_map = children_map

        # Identify which items have children (for collapsible containers)
        self._items_with_children = set(children_map.keys())

        # Build item lookup for rendering
        item_by_key = {}
        for key, item in self.malcolm_config.get_all_config_items().items():
            item_by_key[key] = item

        # Track which items we've rendered (to avoid duplicates)
        rendered_keys: Set[str] = set()

        def render_item(key: str, item: Any, depth: int, parent_frame: customtkinter.CTkFrame):
            """Render a single item, recursively rendering children if it has any."""
            if key in rendered_keys:
                return
            rendered_keys.add(key)

            has_children = key in self._items_with_children
            child_keys = children_map.get(key, [])

            if has_children:
                # Create collapsible container for items with children
                initial_collapsed = self._compute_initial_collapse_state(key)
                container_bg = self._resolve_parent_bg_color(parent_frame, self._tab_bg)
                container = CollapsibleContainer(
                    parent=parent_frame,
                    depth=depth,
                    on_toggle=self._on_collapse_toggle,
                    key=key,
                    collapsed=initial_collapsed,
                    tab_bg=container_bg,
                )
                container.pack(fill="x", padx=6, pady=4)
                self._containers[key] = container
                self._collapse_state[key] = initial_collapsed

                # Create widget in container's header
                header_frame = container.get_header_frame()
                widget_container = self._create_config_widget(header_frame, key, item)
                if widget_container:
                    widget_container.pack(fill="x", expand=True)
                    self.widget_map[key] = widget_container
                    self.depth_map[key] = depth
                    self.rendered_items.add(key)
                    self.pack_targets[key] = container.outer_frame
                    self.pack_options[key] = container.pack_info()

                    # Setup visibility and observers
                    self._setup_item_visibility(key, widget_container)

                    # Setup observer for auto-collapse/expand
                    self.malcolm_config.observe(
                        key,
                        lambda _value, k=key: self._on_parent_value_changed(k)
                    )

                # Render children inside the container's content frame
                content_frame = container.get_content_frame()
                for child_key in child_keys:
                    child_item = item_by_key.get(child_key)
                    if child_item:
                        render_item(child_key, child_item, depth + 1, content_frame)
            else:
                # Simple item without children - render in a panel
                if depth > 0:
                    panel_bg = self._panel_bg_color(depth, enabled=True)
                    panel_parent_bg = self._resolve_parent_bg_color(parent_frame, self._tab_bg)
                    panel = customtkinter.CTkFrame(
                        parent_frame,
                        fg_color=panel_bg,
                        bg_color=panel_parent_bg,
                        corner_radius=PANEL_CORNER_RADIUS,
                        border_width=PANEL_BORDER_WIDTH,
                        border_color=self._panel_border_color(depth, enabled=True),
                    )
                    panel.pack(fill="x", padx=6, pady=3)
                    self.pack_targets[key] = panel
                    self.pack_options[key] = panel.pack_info()
                    widget_container = self._create_config_widget(panel, key, item)
                    if not widget_container:
                        panel.destroy()
                        return
                    widget_container.pack(fill="x", padx=10, pady=6)
                    self.panel_map[key] = panel
                else:
                    widget_container = self._create_config_widget(parent_frame, key, item)
                    if widget_container:
                        widget_container.pack(fill="x", padx=6, pady=4)
                        self.pack_targets[key] = widget_container
                        self.pack_options[key] = widget_container.pack_info()
                    else:
                        return

                if widget_container:
                    self.widget_map[key] = widget_container
                    self.depth_map[key] = depth
                    self.rendered_items.add(key)
                    self._setup_item_visibility(key, widget_container)

        # Render top-level items
        for key, item, depth in items:
            if depth == 0:
                render_item(key, item, depth, scrollable_frame)

    def _setup_item_visibility(self, key: str, widget_container: customtkinter.CTkFrame):
        """Setup visibility state and observers for an item."""
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

    def _compute_initial_collapse_state(self, key: str) -> bool:
        """Compute collapse state based on parent value.

        Returns True if should be collapsed, False if expanded.

        For boolean values: collapse when False (feature disabled)
        For ENUM/string values: collapse when value is in COLLAPSE_ENUM_VALUES
        """
        value = self.malcolm_config.get_value(key)

        # Boolean: collapse when False (feature disabled)
        if isinstance(value, bool):
            return not value

        # String (ENUM value): check against known collapse values
        if isinstance(value, str):
            return value in COLLAPSE_ENUM_VALUES

        # Default: expanded
        return False

    def _on_collapse_toggle(self, key: str, collapsed: bool):
        """Handle user clicking a collapse toggle."""
        self._collapse_state[key] = collapsed

    def _on_parent_value_changed(self, key: str):
        """Handle parent value change for auto-collapse/expand."""
        if key not in self._containers:
            return

        new_collapsed = self._compute_initial_collapse_state(key)
        if self._collapse_state.get(key) != new_collapsed:
            self._collapse_state[key] = new_collapsed
            self._containers[key].set_collapsed(new_collapsed)

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

    def _get_tab_items_with_children(self) -> Tuple[List[Tuple[str, object, int]], Dict[str, List[str]]]:
        """Get all ConfigItems with depth info and a map of which items have children.

        Returns:
            Tuple of (items_list, children_map) where:
            - items_list: List of (key, item, depth) tuples in display order
            - children_map: Dict mapping parent_key -> [child_keys] for ConfigItems only
        """
        from scripts.installer.core.menu_item import MenuItem

        # Build item lookup including both ConfigItems and MenuItems
        item_by_key = {}
        config_item_keys = set()

        # Add all ConfigItems
        for key, item in self.malcolm_config.get_all_config_items().items():
            item_by_key[key] = item
            config_item_keys.add(key)

        # Add all MenuItems
        for key, item in self.malcolm_config.get_all_menu_items().items():
            item_by_key[key] = item

        # Build parent → children map (all items)
        all_children = {}
        for key, item in item_by_key.items():
            parent = item.ui_parent
            if parent and parent in item_by_key:
                all_children.setdefault(parent, []).append(key)

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

        # Build ConfigItem-only children map (for collapsible containers)
        # This maps ConfigItem parents to their ConfigItem children
        config_children_map: Dict[str, List[str]] = {}

        def get_config_children(parent_key: str) -> List[str]:
            """Get ConfigItem children of a key, skipping MenuItems."""
            result = []
            for child_key in all_children.get(parent_key, []):
                if child_key in config_item_keys:
                    result.append(child_key)
                else:
                    # If child is a MenuItem, get its ConfigItem children
                    result.extend(get_config_children(child_key))
            return _sorted_keys(result)

        # Build children map for ConfigItems
        for key in config_item_keys:
            children = get_config_children(key)
            if children:
                config_children_map[key] = children

        # Collect items via recursive tree walk
        result = []

        def walk(key: str, depth: int) -> None:
            """Recursively walk tree and collect items with depth."""
            item = item_by_key.get(key)
            if not item:
                return

            is_menu_item = isinstance(item, MenuItem)

            if not is_menu_item:
                result.append((key, item, depth))

            # Recursively walk children in priority order
            child_depth = depth if is_menu_item else depth + 1

            child_keys = all_children.get(key, [])
            sorted_children = _sorted_keys(child_keys)
            for child_key in sorted_children:
                walk(child_key, child_depth)

        # Start from this tab's root
        root_item = item_by_key.get(self.menu_item_key)
        if root_item:
            if isinstance(root_item, MenuItem):
                child_keys = all_children.get(self.menu_item_key, [])
                sorted_children = _sorted_keys(child_keys)
                for child_key in sorted_children:
                    walk(child_key, 0)
            else:
                walk(self.menu_item_key, 0)

        return result, config_children_map

    def _create_config_widget(
        self,
        parent: customtkinter.CTkFrame,
        key: str,
        item: object
    ) -> Optional[customtkinter.CTkFrame]:
        """Create widget for a ConfigItem using the factory."""
        return create_config_item_widget(
            parent, key, item, self.malcolm_config, accent_colors=self.accent_colors
        )

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
        level = "nested" if is_nested else "flat"
        state = "enabled" if enabled else "disabled"
        return PANEL_COLORS[level][state]["bg"]

    def _panel_border_color(self, depth: int, enabled: bool) -> tuple:
        """Get panel border color for depth and enabled state."""
        is_nested = depth > 1
        level = "nested" if is_nested else "flat"
        state = "enabled" if enabled else "disabled"
        return PANEL_COLORS[level][state]["border"]

    def _section_bg_color(self, index: int) -> tuple:
        """Get alternating section background color."""
        return SECTION_COLORS["even"]["bg"] if index % 2 == 0 else SECTION_COLORS["odd"]["bg"]

    def _section_border_color(self, index: int) -> tuple:
        """Get alternating section border color."""
        return SECTION_COLORS["even"]["border"] if index % 2 == 0 else SECTION_COLORS["odd"]["border"]

    def _tab_bg_color(self) -> tuple:
        """Resolve the tab background color for blending rounded corners."""
        parent_color = None
        try:
            parent_color = self.parent_frame.cget("fg_color")
        except Exception:
            parent_color = None

        if isinstance(parent_color, (list, tuple)):
            return tuple(parent_color)

        if parent_color and parent_color != "transparent":
            stored_color = getattr(self.parent_frame, "_fg_color", None)
            if isinstance(stored_color, (list, tuple)):
                return tuple(stored_color)

        try:
            theme_color = customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"]
        except Exception:
            theme_color = TAB_BG_FALLBACK

        if isinstance(theme_color, list):
            theme_color = tuple(theme_color)

        return theme_color

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
        panel_parent_bg = self._resolve_parent_bg_color(panel.master, self._tab_bg)
        panel.configure(
            fg_color=self._panel_bg_color(depth, enabled=is_visible),
            bg_color=panel_parent_bg,
            border_color=self._panel_border_color(depth, enabled=is_visible),
        )

    def _resolve_parent_bg_color(self, frame: customtkinter.CTkFrame, fallback: tuple) -> tuple:
        """Resolve a frame background color to use for child corner blending."""
        for attr in ("fg_color", "bg_color"):
            try:
                value = frame.cget(attr)
            except Exception:
                value = None
            if isinstance(value, list):
                value = tuple(value)
            if value and value != "transparent":
                return value

        stored_color = getattr(frame, "_fg_color", None)
        if isinstance(stored_color, list):
            stored_color = tuple(stored_color)
        if stored_color and stored_color != "transparent":
            return stored_color

        return fallback
