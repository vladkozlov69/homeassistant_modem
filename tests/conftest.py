# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Test setup for mm_modem unit tests.

Stubs native GI/Home Assistant dependencies when unavailable so package modules
and tests can be imported and run in isolation.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = []  # mark as package when needed
        sys.modules[name] = module
    return module


def _stub_gi() -> None:
    gi = _ensure_module("gi")
    gi.require_version = lambda *_args, **_kwargs: None

    repo = _ensure_module("gi.repository")
    gi.repository = repo

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, _name):
            return MagicMock()

        @classmethod
        def __getattr__(cls, _name):
            return MagicMock()

    def _make_repo_module(mod_name: str):
        mod = _ensure_module(f"gi.repository.{mod_name}")
        setattr(repo, mod_name, mod)

        def _getattr(name):
            value = MagicMock()
            setattr(mod, name, value)
            return value

        mod.__getattr__ = _getattr
        return mod

    for mod_name in ("Gio", "GLib", "ModemManager", "NM"):
        mod = _make_repo_module(mod_name)
        # common constructors/constants placeholders
        for attr in (
            "BusType",
            "DBusObjectManagerClientFlags",
            "MainLoop",
            "Client",
            "SmsProperties",
            "Manager",
            "SmsState",
            "ModemState",
            "CallProperties",
            "CallState",
        ):
            if not hasattr(mod, attr):
                setattr(mod, attr, MagicMock())


def _stub_homeassistant_if_missing() -> None:
    try:
        import homeassistant  # noqa: F401
        return
    except Exception:
        pass

    ha = _ensure_module("homeassistant")
    components = _ensure_module("homeassistant.components")
    helpers = _ensure_module("homeassistant.helpers")

    # homeassistant.const
    const = _ensure_module("homeassistant.const")
    const.EVENT_HOMEASSISTANT_STOP = "homeassistant_stop"
    const.CONF_NAME = "name"
    const.CONF_RECIPIENT = "recipient"

    # homeassistant.core
    core = _ensure_module("homeassistant.core")

    class Event:  # minimal placeholder
        def __init__(self, event_type=None, data=None, *args, **kwargs):
            self.event_type = event_type
            self.data = data or {}

    class EventBus:  # minimal placeholder for specs/mocks
        pass

    def callback(func):
        return func

    core.Event = Event
    core.EventBus = EventBus
    core.callback = callback

    # homeassistant.helpers.config_validation
    cv = _ensure_module("homeassistant.helpers.config_validation")

    def _string(value):
        if value is None:
            raise ValueError("string value is None")
        return str(value)

    cv.string = _string

    # homeassistant.helpers.discovery
    discovery = _ensure_module("homeassistant.helpers.discovery")
    async def async_load_platform(*_args, **_kwargs):
        return None
    discovery.async_load_platform = async_load_platform

    # homeassistant.helpers.entity
    entity = _ensure_module("homeassistant.helpers.entity")

    class Entity:
        hass = None

        @property
        def should_poll(self):
            return True

        def async_write_ha_state(self):
            return None

        def schedule_update_ha_state(self, force_refresh=False):
            return None

    entity.Entity = Entity

    # homeassistant.components.logbook
    logbook = _ensure_module("homeassistant.components.logbook")

    def async_log_entry(hass, name, message, domain, entity_id, context=None, **_kwargs):
        if hass is not None and getattr(hass, "bus", None) is not None:
            hass.bus.async_fire(
                "logbook_entry",
                {
                    "name": name,
                    "message": message,
                    "domain": domain,
                    "entity_id": entity_id,
                },
                context=context,
            )
        return None

    def log_entry(*_args, **_kwargs):
        return None

    logbook.async_log_entry = async_log_entry
    logbook.log_entry = log_entry

    # homeassistant.components.binary_sensor
    binary_sensor = _ensure_module("homeassistant.components.binary_sensor")
    class BinarySensorEntity(Entity):
        pass
    class BinarySensorDeviceClass:
        CONNECTIVITY = "connectivity"
    binary_sensor.BinarySensorEntity = BinarySensorEntity
    binary_sensor.BinarySensorDeviceClass = BinarySensorDeviceClass

    # homeassistant.components.notify
    notify = _ensure_module("homeassistant.components.notify")
    class _BaseSchema:
        def extend(self, schema):
            return schema
    class BaseNotificationService:
        pass
    notify.PLATFORM_SCHEMA = _BaseSchema()
    notify.ATTR_TARGET = "target"
    notify.BaseNotificationService = BaseNotificationService

    # homeassistant.components.sensor
    sensor = _ensure_module("homeassistant.components.sensor")
    class SensorEntity(Entity):
        pass
    sensor.SensorEntity = SensorEntity

    # homeassistant.util.dt
    from datetime import datetime, timezone
    _ensure_module("homeassistant.util")
    dt = _ensure_module("homeassistant.util.dt")
    dt.now = lambda: datetime.now(timezone.utc)


def _stub_voluptuous_if_missing() -> None:
    try:
        import voluptuous  # noqa: F401
        return
    except Exception:
        pass
    vol = _ensure_module("voluptuous")
    class _Marker:
        def __init__(self, key, *args, **kwargs):
            self.key = key
    def Required(key, *args, **kwargs):
        return _Marker(key)
    def Optional(key, *args, **kwargs):
        return _Marker(key)
    class Schema:
        def __init__(self, schema, *args, **kwargs):
            self.schema = schema
        def __call__(self, value):
            return value
    vol.Required = Required
    vol.Optional = Optional
    vol.Schema = Schema


_stub_gi()
_stub_voluptuous_if_missing()
_stub_homeassistant_if_missing()


integration_root = Path(__file__).resolve().parents[1]
if str(integration_root) not in sys.path:
    sys.path.insert(0, str(integration_root.parent))

# Ensure the package can be imported as `mm_modem` even when running from repo root.
spec = importlib.util.spec_from_file_location(
    "mm_modem",
    integration_root / "__init__.py",
    submodule_search_locations=[str(integration_root)],
)
module = importlib.util.module_from_spec(spec)
sys.modules["mm_modem"] = module
assert spec and spec.loader
spec.loader.exec_module(module)
