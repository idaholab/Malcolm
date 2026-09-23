#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.

"""Utilities for profile-scoped item and choice visibility."""

from typing import Any, Iterable, Optional

from scripts.installer.configs.constants.profile_scope_keys import (
    META_ALLOWED_PROFILES,
    META_CHOICE_ALLOWED_PROFILES,
)


def choice_value(choice: Any) -> Any:
    """Normalize a choice entry to its internal value."""
    if isinstance(choice, tuple) and len(choice) >= 1:
        return choice[0]
    return choice


def item_allowed_for_profile(item: Any, profile: Optional[str]) -> bool:
    """Return True when item-level profile scope allows the current profile."""
    if not item or not profile:
        return True
    allowed = item.metadata.get(META_ALLOWED_PROFILES)
    if not allowed:
        return True
    return profile in set(allowed)


def choice_allowed_for_profile(item: Any, raw_choice: Any, profile: Optional[str]) -> bool:
    """Return True when choice-level profile scope allows the current profile."""
    if not item or not profile:
        return True
    scoped = item.metadata.get(META_CHOICE_ALLOWED_PROFILES)
    if not scoped:
        return True
    val = choice_value(raw_choice)
    allowed = scoped.get(val)
    if not allowed:
        return True
    return profile in set(allowed)


def filter_choices_for_profile(choices: Iterable[Any], item: Any, profile: Optional[str]) -> list[Any]:
    """Filter raw choices by profile scope metadata."""
    return [c for c in choices if choice_allowed_for_profile(item, c, profile)]
