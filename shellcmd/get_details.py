#!/usr/bin/env python
# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
#
# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

#

import sys, signal, gi

gi.require_version('ModemManager', '1.0')
from gi.repository import GLib, GObject, Gio, ModemManager

if __name__ == "__main__":

    # Connection to ModemManager
    connection = Gio.bus_get_sync (Gio.BusType.SYSTEM, None)
    manager = ModemManager.Manager.new_sync (connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
    if manager.get_name_owner() is None:
        sys.stderr.write('ModemManager not found in bus')
        sys.exit(2)

    # Iterate modems and send SMS with each
    for obj in manager.get_objects():
        modem3gpp = obj.get_modem3gpp()
        print(modem3gpp)
        print(modem3gpp.get_operator_name())

