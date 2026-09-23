#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""
Collapsible Container Component
==============================

A container that can be collapsed/expanded to show/hide its children.
Used for grouping ConfigItems with their dependent children in the GUI.
"""

from typing import Callable, Optional, Tuple
import customtkinter

from scripts.installer.ui.gui.components.styles import (
    CONTAINER_COLORS_BY_DEPTH,
    CONTAINER_CORNER_RADIUS,
    PANEL_BORDER_WIDTH,
    TAB_BG_FALLBACK,
    TOGGLE_CORNER_RADIUS,
    TOGGLE_HOVER_COLOR,
    TOGGLE_TEXT_COLOR,
)


# Collapse toggle symbols
COLLAPSE_TOGGLE_EXPANDED = "\u25BC"   # ▼
COLLAPSE_TOGGLE_COLLAPSED = "\u25B6"  # ▶

def _get_container_colors(depth: int) -> dict:
    """Get container colors for a given depth level."""
    capped_depth = min(depth, 3)
    return CONTAINER_COLORS_BY_DEPTH.get(capped_depth, CONTAINER_COLORS_BY_DEPTH[3])


class CollapsibleContainer:
    """A container that can be collapsed/expanded to show/hide children.

    Structure:
        outer_frame (border container)
        └── header_frame (contains parent widget + toggle button)
        └── content_frame (contains children, hidden when collapsed)
    """

    def __init__(
        self,
        parent: customtkinter.CTkFrame,
        depth: int,
        on_toggle: Optional[Callable[[str, bool], None]] = None,
        key: str = "",
        collapsed: bool = False,
        tab_bg: Optional[Tuple[str, str]] = None,
    ):
        """Create a collapsible container.

        Args:
            parent: Parent widget to place the container in
            depth: Nesting depth (0 = top level, higher = more nested)
            on_toggle: Callback when collapse state changes: fn(key, collapsed)
            key: Config item key (passed to on_toggle callback)
            collapsed: Initial collapse state (True = collapsed)
            tab_bg: Background color of the tab for blending corners
        """
        self._depth = depth
        self._collapsed = collapsed
        self._on_toggle = on_toggle
        self._key = key
        self._tab_bg = tab_bg or TAB_BG_FALLBACK

        colors = _get_container_colors(depth)

        # Outer frame with border
        self.outer_frame = customtkinter.CTkFrame(
            parent,
            fg_color=colors["bg"],
            bg_color=self._tab_bg,
            corner_radius=CONTAINER_CORNER_RADIUS,
            border_width=PANEL_BORDER_WIDTH,
            border_color=colors["border"],
        )

        # Header frame (holds parent widget + toggle)
        self._header_frame = customtkinter.CTkFrame(
            self.outer_frame,
            fg_color="transparent",
        )
        self._header_frame.pack(fill="x", padx=8, pady=(6, 0))
        self._header_frame.grid_columnconfigure(0, weight=1)

        # Widget container (where the parent ConfigItem widget goes)
        self._widget_container = customtkinter.CTkFrame(
            self._header_frame,
            fg_color="transparent",
        )
        self._widget_container.grid(row=0, column=0, sticky="ew")

        # Toggle button
        self._toggle_btn = customtkinter.CTkButton(
            self._header_frame,
            text=COLLAPSE_TOGGLE_COLLAPSED if collapsed else COLLAPSE_TOGGLE_EXPANDED,
            width=24,
            height=24,
            corner_radius=TOGGLE_CORNER_RADIUS,
            fg_color="transparent",
            hover_color=TOGGLE_HOVER_COLOR,
            text_color=TOGGLE_TEXT_COLOR,
            command=self._on_toggle_clicked,
        )
        self._toggle_btn.grid(row=0, column=1, sticky="ne", padx=(8, 0))

        # Content frame (holds children). Match container bg so child corners blend in.
        self._content_frame = customtkinter.CTkFrame(
            self.outer_frame,
            fg_color=colors["bg"],
            bg_color=colors["bg"],
        )
        if not collapsed:
            self._content_frame.pack(fill="x", padx=8, pady=(4, 6))

    def _on_toggle_clicked(self):
        """Handle toggle button click."""
        self._collapsed = not self._collapsed
        self._update_ui()
        if self._on_toggle:
            self._on_toggle(self._key, self._collapsed)

    def _update_ui(self):
        """Update UI to reflect current collapse state."""
        if self._collapsed:
            self._toggle_btn.configure(text=COLLAPSE_TOGGLE_COLLAPSED)
            self._content_frame.pack_forget()
        else:
            self._toggle_btn.configure(text=COLLAPSE_TOGGLE_EXPANDED)
            self._content_frame.pack(fill="x", padx=8, pady=(4, 6))

    def set_collapsed(self, collapsed: bool):
        """Set the collapse state.

        Args:
            collapsed: True to collapse, False to expand
        """
        if self._collapsed != collapsed:
            self._collapsed = collapsed
            self._update_ui()

    def is_collapsed(self) -> bool:
        """Return whether the container is collapsed."""
        return self._collapsed

    def get_header_frame(self) -> customtkinter.CTkFrame:
        """Return the frame where the parent ConfigItem widget should be placed."""
        return self._widget_container

    def get_content_frame(self) -> customtkinter.CTkFrame:
        """Return the frame where children should be rendered."""
        return self._content_frame

    def pack(self, **kwargs):
        """Pack the outer frame."""
        self.outer_frame.pack(**kwargs)

    def pack_info(self) -> dict:
        """Get pack info for the outer frame."""
        return self.outer_frame.pack_info()

    def pack_forget(self):
        """Hide the outer frame."""
        self.outer_frame.pack_forget()
