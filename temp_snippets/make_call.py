import sys, signal, gi

# from gi.repository import GLib

import time

import threading

gi.require_version('ModemManager', '1.0')
from gi.repository import GLib, GObject, Gio, ModemManager

class Dialer:

    _voice = None
    _call = None

    def on_ready(source_object, res, *user_data):
        print('>> on_ready')

    def initiate_call(self, call):
        print(">> initiate_call")
        call.start(cancellable=None, callback=self.on_ready)
        print("<< initiate_call")

    def poll_call(call):
        print(call.get_state())


    def dial(self):
# Prepare call properties
        call_properties = ModemManager.CallProperties.new()
        call_properties.set_number('067683837')


        # Connection to ModemManager
        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync(connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
        if manager.get_name_owner() is None:
            sys.stderr.write('ModemManager not found in bus')
            sys.exit(2)

        print(manager.get_version())

        # self._voice = ModemManager.GdbusModemVoiceProxy.new_sync(connection, Gio.DBusProxyFlags.DO_NOT_AUTO_START, None, "/org/freedesktop/ModemManager1/Modem/0", None)

        # p = GLib.Variant('s','number=067683837')

        # call = self._voice.create_call_sync(p, None)


        for obj in manager.get_objects():
            print(obj)
            # get instance of ModemManager.ModemVoice
            self._voice = obj.get_modem_voice()
            print(self._voice.get_path())

            try:
                self._call = self._voice.create_call_sync(call_properties, None)
                print(self._call)

                t = threading.Thread(target=self.initiate_call, args=( self._call,))
                t.start()

                time.sleep(1)

            except Exception as e:
                raise e
            finally:
                print(">> finally")
                for callvar in self._voice.list_calls_sync():
                    print('calls:', callvar.get_path())
            #     # call.hangup()
            #     # voice.delete_call_sync(call.get_path(), None)




    def cleanup(self):
        print('cleanup current call:', self._call.get_path())
        self._call.hangup()
        print(self._call.get_state())
        self._voice.delete_call_sync(self._call.get_path(), None)
        for callvar in self._voice.list_calls_sync():
            print('cleanup:', callvar.get_path())
            # call.hangup_sync()
            print(callvar.get_state())
            self._voice.delete_call_sync(callvar.get_path(), None)



if __name__ == "__main__":
    dialer = Dialer()
    threading.Thread(target=dialer.dial).start()
    for x in range(10):
        print("wait")
        time.sleep(1)
    dialer.cleanup()
