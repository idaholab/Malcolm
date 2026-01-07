#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Simple tooltip component for disabled widgets."""

import customtkinter


def add_tooltip(widget, text: str, delay: float = 0.5):
    """Add a tooltip to a widget that shows on hover.

    Args:
        widget: The widget to add the tooltip to
        text: The tooltip text to display
        delay: Delay in seconds before showing tooltip (default: 0.5)
    """
    # Store tooltip state as widget attributes for cleanup
    widget._tooltip_window = None
    widget._tooltip_after_id = None

    def show_tooltip(event):
        def create_tooltip():
            if widget._tooltip_window:
                return

            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() + widget.winfo_height() + 5

            widget._tooltip_window = customtkinter.CTkToplevel()
            widget._tooltip_window.wm_overrideredirect(True)
            widget._tooltip_window.wm_geometry(f"+{x}+{y}")

            label = customtkinter.CTkLabel(
                widget._tooltip_window,
                text=text,
                fg_color=("gray95", "gray20"),
                corner_radius=4,
                padx=8,
                pady=4,
            )
            label.pack()

        # Schedule tooltip to appear after delay
        widget._tooltip_after_id = widget.after(int(delay * 1000), create_tooltip)

    def hide_tooltip(event):
        # Cancel scheduled tooltip if mouse leaves before delay
        if widget._tooltip_after_id:
            widget.after_cancel(widget._tooltip_after_id)
            widget._tooltip_after_id = None

        # Destroy tooltip if it exists
        if widget._tooltip_window:
            widget._tooltip_window.destroy()
            widget._tooltip_window = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)


def remove_tooltip(widget):
    """Remove tooltip from a widget and destroy any visible tooltip window.

    Args:
        widget: The widget to remove the tooltip from
    """
    # Cancel any scheduled tooltip
    if hasattr(widget, '_tooltip_after_id') and widget._tooltip_after_id:
        widget.after_cancel(widget._tooltip_after_id)
        widget._tooltip_after_id = None

    # Destroy visible tooltip window
    if hasattr(widget, '_tooltip_window') and widget._tooltip_window:
        widget._tooltip_window.destroy()
        widget._tooltip_window = None

    # Unbind events
    widget.unbind("<Enter>")
    widget.unbind("<Leave>")
