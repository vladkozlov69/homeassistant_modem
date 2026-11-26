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

    # Process input arguments
    if len(sys.argv) != 3:
        sys.stderr.write('error: wrong number of arguments\n')
        sys.stdout.write('usage: sms-python <NUMBER> <TEXT>\n')
        sys.exit(1)

    # Prepare SMS properties
    sms_properties = ModemManager.SmsProperties.new ()
    sms_properties.set_number(sys.argv[1])
    sms_properties.set_text(sys.argv[2])

    # Connection to ModemManager
    connection = Gio.bus_get_sync (Gio.BusType.SYSTEM, None)
    manager = ModemManager.Manager.new_sync (connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
    if manager.get_name_owner() is None:
        sys.stderr.write('ModemManager not found in bus')
        sys.exit(2)

    # Iterate modems and send SMS with each
    for obj in manager.get_objects():
        messaging = obj.get_modem_messaging()
        print(messaging)
        sms = messaging.create_sync(sms_properties)
        print(sms)
        sms.send_sync()
        print('%s: sms sent' % messaging.get_object_path()) 
