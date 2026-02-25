#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.

"""Dialog-based configuration menu using python3-dialog."""

import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from scripts.malcolm_common import (
    InstallerAskForString,
    InstallerChooseOne,
    InstallerDisplayMessage,
    UserInterfaceMode,
    DialogBackException,
    DialogCanceledException,
)
from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.configs.constants.constants import MAIN_MENU_ITEM_KEYS
from scripts.installer.ui.shared.menu_builder import ValueFormatter
from scripts.installer.ui.shared.store_view_model import build_rows_from_items, build_child_map
from scripts.installer.ui.shared.search_utils import format_search_results_text
from scripts.installer.ui.shared.prompt_utils import prompt_config_item_value
from scripts.installer.utils.exceptions import (
    ConfigValueValidationError,
    ConfigItemNotFoundError,
)

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.install_context import InstallContext


BACK_LABEL = "Back"


class DialogConfigurationMenu:
    def __init__(
        self,
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
        main_menu_keys: List[str],
        debug_mode: bool = False,
        ui_mode: UserInterfaceMode = UserInterfaceMode.InteractionDialog,
    ) -> None:
        self.mc = malcolm_config
        self.ctx = install_context
        self.main_menu_keys = main_menu_keys or MAIN_MENU_ITEM_KEYS
        self.debug_mode = debug_mode
        self.ui_mode = ui_mode
        # Build child map from both ConfigItems and MenuItems
        all_config_items = list(self.mc.get_all_config_items().items())
        all_menu_items = list(self.mc.get_visible_menu_items().items())
        combined_items = all_config_items + all_menu_items
        self.child_map: Dict[str, List[str]] = build_child_map(combined_items)
        # Track selected tag at each menu level for position restoration
        self.nav_stack: Dict[Optional[str], str] = {}

    def run(self) -> bool:
        try:
            return self._navigate(None)
        except (KeyboardInterrupt, DialogCanceledException):
            return False

    def _ordered_visible_children(self, parent_key: Optional[str]) -> List[str]:
        """Return visible children in a stable, view-model-driven order."""
        # Get direct children from child_map
        if parent_key is None:
            # Top level: show main menu items
            candidate_keys = self.main_menu_keys
        else:
            # Get direct children of the parent from child_map
            candidate_keys = self.child_map.get(parent_key, [])
        
        # Filter for visible items and build sortable list
        visible_items: List[Tuple[int, str, str]] = []  # (priority, label_lower, key)
        
        for key in candidate_keys:
            # Check if it's a ConfigItem or MenuItem
            item = self.mc.get_item(key)
            menu_item = self.mc.get_menu_item(key) if not item else None
            
            if not item and not menu_item:
                continue
            
            # Check visibility
            if menu_item:
                if not self.mc.is_menu_item_visible(key):
                    continue
                target_item = menu_item
            else:
                if not self.mc.is_item_visible(key):
                    continue
                target_item = item
            
            # Verify parent relationship
            if target_item.ui_parent != parent_key:
                continue
            
            # Get sort priority and label for sorting
            priority = getattr(target_item, 'sort_priority', None)
            priority_value = priority if priority is not None else 999999
            label_lower = (target_item.label or key).lower()
            
            visible_items.append((priority_value, label_lower, key))
        
        # Sort by priority first, then alphabetically by label
        visible_items.sort()
        
        # Return just the keys in sorted order
        return [key for _, _, key in visible_items]

    def _make_choice_list(
        self, keys: List[str], include_actions: bool, parent_key: Optional[str] = None, selected_tag: Optional[str] = None
    ) -> Tuple[List[Tuple[str, str, bool]], Dict[str, str]]:
        choices: List[Tuple[str, str, bool]] = []
        tag_map: Dict[str, str] = {}
        has_default_selection = False
        
        for key in keys:
            # Check if it's a MenuItem or ConfigItem
            item = self.mc.get_item(key)
            menu_item = self.mc.get_menu_item(key) if not item else None
            
            if not item and not menu_item:
                continue
            
            if menu_item:
                label = menu_item.label or key
                if not label.endswith(" Settings"):
                    label = f"{label} Settings"
                tag = label
                is_selected = (selected_tag is not None and tag == selected_tag and not has_default_selection)
                if is_selected:
                    has_default_selection = True
                tag_map[tag] = f"GROUP:{key}"
                choices.append((tag, "", is_selected))
            else:
                # ConfigItem - display with value
                value_display = ValueFormatter.format_config_value(item.label, item.get_value())
                desc = value_display if isinstance(value_display, str) else str(value_display)
                tag = item.label or key
                is_selected = (selected_tag is not None and tag == selected_tag and not has_default_selection)
                if is_selected:
                    has_default_selection = True
                tag_map[tag] = f"KEY:{key}"
                choices.append((tag, desc, is_selected))

        if include_actions:
            # add a non-selectable-looking separator label before actions
            sep_tag = " ──────── Actions ────────"
            choices.append((sep_tag, "", False))
            tag_map[sep_tag] = "SEP"
            action_items = [
                ("Save and Continue", "", False),
                ("Where Is…? (search)", "", False),
                ("Exit Installer", "", False),
            ]
            choices.extend(action_items)
            tag_map.update(
                {
                    "Save and Continue": "ACTION:save",
                    "Where Is…? (search)": "ACTION:search",
                    "Exit Installer": "ACTION:exit",
                }
            )
        return choices, tag_map

    def _navigate(self, parent_key: Optional[str]) -> bool:
        while True:
            saved_tag = self.nav_stack.get(parent_key)

            keys = self._ordered_visible_children(parent_key)
            include_actions = parent_key is None
            choices, tag_map = self._make_choice_list(keys, include_actions, parent_key, selected_tag=saved_tag)

            if not choices:
                return True if parent_key is None else True

            try:
                if parent_key is None:
                    label = "Malcolm Configuration"
                else:
                    parent_item = self.mc.get_item(parent_key)
                    parent_menu = self.mc.get_menu_item(parent_key) if not parent_item else None
                    label = (parent_item.label if parent_item else parent_menu.label if parent_menu else parent_key)
                    if parent_menu and not label.endswith(" Settings"):
                        label = f"{label} Settings"
                prompt = re.sub(r'^(?:Enable |Use )| Mode$', '', label) + ": select an item to configure"
                result = InstallerChooseOne(
                    prompt,
                    choices=choices,
                    uiMode=self.ui_mode,
                    extraLabel=(None if parent_key is None else BACK_LABEL),
                )
            except DialogBackException:
                return True
            except DialogCanceledException:
                return False

            selected_tag = result
            mapped = tag_map.get(result, "")
            
            if mapped == "SEP":
                continue
            if mapped == "ACTION:exit":
                return False
            if mapped == "ACTION:save":
                return True
            if mapped == "ACTION:search":
                self._handle_search()
                continue

            if mapped.startswith("KEY:"):
                key = mapped.split(":", 1)[1]
                self.nav_stack[parent_key] = selected_tag
                self._prompt_for_item_value(key)
                continue
            elif mapped.startswith("GROUP:"):
                grp_key = mapped.split(":", 1)[1]
                self.nav_stack[parent_key] = selected_tag
                menu_item = self.mc.get_menu_item(grp_key)
                if menu_item:
                    if not self._navigate(grp_key):
                        return False
                    continue
                if not self._navigate(grp_key):
                    return False
                continue
            else:
                menu_item = self.mc.get_menu_item(result)
                if menu_item:
                    self.nav_stack[parent_key] = selected_tag
                    if not self._navigate(result):
                        return False
                    continue
                self.nav_stack[parent_key] = selected_tag
                key = result
                self._prompt_for_item_value(key)
            continue

    def _prompt_for_item_value(self, key: str) -> None:
        item = self.mc.get_item(key)
        if not item:
            return

        while True:
            try:
                new_value = prompt_config_item_value(
                    ui_mode=self.ui_mode,
                    config_item=item,
                    back_label=BACK_LABEL,
                    show_preamble=True,
                )
            except (DialogBackException, DialogCanceledException):
                return

            if new_value is None:
                return

            try:
                self.mc.set_value(key, new_value)
            except ConfigValueValidationError as e:
                InstallerDisplayMessage(str(e), uiMode=self.ui_mode)
                # let user try again
                continue
            except ConfigItemNotFoundError as e:
                InstallerLogger.error(str(e))
                return

            return

    def _flatten_visible_keys(self) -> List[str]:
        """Flatten visible items using the view model for consistent order."""
        rows = build_rows_from_items(self.mc.get_all_config_items().items(), self.mc, roots=self.main_menu_keys)
        return [r.key for r in rows if r.visible]

    def _handle_search(self) -> None:
        try:
            term = InstallerAskForString("Enter search term:", default="", uiMode=self.ui_mode)
        except (DialogBackException, DialogCanceledException):
            return
        if not term:
            return

        displayed_keys = self._flatten_visible_keys()
        text = format_search_results_text(
            self.mc,
            term,
            displayed_keys,
            debug_mode=self.debug_mode,
            include_numbers=False,
            colorize=False,
        )
        InstallerDisplayMessage(text, uiMode=self.ui_mode)
