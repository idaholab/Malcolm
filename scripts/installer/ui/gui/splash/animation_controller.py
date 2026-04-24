#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Animation timing and orchestration utilities for splash screen."""

import time
from dataclasses import dataclass, field
from typing import Callable, Optional
import uuid

from scripts.installer.ui.gui.splash import FRAME_DELAY_MS


@dataclass
class AnimationConfig:
    """Configuration for a single animation."""

    duration_ms: int
    easing: str = "ease_out_cubic"  # ease_in_cubic, ease_out_cubic, ease_in_out_cubic, linear
    delay_ms: int = 0


class AnimationController:
    """
    Manages animation timing using tkinter's after() method.

    Provides frame-by-frame animation with configurable easing functions
    and callbacks for animation lifecycle events. Includes safety checks
    for widget existence and proper cleanup on destroy.
    """

    def __init__(self, widget):
        """
        Initialize animation controller.

        Args:
            widget: tkinter widget to use for after() scheduling
        """
        self._widget = widget
        self._animations: dict[str, dict] = {}  # animation_id -> state dict

    def animate(
        self,
        config: AnimationConfig,
        on_frame: Callable[[float], None],
        on_complete: Optional[Callable[[], None]] = None,
    ) -> str:
        """
        Start an animation with the given configuration.

        Args:
            config: Animation configuration (duration, easing, delay)
            on_frame: Called each frame with progress (0.0 to 1.0, eased)
            on_complete: Called when animation completes

        Returns:
            Animation ID for cancellation
        """
        animation_id = str(uuid.uuid4())

        easing_func = self._get_easing_func(config.easing)

        state = {
            "config": config,
            "on_frame": on_frame,
            "on_complete": on_complete,
            "easing_func": easing_func,
            "start_time": None,
            "after_id": None,
        }
        self._animations[animation_id] = state

        if config.delay_ms > 0:
            state["after_id"] = self._widget.after(
                config.delay_ms, lambda: self._start_animation(animation_id)
            )
        else:
            self._start_animation(animation_id)

        return animation_id

    def _start_animation(self, animation_id: str) -> None:
        """Begin the animation frame loop."""
        if animation_id not in self._animations:
            return

        state = self._animations[animation_id]
        state["start_time"] = time.time() * 1000  # Convert to ms

        # Call first frame immediately with progress 0
        self._animate_frame(animation_id)

    def _animate_frame(self, animation_id: str) -> None:
        """Single animation frame update."""
        if animation_id not in self._animations:
            return

        # Safety check: verify widget still exists
        if not self._widget_exists():
            self._cleanup_animation(animation_id)
            return

        state = self._animations[animation_id]
        config = state["config"]
        current_time = time.time() * 1000

        elapsed = current_time - state["start_time"]

        if elapsed >= config.duration_ms:
            # Animation complete - call final frame with progress 1.0
            state["on_frame"](1.0)
            on_complete = state["on_complete"]
            self._cleanup_animation(animation_id)
            if on_complete:
                on_complete()
            return

        # Calculate progress with easing
        raw_progress = elapsed / config.duration_ms
        eased_progress = state["easing_func"](raw_progress)

        # Update frame
        state["on_frame"](eased_progress)

        # Schedule next frame
        state["after_id"] = self._widget.after(
            FRAME_DELAY_MS, lambda: self._animate_frame(animation_id)
        )

    def _widget_exists(self) -> bool:
        """Check if the widget still exists and is valid."""
        try:
            return self._widget.winfo_exists()
        except Exception:
            return False

    def _cleanup_animation(self, animation_id: str) -> None:
        """Clean up animation state."""
        if animation_id in self._animations:
            state = self._animations.pop(animation_id)
            if state["after_id"] is not None:
                try:
                    self._widget.after_cancel(state["after_id"])
                except Exception:
                    pass  # Widget may already be destroyed

    def cancel(self, animation_id: str) -> None:
        """Cancel a running animation."""
        self._cleanup_animation(animation_id)

    def cancel_all(self) -> None:
        """Cancel all running animations."""
        animation_ids = list(self._animations.keys())
        for animation_id in animation_ids:
            self._cleanup_animation(animation_id)

    def _get_easing_func(self, easing: str) -> Callable[[float], float]:
        """Get the easing function by name."""
        easing_funcs = {
            "linear": self.linear,
            "ease_in_cubic": self.ease_in_cubic,
            "ease_out_cubic": self.ease_out_cubic,
            "ease_in_out_cubic": self.ease_in_out_cubic,
        }
        return easing_funcs.get(easing, self.ease_out_cubic)

    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)."""
        return t

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in function for smooth acceleration."""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out function for smooth deceleration."""
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out for smooth acceleration and deceleration."""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2


def lerp(start: float, end: float, progress: float) -> float:
    """Linear interpolation between two values."""
    return start + (end - start) * progress


def lerp_int(start: int, end: int, progress: float) -> int:
    """Linear interpolation between two integers."""
    return int(start + (end - start) * progress)
