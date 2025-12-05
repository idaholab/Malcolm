#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple, Dict, Optional, Union

from scripts.installer.core.config_item import ConfigItem
from scripts.installer.core.menu_item import MenuItem


@dataclass
class StoreRow:
    key: str
    label: str
    value_formatted: Any
    choices: List[Any]
    visible: bool
    ui_parent: Optional[str]
    editable: bool = True
    depth: int = 0
    prefix: str = ""


def build_child_map(items: Iterable[Tuple[str, Union[ConfigItem, MenuItem]]]) -> Dict[str, List[str]]:
    """Build parent → children mapping from items (both ConfigItems and MenuItems)."""
    children: Dict[str, List[str]] = {}
    material = list(items)
    item_by_key = {k: it for k, it in material}

    for key, item in material:
        parent = item.ui_parent
        if parent and parent in item_by_key:
            children.setdefault(parent, []).append(key)

    return children


def build_rows_from_items(
    items: Iterable[Tuple[str, ConfigItem]],
    store,
    *,
    roots: Optional[List[str]] = None,
) -> List[StoreRow]:
    """Build visible rows from a store for UI rendering with stable grouping/order.
    
    Now handles both ConfigItems and MenuItems. MenuItems are displayed as
    non-editable group headers.
    """
    rows: List[StoreRow] = []
    try:
        from scripts.installer.core.transform_registry import apply_outbound
    except Exception:

        def apply_outbound(k: str, v: Any) -> Any:  # type: ignore
            return v

    # Materialize input and build quick lookups
    material: List[Tuple[str, ConfigItem]] = list(items)
    item_by_key: Dict[str, Union[ConfigItem, MenuItem]] = {k: it for k, it in material}
    
    # Add MenuItems to the lookup
    if hasattr(store, 'get_visible_menu_items'):
        menu_items = store.get_visible_menu_items()
        for key, menu_item in menu_items.items():
            if key not in item_by_key:
                item_by_key[key] = menu_item
                material.append((key, menu_item))

    # Build parent → children map using shared logic
    children = build_child_map(material)
    top_level: List[str] = []

    for key, item in material:
        parent = item.ui_parent
        if not parent or parent not in item_by_key:
            top_level.append(key)

    def _sorted_keys(keys: List[str]) -> List[str]:
        try:
            def sort_key(k: str):
                item = item_by_key.get(k)
                if not item:
                    return (999999, k.lower())  # Items without sort_priority go last
                # Get sort_priority, defaulting to None if not present
                priority = getattr(item, 'sort_priority', None)
                label = (item.label or k).lower()
                # Sort by priority first (None values treated as 999999), then alphabetically
                return (priority if priority is not None else 999999, label)
            return sorted(keys, key=sort_key)
        except Exception:
            return keys

    def walk(k: str, depth: int, ancestors_last: List[bool]) -> None:
        it = item_by_key.get(k)
        if not it:
            return
        
        # Check visibility - could be MenuItem or ConfigItem
        if isinstance(it, MenuItem):
            vis = bool(store.is_menu_item_visible(k))
        else:
            vis = bool(store.is_item_visible(k))
        
        if not vis:
            return
        
        # Build tree prefix using ancestors' lastness
        prefix_parts: List[str] = []
        for is_last in ancestors_last[:-1]:
            prefix_parts.append("    " if is_last else "│   ")
        if ancestors_last:
            prefix_parts.append("└── " if ancestors_last[-1] else "├── ")
        prefix = "".join(prefix_parts)
        
        # MenuItems are non-editable group headers, ConfigItems are editable
        is_menu_item = isinstance(it, MenuItem)
        value_formatted = "" if is_menu_item else apply_outbound(k, it.get_value())
        choices = [] if is_menu_item else (it.choices if hasattr(it, 'choices') else [])
        
        rows.append(
            StoreRow(
                key=k,
                label=it.label or k,
                value_formatted=value_formatted,
                choices=choices,
                visible=vis,
                ui_parent=it.ui_parent,
                editable=not is_menu_item,  # MenuItems are not editable
                depth=depth,
                prefix=prefix,
            )
        )
        # Only consider visible children for connector correctness
        vis_children = []
        for ck in children.get(k, []):
            child_item = item_by_key.get(ck)
            if child_item:
                if isinstance(child_item, MenuItem):
                    if store.is_menu_item_visible(ck):
                        vis_children.append(ck)
                else:
                    if store.is_item_visible(ck):
                        vis_children.append(ck)
        ordered = _sorted_keys(vis_children)
        for idx, child_key in enumerate(ordered):
            is_last = idx == (len(ordered) - 1)
            walk(child_key, depth + 1, ancestors_last + [is_last])

    # Determine ordered top-level keys
    if roots:
        ordered_top = [k for k in roots if k in item_by_key]
    else:
        ordered_top = _sorted_keys(top_level)

    # Traverse top-level then their children; only render visible tops
    visible_tops = []
    for kk in ordered_top:
        item = item_by_key.get(kk)
        if item:
            if isinstance(item, MenuItem):
                if store.is_menu_item_visible(kk):
                    visible_tops.append(kk)
            else:
                if store.is_item_visible(kk):
                    visible_tops.append(kk)
    
    for idx, k in enumerate(visible_tops):
        is_last = idx == (len(visible_tops) - 1)
        walk(k, 0, [is_last])

    return rows
