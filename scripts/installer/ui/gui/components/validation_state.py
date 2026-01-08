#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Visual validation state management for GUI widgets."""

import tkinter as tk
import customtkinter

from scripts.installer.utils.logger_utils import InstallerLogger


def _configure_supported(widget, **kwargs):
    """Configure widget with supported kwargs only, ignore unsupported.

    This is a best-effort function for setting visual properties on widgets
    that may or may not support all configuration options.
    """
    try:
        widget.configure(**kwargs)
        return
    except tk.TclError:
        # Expected: widget doesn't support some options, fall through to filter
        pass
    except Exception as e:
        InstallerLogger.debug(f"Unexpected error configuring widget: {e}")
        return

    try:
        supported = set(widget.configure().keys())
    except Exception as e:
        InstallerLogger.debug(f"Could not get widget config keys: {e}")
        return

    filtered = {key: value for key, value in kwargs.items() if key in supported}
    if not filtered:
        return
    try:
        widget.configure(**filtered)
    except Exception as e:
        InstallerLogger.debug(f"Failed to configure filtered widget options: {e}")


def show_validation_error(widget, error_label, message: str):
    """Show red border and error message on widget. Fail loudly.

    Args:
        widget: The input widget to mark as invalid
        error_label: The label widget to display the error message
        message: The error message to display
    """
    # Set red border on input widget
    _configure_supported(widget, border_color="red", border_width=2)

    # Show error message
    error_label.configure(text=f"⚠ {message}", text_color="red")
    error_label.grid()


def clear_validation_error(widget, error_label):
    """Clear validation error state from widget.

    Args:
        widget: The input widget to clear error state from
        error_label: The label widget to hide
    """
    # Reset border to normal
    _configure_supported(widget, border_color=("gray60", "gray40"), border_width=1)

    # Hide error message
    error_label.configure(text="")
    error_label.grid_remove()
