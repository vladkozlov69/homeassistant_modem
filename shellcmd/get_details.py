#!/usr/bin/env python
# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright (C) 2016 Aleksander Morgado <aleksander@aleksander.es>
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

