#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Animated loading dots indicator."""

from typing import Optional
import customtkinter

from scripts.installer.ui.gui.splash import LOADING_DOT_INTERVAL_MS


class LoadingDots(customtkinter.CTkLabel):
    """
    Animated "..." loading indicator.

    Cycles through "", ".", "..", "..." patterns at a configurable interval.
    Properly handles cleanup via after_cancel when stopped or destroyed.
    """

    def __init__(
        self,
        parent,
        base_text: str = "Loading",
        interval_ms: int = LOADING_DOT_INTERVAL_MS,
        **kwargs,
    ):
        """
        Initialize loading dots indicator.

        Args:
            parent: Parent widget
            base_text: Text before the dots (e.g., "Loading")
            interval_ms: Milliseconds between dot updates
            **kwargs: Additional CTkLabel arguments
        """
        # Set default font if not provided
        if "font" not in kwargs:
            kwargs["font"] = ("Helvetica", 14)

        super().__init__(parent, text=base_text, **kwargs)

        self._base_text = base_text
        self._interval_ms = interval_ms
        self._dot_count = 0
        self._max_dots = 3
        self._after_id: Optional[str] = None
        self._running = False

    def start(self) -> None:
        """Start the animation."""
        if self._running:
            return

        self._running = True
        self._dot_count = 0
        self._update_dots()

    def stop(self) -> None:
        """Stop the animation and reset to base text."""
        self._running = False

        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass  # Widget may already be destroyed
            self._after_id = None

        # Reset to base text
        try:
            if self.winfo_exists():
                self.configure(text=self._base_text)
        except Exception:
            pass

    def _update_dots(self) -> None:
        """Update the dot count for animation frame."""
        if not self._running:
            return

        # Safety check: verify widget still exists
        try:
            if not self.winfo_exists():
                self._running = False
                return
        except Exception:
            self._running = False
            return

        # Update text with current dot count
        dots = "." * self._dot_count
        self.configure(text=f"{self._base_text}{dots}")

        # Cycle through 0, 1, 2, 3 dots
        self._dot_count = (self._dot_count + 1) % (self._max_dots + 1)

        # Schedule next update
        self._after_id = self.after(self._interval_ms, self._update_dots)

    def destroy(self) -> None:
        """Clean up before destroying widget."""
        self.stop()
        super().destroy()
