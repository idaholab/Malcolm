#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
import customtkinter

from scripts.installer.ui.gui.components.styles import (
    PANEL_BORDER_WIDTH,
    PANEL_COLORS,
    PANEL_CORNER_RADIUS,
    SECTION_COLORS,
    TAB_BG_FALLBACK,
)

from scripts.installer.ui.gui.widgets.config_item_widget import create_config_item_widget
from scripts.installer.ui.gui.components.collapsible_container import CollapsibleContainer
from scripts.installer.configs.constants.configuration_item_keys import KEY_CONFIG_ITEM_MALCOLM_PROFILE
from scripts.installer.core.profile_scope import item_allowed_for_profile

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig


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
        hide_invisible: bool = False,
    ):
        self.parent_frame = parent_frame
        self.malcolm_config = malcolm_config
        self.menu_item_key = menu_item_key
        self.accent_colors = accent_colors
        self.hide_invisible = hide_invisible
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
        self._scrollable_frame: Optional[customtkinter.CTkScrollableFrame] = None

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
        self._scrollable_frame = scrollable_frame
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
            if self._should_omit_item_for_profile(key):
                return
            if self.hide_invisible and not self.malcolm_config.is_item_visible(key):
                return

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

        # Hide iso_only items at build time when invisible
        if not is_visible:
            item = self.malcolm_config.get_item(key)
            if item and item.metadata.get("iso_only"):
                target = self.pack_targets.get(key)
                if target:
                    target.pack_forget()

        # Observe changes to update enabled/disabled state
        self.malcolm_config.observe(
            key,
            lambda _value, k=key: self._update_widget_visibility(k)
        )

    def _compute_initial_collapse_state(self, key: str) -> bool:
        """Compute collapse state based on whether children are visible.

        Returns True if should be collapsed, False if expanded.

        Uses the dependency system as the source of truth: if no children
        are visible, collapse the container.
        """
        child_keys = self._children_map.get(key, [])
        if not child_keys:
            return False

        # Collapse when none of the children are visible
        return not any(self.malcolm_config.is_item_visible(ck) for ck in child_keys)

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

        # Add MenuItems when the store has them (MalcolmConfig does; InstallContext does not).
        get_menu_items = getattr(self.malcolm_config, "get_all_menu_items", None)
        if callable(get_menu_items):
            for key, item in get_menu_items().items():
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
            """Get ConfigItem children of a key, skipping MenuItems.

            Structural (not visibility-filtered) so an item's CollapsibleContainer
            wrapper stays consistent as children toggle visible/invisible.
            """
            result = []
            for child_key in all_children.get(parent_key, []):
                if child_key in config_item_keys:
                    result.append(child_key)
                else:
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

            if self.hide_invisible and not is_menu_item and not self.malcolm_config.is_item_visible(key):
                return

            if not is_menu_item:
                result.append((key, item, depth))

            child_depth = depth if is_menu_item else depth + 1
            for child_key in _sorted_keys(all_children.get(key, [])):
                walk(child_key, child_depth)

        # Start from this tab's root, or from all top-level items when no root
        if self.menu_item_key is None:
            top_level = [k for k, it in item_by_key.items() if not it.ui_parent]
            for child_key in _sorted_keys(top_level):
                walk(child_key, 0)
        else:
            root_item = item_by_key.get(self.menu_item_key)
            if root_item:
                if isinstance(root_item, MenuItem):
                    child_keys = all_children.get(self.menu_item_key, [])
                    for child_key in _sorted_keys(child_keys):
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

    def _should_omit_item_for_profile(self, key: str) -> bool:
        """Return True when item should be omitted entirely for selected profile."""
        from scripts.installer.core.dependencies import DEPENDENCY_CONFIG
        from scripts.malcolm_constants import PROFILE_HEDGEHOG, PROFILE_MALCOLM

        current_profile = self.malcolm_config.get_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE)
        if current_profile not in (PROFILE_HEDGEHOG, PROFILE_MALCOLM):
            return False

        item = self.malcolm_config.get_item(key)
        if item and not item_allowed_for_profile(item, current_profile):
            return True

        dep_spec = DEPENDENCY_CONFIG.get(key)
        if not dep_spec or not dep_spec.visibility or not dep_spec.visibility.depends_on:
            return False

        vis = dep_spec.visibility
        if not callable(vis.condition):
            return False

        dep_keys = vis.depends_on if isinstance(vis.depends_on, list) else [vis.depends_on]
        if KEY_CONFIG_ITEM_MALCOLM_PROFILE not in dep_keys:
            return False

        other_profile = PROFILE_MALCOLM if current_profile == PROFILE_HEDGEHOG else PROFILE_HEDGEHOG
        current_values = []
        other_values = []
        for dep_key in dep_keys:
            if dep_key == KEY_CONFIG_ITEM_MALCOLM_PROFILE:
                current_values.append(current_profile)
                other_values.append(other_profile)
            else:
                value = self.malcolm_config.get_value(dep_key)
                current_values.append(value)
                other_values.append(value)

        return (not vis.condition(*current_values)) and vis.condition(*other_values)

    def _update_widget_visibility(self, key: str):
        """Update widget enabled/disabled state based on MalcolmConfig visibility.

        Items are shown (packed) but disabled when their visibility condition is false.
        iso_only items are fully hidden when invisible.

        Args:
            key: The ConfigItem key
        """
        if key not in self.widget_map:
            return

        container = self.widget_map[key]
        is_visible = self.malcolm_config.is_item_visible(key)

        item = self.malcolm_config.get_item(key)
        if not item:
            return

        if is_visible:
            self._set_widget_state_recursive(container, "normal")
        else:
            self._set_widget_state_recursive(container, "disabled")
        self._update_panel_style(key, is_visible)

        # iso_only items get fully hidden/shown
        if item.metadata.get("iso_only"):
            target = self.pack_targets.get(key)
            if target:
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
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        def on_linux_scroll(event):
            try:
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
            except Exception:
                pass

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
        scrollable_frame.bind("<Destroy>", unbind_events, add="+")

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

    def scroll_to_item(self, key: str) -> None:
        """Scroll the tab so the given item is visible, expanding collapsed ancestors.

        Args:
            key: ConfigItem key to bring into view
        """
        self._expand_ancestors(key)

        target = self.pack_targets.get(key)
        if target is None or self._scrollable_frame is None:
            return
        canvas = getattr(self._scrollable_frame, "_parent_canvas", None)
        if canvas is None:
            return

        canvas.update_idletasks()
        inner_children = canvas.winfo_children()
        inner_frame = inner_children[0] if inner_children else None
        total_height = inner_frame.winfo_height() if inner_frame else canvas.winfo_height()
        if total_height <= 0:
            return

        target_y = target.winfo_y()
        # Small leading margin so the item isn't flush to the top edge
        fraction = max(0.0, min(1.0, (target_y - 20) / total_height))
        canvas.yview_moveto(fraction)

    def _expand_ancestors(self, key: str) -> None:
        """Expand any collapsed ancestor containers so the target becomes reachable."""
        item = self.malcolm_config.get_item(key)
        if not item:
            return
        parent_key = item.ui_parent
        while parent_key:
            container = self._containers.get(parent_key)
            if container and self._collapse_state.get(parent_key):
                container.set_collapsed(False)
                self._collapse_state[parent_key] = False
            parent_item = self.malcolm_config.get_item(parent_key)
            if not parent_item:
                break
            parent_key = parent_item.ui_parent

    def pulse_item(self, key: str, pulses: int = 2, interval_ms: int = 180) -> None:
        """Flash the target item's container border with the accent color.

        Args:
            key: ConfigItem key whose container should pulse
            pulses: Number of on/off cycles
            interval_ms: Delay between toggles
        """
        target = self.pack_targets.get(key)
        if target is None or not self.accent_colors:
            return
        accent = self.accent_colors.get("primary")
        if not accent:
            return

        try:
            original_color = target.cget("border_color")
            original_width = target.cget("border_width")
        except (AttributeError, ValueError, TypeError):
            return

        steps_remaining = pulses * 2  # each pulse = one "on" + one "off"

        def step():
            nonlocal steps_remaining
            if steps_remaining <= 0:
                target.configure(border_color=original_color, border_width=original_width)
                return
            if steps_remaining % 2 == 0:
                target.configure(border_color=original_color, border_width=original_width)
            else:
                target.configure(border_color=accent, border_width=3)
            steps_remaining -= 1
            target.after(interval_ms, step)

        step()
