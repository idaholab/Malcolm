#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Linux-specific tweak aggregator used by the platform installer.

This module provides Linux-specific tweak implementations and a single
apply_all() entry point used by LinuxInstaller.
"""

import os
import pathlib
import re
import tempfile
from typing import Optional, Sequence

from scripts.installer.configs.constants.enums import InstallerResult
from scripts.malcolm_utils import file_contents, which
from scripts.malcolm_common import SYSTEM_INFO

from scripts.installer.utils import InstallerLogger as logger


def _should_apply_tweak(ctx, tweak_id: str) -> bool:
    """Apply when auto_tweaks is on or the tweak is explicitly selected in ctx."""
    if ctx.auto_tweaks:
        return True
    try:
        return bool(ctx.get_item_value(tweak_id))
    except Exception:
        return False


def _read_existing_lines(path: str) -> list:
    """Read `path` and return stripped non-empty lines, or [] if missing/unreadable."""
    try:
        if os.path.exists(path) and (existing := file_contents(path)):
            if not isinstance(existing, str):
                return []
            return [ln.strip() for ln in existing.splitlines() if ln.strip()]
    except (PermissionError, OSError):
        logger.warning(f"Cannot read {path}, assuming it needs to be written")
    return []


def _write_managed_file(
    path: str,
    desired_lines: Sequence[str],
    platform,
    *,
    parent_dir: Optional[str] = None,
) -> tuple[bool, str]:
    """Atomically write `desired_lines` to `path` via tempfile + privileged cp.

    Returns (wrote_ok, message). Ensures parent_dir exists (if provided), skips
    when content already matches, and chmods 0o644 after copy.
    """
    if parent_dir:
        try:
            pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return False, f"No permission to create {parent_dir}"

    if _read_existing_lines(path) == [ln.strip() for ln in desired_lines if ln.strip()]:
        return True, f"Already configured: {path}"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.writelines(f"{line}\n" for line in desired_lines)
            tmp_path = tmp.name
        err, out = platform.run_process(["cp", tmp_path, path])
        if err != 0:
            return False, f"Failed to write {path}: {' '.join(out)}"
        if os.path.exists(path):
            try:
                os.chmod(path, 0o644)
            except (PermissionError, OSError) as e:
                logger.warning(f"Could not chmod {path}: {e}")
        return True, f"Wrote {path}"
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {tmp_path}: {e}")


def apply_sysctl(malcolm_config, config_dir: str, platform, ctx) -> tuple[InstallerResult, str]:
    """Apply sysctl tweaks"""
    SYSCTL_SETTINGS = [
        ("fs.file-max", "2097152"),
        ("fs.inotify.max_user_watches", "131072"),
        ("fs.inotify.max_queued_events", "131072"),
        ("fs.inotify.max_user_instances", "512"),
        ("vm.max_map_count", "524288"),
        ("vm.swappiness", "1"),
        ("vm.dirty_background_ratio", "5"),
        ("vm.dirty_ratio", "10"),
        ("vm.overcommit_memory", "1"),
        ("net.core.somaxconn", "65535"),
        ("net.ipv4.tcp_retries2", "5"),
    ]

    def _sysctl_toggle_id(setting_name: str) -> str:
        return f"sysctl_{setting_name.split('.')[-1].replace('-', '_')}"

    def _write_to_sysctl_conf(setting_name: str, setting_value: str) -> bool:
        path = '/etc/sysctl.d/99-sysctl-performance.conf' if os.path.isdir('/etc/sysctl.d') else '/etc/sysctl.conf'
        prefix = f"{setting_name}="
        desired_line = f"{prefix}{setting_value}"
        try:
            existing_lines = _read_existing_lines(path)
            if desired_line in existing_lines:
                return True
            filtered = [ln for ln in existing_lines if not ln.startswith(prefix)]
            filtered.append(desired_line)
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                    tmp.writelines(f'{s}\n' for s in filtered)
                    tmp_path = tmp.name
                err, out = platform.run_process(["cp", tmp_path, path])
                if err == 0 and os.path.exists(path):
                    try:
                        os.chmod(path, 0o644)
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Could not chmod {path}: {e}")
                return err == 0
            finally:
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except OSError as e:
                        logger.warning(f"Failed to cleanup temp file {tmp_path}: {e}")
        except Exception as e:
            logger.error(f"Error applying sysctl settings: {e}")
            return False

    group_selected = _should_apply_tweak(ctx, "sysctl")
    any_selected = group_selected or any(_should_apply_tweak(ctx, _sysctl_toggle_id(name)) for name, _ in SYSCTL_SETTINGS)
    if not any_selected:
        return InstallerResult.SKIPPED, "No sysctl tweaks selected"

    successes = 0
    for setting_name, setting_value in SYSCTL_SETTINGS:
        if not (group_selected or _should_apply_tweak(ctx, _sysctl_toggle_id(setting_name))):
            successes += 1
            continue
        if platform.is_dry_run():
            logger.info(f"Dry run: would set {setting_name}={setting_value}")
            successes += 1
            continue
        if _write_to_sysctl_conf(setting_name, setting_value):
            logger.info(f"Applied {setting_name}={setting_value}")
            successes += 1
        else:
            logger.error(f"Failed to apply {setting_name}={setting_value}")

    if platform.is_dry_run():
        return InstallerResult.SKIPPED, "Dry run: would apply sysctl settings"
    return (
        (InstallerResult.SUCCESS, "Applied sysctl settings")
        if successes == len(SYSCTL_SETTINGS)
        else (InstallerResult.FAILURE, "Some sysctl settings failed")
    )


def apply_security_limits(malcolm_config, config_dir: str, platform, ctx) -> tuple[InstallerResult, str]:
    if not _should_apply_tweak(ctx, "security_limits"):
        return InstallerResult.SKIPPED, "Security limits not selected"

    limits_dir = "/etc/security/limits.d"
    limits_file = os.path.join(limits_dir, "99-malcolm.conf")
    desired_content = [
        "# Malcolm file and memory limits",
        "* soft nofile 65535",
        "* hard nofile 65535",
        "* soft memlock unlimited",
        "* hard memlock unlimited",
        "* soft nproc 262144",
        "* hard nproc 524288",
    ]

    if platform.is_dry_run():
        logger.info(f"Dry run: would write {limits_file} with security limits")
        return InstallerResult.SKIPPED, "Security limits skipped (dry run)"

    try:
        ok, msg = _write_managed_file(limits_file, desired_content, platform, parent_dir=limits_dir)
    except Exception as e:
        logger.error(f"Error applying security limits: {e}")
        return InstallerResult.FAILURE, "Security limits exception"
    if ok:
        logger.info(msg)
        return InstallerResult.SUCCESS, "Security limits applied"
    if "No permission" in msg:
        logger.warning(msg)
        return InstallerResult.SKIPPED, "Security limits skipped (no permissions)"
    logger.error(msg)
    return InstallerResult.FAILURE, "Security limits failed"


def apply_systemd_limits(malcolm_config, config_dir: str, platform, ctx) -> tuple[InstallerResult, str]:
    if not _should_apply_tweak(ctx, "systemd_limits"):
        return InstallerResult.SKIPPED, "Systemd limits not selected"

    if SYSTEM_INFO["distro"] not in ["centos"] and SYSTEM_INFO["codename"] not in ["core"]:
        logger.info(f"Skipping systemd limits (not applicable for {SYSTEM_INFO['distro']} {SYSTEM_INFO['distro']})")
        return InstallerResult.SKIPPED, "Not applicable"

    systemd_dir = "/etc/systemd/system.conf.d"
    limits_file = os.path.join(systemd_dir, "99-malcolm.conf")
    desired_content = [
        "[Manager]" "DefaultLimitNOFILE=65535:65535",
        "DefaultLimitMEMLOCK=infinity",
    ]

    if platform.is_dry_run():
        logger.info(f"Dry run: would write {limits_file} with systemd limits")
        return InstallerResult.SKIPPED, "Systemd limits skipped (dry run)"

    try:
        ok, msg = _write_managed_file(limits_file, desired_content, platform, parent_dir=systemd_dir)
    except Exception as e:
        logger.error(f"Error applying systemd limits: {e}")
        return InstallerResult.FAILURE, "Systemd limits exception"
    if ok:
        logger.info(msg)
        return InstallerResult.SUCCESS, "Systemd limits applied"
    if "No permission" in msg:
        logger.warning(msg)
        return InstallerResult.SKIPPED, "Systemd limits skipped (no permissions)"
    logger.error(msg)
    return InstallerResult.FAILURE, "Systemd limits failed"


def apply_grub_cgroup(
    malcolm_config,
    config_dir: str,
    platform,
    ctx,
    grub_file="/etc/default/grub",
    params=None,
    backup=True,
) -> tuple[InstallerResult, str]:
    if not _should_apply_tweak(ctx, "grub_cgroup"):
        logger.info("cgroup kernel parameters tweak not selected, skipping.")
        return InstallerResult.SKIPPED, "cgroup kernel parameters not selected"

    if params is None:
        params = [
            "systemd.unified_cgroup_hierarchy=1",
            "cgroup_enable=memory",
            "swapaccount=1",
            "cgroup.memory=nokmem",
        ]

    def system_uses_systemd_boot():
        # systemd-boot uses kernelstub, installs loader entries in /boot/loader/entries, and (usually) has /boot/loader/loader.conf
        return (
            which("kernelstub") and os.path.isdir("/boot/loader/entries") and os.path.isfile("/boot/loader/loader.conf")
        )

    def system_uses_bls():
        # BLS-enabled if both grubby and /boot/loader/entries exist, and not disabled in /etc/default/grub
        if which("grubby") and os.path.isdir("/boot/loader/entries"):
            try:
                with open("/etc/default/grub", "r") as f:
                    for line in f:
                        if "GRUB_ENABLE_BLSCFG" in line and "false" in line.lower():
                            return False
                return True
            except FileNotFoundError:
                return True
        return False

    def modify_line(varname, content):
        match = re.search(rf'^{varname}="(.*?)"', content, re.MULTILINE)
        if match:
            existing = match.group(1).split()
            new_params = [p for p in params if p not in existing]
            if not new_params:
                return content, []
            updated = " ".join(existing + new_params)
            content = content[: match.start()] + f'{varname}="{updated}"' + content[match.end() :]
            return content, new_params
        else:
            # variable not found, append at the end
            line = f'\n{varname}="' + " ".join(params) + '"\n'
            return content + line, params

    try:
        if platform.is_dry_run():
            logger.info(f"Dry run: would update cgroup kernel parameters parameters in {grub_file}")
            return InstallerResult.SKIPPED, "cgroup kernel parameters skipped (dry run)"

        if system_uses_systemd_boot():
            err, out = platform.run_process(['kernelstub', '-a', ' '.join(params)])
            if err == 0:
                logger.info("Applied new kernel parameters with kernelstub")
                return InstallerResult.SUCCESS, "cgroup kernel parameters applied"
            logger.error(f"Failed to apply kernel parameters with kernelstub: {' '.join(out)}")
            return InstallerResult.FAILURE, "cgroup kernel parameters failed"

        elif system_uses_bls():
            err, out = platform.run_process(['grubby', '--update-kernel=ALL', f"--args={' '.join(params)}"])
            if err == 0:
                logger.info("Applied new kernel parameters with grubby")
                return InstallerResult.SUCCESS, "cgroup kernel parameters applied"
            logger.error(f"Failed to apply kernel parameters with grubby: {' '.join(out)}")
            return InstallerResult.FAILURE, "cgroup kernel parameters failed"

        elif os.path.exists(grub_file):
            with open(grub_file, "r", encoding="utf-8") as f:
                orig_content = f.read()

            # prefer GRUB_CMDLINE_LINUX, fallback to DEFAULT
            if re.search(r"^GRUB_CMDLINE_LINUX=", orig_content, re.MULTILINE):
                varname = "GRUB_CMDLINE_LINUX"
            elif re.search(r"^GRUB_CMDLINE_LINUX_DEFAULT=", orig_content, re.MULTILINE):
                varname = "GRUB_CMDLINE_LINUX_DEFAULT"
            else:
                varname = "GRUB_CMDLINE_LINUX"
            new_content, added = modify_line(varname, orig_content)

            if added:
                if backup:
                    try:
                        with open(f"{grub_file}.bak", "w", encoding="utf-8") as f:
                            f.write(orig_content)
                    except OSError as e:
                        logger.warning(f"Failed to create backup of {grub_file}: {e}")
                with open(grub_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                try:
                    os.chmod(grub_file, 0o644)
                except Exception:
                    pass

                if which('update-grub'):
                    err, out = platform.run_process(['update-grub'])
                elif which('update-grub2'):
                    err, out = platform.run_process(['update-grub2'])
                elif which('grub2-mkconfig') and os.path.isfile('/boot/grub2/grub.cfg'):
                    err, out = platform.run_process(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'])
                else:
                    err = 0
                    logger.warning(
                        f"{grub_file} has been modified, consult your distribution's documentation generate new grub config file"
                    )

                if err == 0:
                    logger.info(f"Applied new kernel parameters to {grub_file}")
                    return InstallerResult.SUCCESS, "cgroup kernel parameters applied"
                logger.error(f"Failed to apply cgroup kernel parameters to {grub_file}: {' '.join(out)}")
                return InstallerResult.FAILURE, "cgroup kernel parameters failed"
            else:
                logger.info(f"no changes needed in GRUB config file {grub_file}")
                return InstallerResult.SKIPPED, "no changes needed in GRUB config file"

        else:
            logger.info(f"GRUB config file {grub_file} does not exist, skipping")
            return InstallerResult.SKIPPED, "GRUB config file missing"

    except Exception as e:
        logger.error(f"Error applying cgroup kernel parameters: {e}")
        return InstallerResult.FAILURE, "cgroup kernel parameters exception"


def apply_all(malcolm_config, config_dir: str, platform, ctx) -> tuple[InstallerResult, str]:
    if not platform.should_run_install_steps():
        return InstallerResult.SKIPPED, "Tweaks skipped (non-install control flow)"
    for func in (apply_sysctl, apply_security_limits, apply_systemd_limits, apply_grub_cgroup):
        status, _ = func(malcolm_config, config_dir, platform, ctx)
        if status == InstallerResult.FAILURE:
            return status, "A Linux tweak failed"
    return InstallerResult.SUCCESS, "All Linux tweaks applied"
