#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.

"""Bottom-docked search results panel for the GUI installer.

The entry lives in MainWindow's bottom bar; this panel renders its results.
MainWindow drives it via set_term / move_selection / activate_selection.
Shares the search backend (malcolm_config.search_items) with the TUI/DUI.
"""

from typing import Callable, Dict, List, TYPE_CHECKING
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
MENU_PREFIX = "▸"  # ▸ triangle for section results
CONFIG_PREFIX = "•"  # • bullet for config item results


class SearchPanel(customtkinter.CTkFrame):
    """Bottom-docked results panel driven by the bottom bar's search entry."""

    def __init__(
        self,
        parent,
        malcolm_config: "MalcolmConfig",
        on_jump: Callable[[str], None],
        accent_colors: Dict[str, str],
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
        self._results: List[Dict] = []
        self._selected_idx: int = 0
        self._result_rows: List[customtkinter.CTkFrame] = []

        self.pack_propagate(False)
        self._build_ui()

    def _build_ui(self):
        self._results_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="transparent",
        )
        self._results_frame.pack(fill="both", expand=True, padx=12, pady=(10, 4))

        hint = customtkinter.CTkLabel(
            self,
            text="↑↓ navigate  ·  Enter to jump  ·  Esc to close",
            font=("Helvetica", 10),
            text_color=TEXT_COLOR_MUTED,
        )
        hint.pack(side="bottom", pady=(0, 6))

        self._render_placeholder("Start typing to search...")

    def show(self):
        """Dock the panel above the bottom bar.

        Relies on the button bar having been packed with side="bottom" first.
        Packing this panel with side="bottom" (without `before=`) places it
        above the bar in pack order — Tk processes bottom-sided widgets in
        pack-list order and each claims the bottom of the remaining cavity,
        so the second bottom widget lands above the first.
        """
        if not self.winfo_ismapped():
            self.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def hide(self):
        if self.winfo_ismapped():
            self.pack_forget()

    def set_term(self, term: str) -> None:
        """Update result set for a new search term, showing/hiding as needed."""
        term = term.strip()
        if not term:
            self._results = []
            self.hide()
            return
        self._results = self._mc.search_items(term)
        self._selected_idx = 0
        self.show()
        self._render_results()

    def move_selection(self, delta: int) -> None:
        if not self._results:
            return
        self._selected_idx = max(0, min(len(self._results) - 1, self._selected_idx + delta))
        self._render_results()
        self._scroll_selected_into_view()

    def activate_selection(self) -> None:
        """Jump to the currently selected result, if any."""
        if not self._results:
            return
        key = self._results[self._selected_idx]["key"]
        self.hide()
        self._on_jump(key)

    def has_results(self) -> bool:
        return bool(self._results)

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
            self._render_placeholder("No matches")
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
            try:
                left.configure(text_color=dim_color)
            except (AttributeError, ValueError):
                pass

        def _on_click(_event, selected_idx=idx):
            self._selected_idx = selected_idx
            self._render_results()
            self.activate_selection()

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
