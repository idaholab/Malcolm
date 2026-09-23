#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Simple tooltip component for disabled widgets."""

import tkinter as tk
import customtkinter

from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.components.styles import TOOLTIP_BG_COLOR, TOOLTIP_CORNER_RADIUS


def add_tooltip(widget, text: str, delay: float = 0.5):
    """Add a tooltip to a widget that shows on hover.

    Args:
        widget: The widget to add the tooltip to
        text: The tooltip text to display
        delay: Delay in seconds before showing tooltip (default: 0.5)
    """
    # First, clean up any existing tooltip to prevent orphaned windows
    remove_tooltip(widget)

    # Store tooltip state as widget attributes for cleanup
    widget._tooltip_window = None
    widget._tooltip_after_id = None
    widget._tooltip_text = text  # Store text for reference

    def show_tooltip(event):
        # Cancel any existing scheduled tooltip first to prevent duplicates
        if widget._tooltip_after_id:
            widget.after_cancel(widget._tooltip_after_id)
            widget._tooltip_after_id = None

        # Don't schedule if tooltip already showing
        if widget._tooltip_window:
            return

        def create_tooltip():
            # Double-check tooltip doesn't exist (race condition protection)
            if widget._tooltip_window:
                return

            try:
                x = widget.winfo_rootx() + 10
                y = widget.winfo_rooty() + widget.winfo_height() + 5

                widget._tooltip_window = customtkinter.CTkToplevel()
                widget._tooltip_window.wm_overrideredirect(True)
                widget._tooltip_window.wm_geometry(f"+{x}+{y}")

                label = customtkinter.CTkLabel(
                    widget._tooltip_window,
                    text=text,
                    fg_color=TOOLTIP_BG_COLOR,
                    corner_radius=TOOLTIP_CORNER_RADIUS,
                    padx=8,
                    pady=4,
                )
                label.pack()
            except tk.TclError:
                # Widget was destroyed before tooltip could be created
                widget._tooltip_window = None
            except Exception as e:
                InstallerLogger.debug(f"Tooltip creation failed: {e}")
                widget._tooltip_window = None

        # Schedule tooltip to appear after delay
        widget._tooltip_after_id = widget.after(int(delay * 1000), create_tooltip)

    def hide_tooltip(event):
        # Cancel scheduled tooltip if mouse leaves before delay
        if widget._tooltip_after_id:
            try:
                widget.after_cancel(widget._tooltip_after_id)
            except tk.TclError:
                pass  # Timer already fired or widget destroyed
            except Exception as e:
                InstallerLogger.debug(f"Could not cancel tooltip timer: {e}")
            widget._tooltip_after_id = None

        # Destroy tooltip if it exists
        if widget._tooltip_window:
            try:
                widget._tooltip_window.destroy()
            except tk.TclError:
                pass  # Window already destroyed
            except Exception as e:
                InstallerLogger.debug(f"Could not destroy tooltip window: {e}")
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
        try:
            widget.after_cancel(widget._tooltip_after_id)
        except tk.TclError:
            pass  # Timer already fired or widget destroyed
        except Exception as e:
            InstallerLogger.debug(f"Could not cancel tooltip timer during removal: {e}")
        widget._tooltip_after_id = None

    # Destroy visible tooltip window
    if hasattr(widget, '_tooltip_window') and widget._tooltip_window:
        try:
            widget._tooltip_window.destroy()
        except tk.TclError:
            pass  # Window already destroyed
        except Exception as e:
            InstallerLogger.debug(f"Could not destroy tooltip window during removal: {e}")
        widget._tooltip_window = None

    # Unbind events (may fail if widget doesn't have bindings)
    try:
        widget.unbind("<Enter>")
        widget.unbind("<Leave>")
    except tk.TclError:
        pass  # Widget destroyed or never had bindings
    except Exception as e:
        InstallerLogger.debug(f"Could not unbind tooltip events: {e}")
