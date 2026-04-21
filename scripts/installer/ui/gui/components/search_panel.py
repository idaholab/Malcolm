#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.

"""Bottom-docked command-palette search for the GUI installer.

Ctrl+F opens, Esc closes, arrow keys navigate, Enter jumps to the selected item.
Shares the same search backend (malcolm_config.search_items) as the TUI/DUI so
results stay consistent across all three UIs.
"""

from typing import Callable, Dict, List, Optional, TYPE_CHECKING
import customtkinter

from scripts.installer.ui.gui.components.styles import (
    DEFAULT_BORDER_COLOR,
    PANEL_BORDER_WIDTH,
    PANEL_CORNER_RADIUS,
    TEXT_COLOR_MUTED,
)

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig


PANEL_HEIGHT = 260
ROW_CORNER_RADIUS = 4
MENU_PREFIX = "\u25b8"  # ▸ triangle for section results
CONFIG_PREFIX = "\u2022"  # • bullet for config item results


class SearchPanel(customtkinter.CTkFrame):
    """Bottom-docked search overlay with live-filtered, keyboard-navigable results."""

    def __init__(
        self,
        parent,
        malcolm_config: "MalcolmConfig",
        on_jump: Callable[[str], None],
        accent_colors: Dict[str, str],
        pack_before: Optional[customtkinter.CTkBaseClass] = None,
    ):
        super().__init__(
            parent,
            height=PANEL_HEIGHT,
            corner_radius=PANEL_CORNER_RADIUS,
            border_width=PANEL_BORDER_WIDTH,
            border_color=DEFAULT_BORDER_COLOR,
        )
        self._mc = malcolm_config
        self._on_jump = on_jump
        self._accent = accent_colors
        self._pack_before = pack_before
        self._results: List[Dict] = []
        self._selected_idx: int = 0
        self._result_rows: List[customtkinter.CTkFrame] = []

        self.pack_propagate(False)
        self._build_ui()

    def _build_ui(self):
        entry_row = customtkinter.CTkFrame(self, fg_color="transparent")
        entry_row.pack(fill="x", padx=12, pady=(10, 6))

        label = customtkinter.CTkLabel(
            entry_row,
            text="Search",
            font=("Helvetica", 12, "bold"),
            anchor="w",
        )
        label.pack(side="left", padx=(0, 10))

        self._entry = customtkinter.CTkEntry(
            entry_row,
            placeholder_text="Type to filter settings and sections...",
        )
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.bind("<KeyRelease>", self._on_type)
        self._entry.bind("<Down>", self._on_down)
        self._entry.bind("<Up>", self._on_up)
        self._entry.bind("<Return>", self._on_enter)
        self._entry.bind("<Escape>", self._on_escape)

        self._results_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="transparent",
        )
        self._results_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        hint = customtkinter.CTkLabel(
            self,
            text="\u2191\u2193 navigate  \u00b7  Enter to jump  \u00b7  Esc to close",
            font=("Helvetica", 10),
            text_color=TEXT_COLOR_MUTED,
        )
        hint.pack(side="bottom", pady=(0, 6))

        self._render_placeholder("Start typing to search...")

    def show(self):
        """Dock the panel above the button bar and focus the entry."""
        if not self.winfo_ismapped():
            if self._pack_before is not None:
                self.pack(side="bottom", fill="x", padx=10, pady=(0, 5), before=self._pack_before)
            else:
                self.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self._entry.focus_set()
        if self._entry.get():
            self._entry.select_range(0, "end")

    def hide(self):
        """Collapse the panel back down."""
        if self.winfo_ismapped():
            self.pack_forget()

    def toggle(self):
        if self.winfo_ismapped():
            self.hide()
        else:
            self.show()

    def _on_type(self, event=None):
        if event and event.keysym in ("Down", "Up", "Return", "Escape"):
            return
        term = self._entry.get().strip()
        self._results = self._mc.search_items(term) if term else []
        self._selected_idx = 0
        self._render_results()

    def _on_down(self, event=None):
        if self._results and self._selected_idx < len(self._results) - 1:
            self._selected_idx += 1
            self._render_results()
            self._scroll_selected_into_view()
        return "break"

    def _on_up(self, event=None):
        if self._results and self._selected_idx > 0:
            self._selected_idx -= 1
            self._render_results()
            self._scroll_selected_into_view()
        return "break"

    def _on_enter(self, event=None):
        if self._results:
            key = self._results[self._selected_idx]["key"]
            self.hide()
            self._on_jump(key)
        return "break"

    def _on_escape(self, event=None):
        self.hide()
        return "break"

    def _clear_result_rows(self):
        for row in self._result_rows:
            row.destroy()
        self._result_rows = []

    def _render_placeholder(self, text: str):
        self._clear_result_rows()
        placeholder = customtkinter.CTkLabel(
            self._results_frame,
            text=text,
            text_color=TEXT_COLOR_MUTED,
        )
        placeholder.pack(pady=12)
        self._result_rows.append(placeholder)

    def _render_results(self):
        if not self._results:
            term = self._entry.get().strip()
            self._render_placeholder(f"No matches for '{term}'" if term else "Start typing to search...")
            return

        self._clear_result_rows()
        for idx, result in enumerate(self._results):
            row = self._build_result_row(result, idx == self._selected_idx, idx)
            row.pack(fill="x", pady=1)
            self._result_rows.append(row)

    def _build_result_row(self, result: Dict, is_selected: bool, idx: int) -> customtkinter.CTkFrame:
        bg = self._accent["primary"] if is_selected else "transparent"
        text_color = self._accent["text"] if is_selected else None
        dim_color = self._accent["text"] if is_selected else TEXT_COLOR_MUTED

        row = customtkinter.CTkFrame(
            self._results_frame,
            fg_color=bg,
            corner_radius=ROW_CORNER_RADIUS,
        )

        is_menu = result.get("item_type") == "menu"
        visible = result.get("visible", True)
        prefix = MENU_PREFIX if is_menu else CONFIG_PREFIX
        label = result["label"] or result["key"]

        left_text = f"{prefix}  {label}"
        left = customtkinter.CTkLabel(
            row,
            text=left_text,
            font=("Helvetica", 12, "bold" if is_selected else "normal"),
            anchor="w",
            text_color=text_color,
        )
        left.pack(side="left", padx=12, pady=6)

        context = self._result_context(result)
        if context:
            right = customtkinter.CTkLabel(
                row,
                text=context,
                font=("Helvetica", 11),
                anchor="e",
                text_color=dim_color,
            )
            right.pack(side="right", padx=12, pady=6)

        if not visible and not is_menu:
            # Visually mark hidden items so users understand why selecting won't help much
            try:
                left.configure(text_color=dim_color)
            except (AttributeError, ValueError):
                pass

        def _on_click(_event, selected_idx=idx):
            self._selected_idx = selected_idx
            self._render_results()
            self._on_enter()

        for clickable in (row, left):
            clickable.bind("<Button-1>", _on_click)
        if context:
            right.bind("<Button-1>", _on_click)

        return row

    def _result_context(self, result: Dict) -> str:
        ui_parent = result.get("ui_parent")
        is_menu = result.get("item_type") == "menu"

        if is_menu:
            if ui_parent:
                parent = self._mc.get_menu_item(ui_parent)
                if parent and parent.label:
                    return f"in {parent.label}"
            return "section"

        if not result.get("visible", True):
            return "hidden"

        if ui_parent:
            parent = self._mc.get_menu_item(ui_parent)
            if parent and parent.label:
                return parent.label
            parent_item = self._mc.get_item(ui_parent)
            if parent_item and parent_item.label:
                return parent_item.label
        return ""

    def _scroll_selected_into_view(self):
        if not self._result_rows or self._selected_idx >= len(self._result_rows):
            return
        target = self._result_rows[self._selected_idx]
        canvas = getattr(self._results_frame, "_parent_canvas", None)
        if canvas is None:
            return
        try:
            canvas.update_idletasks()
            target_y = target.winfo_y()
            inner = canvas.winfo_children()[0] if canvas.winfo_children() else None
            total_height = inner.winfo_height() if inner else canvas.winfo_height()
            if total_height <= 0:
                return
            fraction = max(0.0, min(1.0, target_y / total_height))
            canvas.yview_moveto(fraction)
        except (AttributeError, ValueError, IndexError):
            return
