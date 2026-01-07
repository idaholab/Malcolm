#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Visual validation state management for GUI widgets."""

import customtkinter


def show_validation_error(widget, error_label, message: str):
    """Show red border and error message on widget. Fail loudly.

    Args:
        widget: The input widget to mark as invalid
        error_label: The label widget to display the error message
        message: The error message to display
    """
    # Set red border on input widget
    widget.configure(border_color="red", border_width=2)

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
    widget.configure(border_color=("gray60", "gray40"), border_width=1)

    # Hide error message
    error_label.configure(text="")
    error_label.grid_remove()
