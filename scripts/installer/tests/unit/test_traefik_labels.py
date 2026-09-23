#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compose label rendering tests for Traefik-related config."""

import os
import shutil
import tempfile
import unittest

from scripts.installer.actions.shared import update_compose_files
from scripts.installer.configs.constants.configuration_item_keys import (
    KEY_CONFIG_ITEM_TRAEFIK_LABELS,
    KEY_CONFIG_ITEM_TRAEFIK_HOST,
    KEY_CONFIG_ITEM_TRAEFIK_OPENSEARCH_HOST,
    KEY_CONFIG_ITEM_TRAEFIK_ENTRYPOINT,
    KEY_CONFIG_ITEM_TRAEFIK_RESOLVER,
    KEY_CONFIG_ITEM_EXPOSE_OPENSEARCH,
    KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
    KEY_CONFIG_ITEM_OPEN_PORTS,
)
from scripts.installer.configs.constants.constants import (
    TRAEFIK_ENABLE,
    LABEL_MALCOLM_RULE,
    LABEL_MALCOLM_ENTRYPOINTS,
    LABEL_MALCOLM_CERTRESOLVER,
    LABEL_MALCOLM_SERVICE,
    LABEL_MALCOLM_SERVICE_PORT,
    LABEL_OS_RULE,
    LABEL_OS_ENTRYPOINTS,
    LABEL_OS_CERTRESOLVER,
    LABEL_OS_SERVICE,
    LABEL_OS_SERVICE_PORT,
    SERVICE_NAME_MALCOLM,
    SERVICE_NAME_OSMALCOLM,
    SERVICE_PORT_MALCOLM,
    SERVICE_PORT_OSMALCOLM,
)
from scripts.installer.configs.constants.enums import OpenPortsChoices
from scripts.installer.core.install_context import InstallContext
from scripts.installer.core.malcolm_config import MalcolmConfig
from scripts.installer.tests.mock.test_framework import MockPlatform
from scripts.malcolm_common import YAMLDynamic
from scripts.malcolm_constants import DatabaseMode, DATABASE_MODE_LABELS


def _write_compose(path, data):
    if yaml_imported := YAMLDynamic():
        yaml = yaml_imported.YAML(typ="safe", pure=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
    else:
        raise RuntimeError("Could not dynamically import YAML library")


def _read_compose(path):
    if yaml_imported := YAMLDynamic():
        yaml = yaml_imported.YAML(typ="safe", pure=True)
        with open(path, "r", encoding="utf-8") as f:
            return yaml.load(f)
    else:
        raise RuntimeError("Could not dynamically import YAML library")


class TestTraefikLabels(unittest.TestCase):
    def setUp(self):
        self.cfg = MalcolmConfig()
        self.tmpdir = tempfile.mkdtemp()
        self.compose_path = os.path.join(self.tmpdir, "docker-compose.yml")
        _write_compose(
            self.compose_path,
            {"version": "3.7", "services": {"nginx-proxy": {"image": "nginx:latest", "labels": {}}}},
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _render_labels(self):
        ok = update_compose_files(self.cfg, self.tmpdir, None, MockPlatform(), InstallContext())
        self.assertTrue(ok)
        return _read_compose(self.compose_path)["services"]["nginx-proxy"].get("labels", {})

    def _set_common_traefik_inputs(self):
        self.cfg.set_value(KEY_CONFIG_ITEM_OPEN_PORTS, OpenPortsChoices.CUSTOMIZE.value)
        self.cfg.set_value(KEY_CONFIG_ITEM_TRAEFIK_LABELS, True)
        self.cfg.set_value(KEY_CONFIG_ITEM_TRAEFIK_HOST, "malcolm.example.org")
        self.cfg.set_value(KEY_CONFIG_ITEM_TRAEFIK_ENTRYPOINT, "websecure")
        self.cfg.set_value(KEY_CONFIG_ITEM_TRAEFIK_RESOLVER, "myresolver")

    def test_labels_enabled_renders_malcolm_labels(self):
        self._set_common_traefik_inputs()
        labels = self._render_labels()

        self.assertTrue(labels.get(TRAEFIK_ENABLE, False))
        self.assertEqual(labels.get(LABEL_MALCOLM_RULE), "Host(`malcolm.example.org`)")
        self.assertEqual(labels.get(LABEL_MALCOLM_ENTRYPOINTS), "websecure")
        self.assertEqual(labels.get(LABEL_MALCOLM_CERTRESOLVER), "myresolver")
        self.assertEqual(labels.get(LABEL_MALCOLM_SERVICE), SERVICE_NAME_MALCOLM)
        self.assertEqual(labels.get(LABEL_MALCOLM_SERVICE_PORT), SERVICE_PORT_MALCOLM)

    def test_labels_disabled_clears_known_traefik_keys(self):
        data = _read_compose(self.compose_path)
        data["services"]["nginx-proxy"]["labels"] = {
            LABEL_MALCOLM_RULE: "Host(`old.example`)",
            LABEL_OS_RULE: "Host(`old-os.example`)",
        }
        _write_compose(self.compose_path, data)

        self.cfg.set_value(KEY_CONFIG_ITEM_TRAEFIK_LABELS, False)
        labels = self._render_labels()

        self.assertFalse(labels.get(TRAEFIK_ENABLE, True))
        self.assertNotIn(LABEL_MALCOLM_RULE, labels)
        self.assertNotIn(LABEL_OS_RULE, labels)

    def test_os_labels_render_only_for_local_and_exposed(self):
        self._set_common_traefik_inputs()
        self.cfg.set_value(KEY_CONFIG_ITEM_TRAEFIK_OPENSEARCH_HOST, "os.malcolm.example.org")
        self.cfg.set_value(KEY_CONFIG_ITEM_EXPOSE_OPENSEARCH, True)
        self.cfg.set_value(
            KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
            DATABASE_MODE_LABELS[DatabaseMode.OpenSearchLocal],
        )

        labels = self._render_labels()
        self.assertEqual(labels.get(LABEL_OS_RULE), "Host(`os.malcolm.example.org`)")
        self.assertEqual(labels.get(LABEL_OS_ENTRYPOINTS), "websecure")
        self.assertEqual(labels.get(LABEL_OS_CERTRESOLVER), "myresolver")
        self.assertEqual(labels.get(LABEL_OS_SERVICE), SERVICE_NAME_OSMALCOLM)
        self.assertEqual(labels.get(LABEL_OS_SERVICE_PORT), SERVICE_PORT_OSMALCOLM)

        self.cfg.set_value(
            KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
            DATABASE_MODE_LABELS[DatabaseMode.OpenSearchRemote],
        )
        labels = self._render_labels()
        self.assertNotIn(LABEL_OS_RULE, labels)

        self.cfg.set_value(
            KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
            DATABASE_MODE_LABELS[DatabaseMode.OpenSearchLocal],
        )
        self.cfg.set_value(KEY_CONFIG_ITEM_EXPOSE_OPENSEARCH, False)
        labels = self._render_labels()
        self.assertNotIn(LABEL_OS_RULE, labels)


if __name__ == "__main__":
    unittest.main()
