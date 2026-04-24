#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Callable, Optional


def config_item_is_visible(config, key: str) -> bool:
    """Return visibility for a configuration item using store state."""
    item = config.get_item(key)
    return bool(item and item.is_visible)


@dataclass(frozen=True)
class _Gating:
    """Resolved visibility-gating inputs used during a single top-level check.

    Holds the final resolved values after merging explicit kwargs with ctx defaults,
    so recursive ancestor checks don't re-resolve them on every call.
    """

    orchestration_mode: object
    runtime_bin: str
    image_archive_path: Optional[str]
    get_value: Optional[Callable[[str], object]]
    docker_installed: Optional[bool]
    compose_available: Optional[bool]
    has_system_tweaks: bool


def _resolve_gating(
    ctx,
    *,
    orchestration_mode,
    runtime_bin: Optional[str],
    image_archive_path: Optional[str],
    get_value: Optional[Callable[[str], object]],
    docker_installed: Optional[bool],
    compose_available: Optional[bool],
    has_system_tweaks: Optional[bool],
) -> _Gating:
    """Merge explicit overrides with ctx defaults into a frozen _Gating struct."""
    return _Gating(
        orchestration_mode=orchestration_mode or getattr(ctx, "_orchestration_mode", None),
        runtime_bin=(runtime_bin or getattr(ctx, "_runtime_bin", None) or "").lower(),
        image_archive_path=image_archive_path or getattr(ctx, "image_archive_path", None),
        get_value=get_value if get_value is not None else getattr(ctx, "get_item_value", None),
        docker_installed=(
            docker_installed if docker_installed is not None else getattr(ctx, "_docker_installed", None)
        ),
        compose_available=(
            compose_available if compose_available is not None else getattr(ctx, "_compose_available", None)
        ),
        has_system_tweaks=(
            has_system_tweaks if has_system_tweaks is not None else getattr(ctx, "has_system_tweaks", True)
        ),
    )


def install_item_is_visible(
    ctx,
    key: str,
    item=None,
    *,
    orchestration_mode=None,
    runtime_bin: Optional[str] = None,
    image_archive_path: Optional[str] = None,
    get_value: Optional[Callable[[str], object]] = None,
    docker_installed: Optional[bool] = None,
    compose_available: Optional[bool] = None,
    has_system_tweaks: Optional[bool] = None,
) -> bool:
    """Return True if an installation item should be visible.

    Uses context defaults but allows explicit overrides for tests.
    """
    gating = _resolve_gating(
        ctx,
        orchestration_mode=orchestration_mode,
        runtime_bin=runtime_bin,
        image_archive_path=image_archive_path,
        get_value=get_value,
        docker_installed=docker_installed,
        compose_available=compose_available,
        has_system_tweaks=has_system_tweaks,
    )
    item = item or (ctx.items.get(key) if hasattr(ctx, "items") else None)
    if item is None:
        return False
    return _is_visible(ctx, key, item, gating)


def _is_visible(ctx, key: str, item, gating: _Gating) -> bool:
    """Pure visibility check using pre-resolved gating. Recurses on ui_parent."""
    meta = item.metadata or {}

    # Kubernetes hides docker/podman-gated items
    try:
        from scripts.malcolm_constants import OrchestrationFramework

        if gating.orchestration_mode == OrchestrationFramework.KUBERNETES:
            rt = meta.get("visible_when_runtime")
            if rt in ("docker", "podman"):
                return False
    except Exception:
        pass

    # hide when parent enabled (e.g., auto tweaks)
    vwp = meta.get("visible_when_parent_disabled")
    if vwp and callable(gating.get_value):
        try:
            if bool(gating.get_value(vwp)):
                return False
        except Exception:
            pass

    # Cascade visibility up the ui_parent chain: if an ancestor is invisible,
    # this item is invisible too. Prevents granular grandchildren from remaining
    # interactive when an ancestor group (e.g., autoTweaks) is enabled.
    parent_key = getattr(item, "ui_parent", None)
    parent_item = ctx.items.get(parent_key) if parent_key and hasattr(ctx, "items") else None
    if parent_item is not None and not _is_visible(ctx, parent_key, parent_item, gating):
        return False

    rt = meta.get("visible_when_runtime")
    if not rt:
        base_visible = not (key == _lazy_key_load_images() and not gating.image_archive_path)
    else:
        base_visible = (rt == "docker" and gating.runtime_bin.startswith("docker")) or (
            rt == "podman" and gating.runtime_bin.startswith("podman")
        )

    if not base_visible:
        return False

    # Additional tool-availability gating
    try:
        (
            KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD,
            KEY_INSTALLATION_ITEM_INSTALL_DOCKER_IF_MISSING,
            KEY_INSTALLATION_ITEM_DOCKER_EXTRA_USERS,
            KEY_INSTALLATION_ITEM_TRY_DOCKER_REPOSITORY,
            KEY_INSTALLATION_ITEM_TRY_DOCKER_CONVENIENCE_SCRIPT,
            KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD,
        ) = _lazy_docker_keys()
    except Exception:
        return True

    if gating.runtime_bin.startswith("docker"):
        if gating.docker_installed is True and key in (
            KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD,
            KEY_INSTALLATION_ITEM_INSTALL_DOCKER_IF_MISSING,
            KEY_INSTALLATION_ITEM_DOCKER_EXTRA_USERS,
            KEY_INSTALLATION_ITEM_TRY_DOCKER_REPOSITORY,
            KEY_INSTALLATION_ITEM_TRY_DOCKER_CONVENIENCE_SCRIPT,
        ):
            return False
        if gating.compose_available is True and key == KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD:
            return False

    if (key == _lazy_key_auto_system_tweaks()) and (not gating.has_system_tweaks):
        return False

    return True


def _lazy_key_load_images():
    from scripts.installer.configs.constants.installation_item_keys import (
        KEY_INSTALLATION_ITEM_LOAD_MALCOLM_IMAGES,
    )

    return KEY_INSTALLATION_ITEM_LOAD_MALCOLM_IMAGES


def _lazy_key_auto_system_tweaks():
    from scripts.installer.configs.constants.installation_item_keys import (
        KEY_INSTALLATION_ITEM_AUTO_TWEAKS,
    )

    return KEY_INSTALLATION_ITEM_AUTO_TWEAKS


def _lazy_docker_keys():
    from scripts.installer.configs.constants.installation_item_keys import (
        KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD,
        KEY_INSTALLATION_ITEM_DOCKER_EXTRA_USERS,
        KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD,
        KEY_INSTALLATION_ITEM_INSTALL_DOCKER_IF_MISSING,
        KEY_INSTALLATION_ITEM_TRY_DOCKER_CONVENIENCE_SCRIPT,
        KEY_INSTALLATION_ITEM_TRY_DOCKER_REPOSITORY,
    )

    return (
        KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD,
        KEY_INSTALLATION_ITEM_INSTALL_DOCKER_IF_MISSING,
        KEY_INSTALLATION_ITEM_DOCKER_EXTRA_USERS,
        KEY_INSTALLATION_ITEM_TRY_DOCKER_REPOSITORY,
        KEY_INSTALLATION_ITEM_TRY_DOCKER_CONVENIENCE_SCRIPT,
        KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD,
    )
