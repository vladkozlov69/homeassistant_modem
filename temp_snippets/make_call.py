import sys, signal, gi

# from gi.repository import GLib

import time

import threading

gi.require_version('ModemManager', '1.0')
from gi.repository import GLib, GObject, Gio, ModemManager

class Caca(Gio.Cancellable):
    _cancel = None


class Dialer:

    _voice = None
    _call = None

    _main_loop = GLib.MainLoop()


    def on_call_created(self, source_object, res, *user_data):
        print('>> on_call_created', source_object, res)
        self._call = source_object.create_call_finish(res)
        self.initiate_call(self._call)

    def on_ready(self, source_object, res, *user_data):
        print('>> call initiated', source_object, res)
        print(source_object.get_path(), source_object.get_state())
        time.sleep(15)
        # source_object.hangup_sync()
        self._main_loop.quit()

    def initiate_call(self, call):
        print(">> initiate_call")
        call.start(cancellable=None, callback=self.on_ready)
        print("<< initiate_call")

    def poll_call(call):
        print(call.get_state())

    def on_object_added(self, manager, obj):
        modem = obj.get_modem()
        print('[ModemWatcher] %s (%s) modem managed by ModemManager [%s]: %s' %
              (modem.get_manufacturer(),
               modem.get_model(),
               modem.get_equipment_identifier(),
               obj.get_object_path()))
        if modem.get_state() == ModemManager.ModemState.FAILED:
            print('[ModemWatcher,%s] ignoring failed modem' %
                  modem_index(obj.get_object_path()))

    """
    Object removed
    """
    def on_object_removed(self, manager, obj):
        print('[ModemWatcher] modem unmanaged by ModemManager: %s' %
              obj.get_object_path())



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

        manager.connect('object-added', self.on_object_added)

        manager.connect('object-removed', self.on_object_removed)

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
                self._call = self._voice.create_call(call_properties, Caca(), self.on_call_created, None)
                # self._call = self._voice.create_call(call_properties, None)
                # print(self._call)

                # t = threading.Thread(target=self.initiate_call, args=( self._call,))
                # t.start()

                # time.sleep(1)
                self._main_loop.run()

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
        # self._call.hangup_sync()
        print(self._call.get_state())
        self._voice.delete_call_sync(self._call.get_path(), None)
        for callvar in self._voice.list_calls_sync():
            print('cleanup:', callvar.get_path())
            # call.hangup_sync()
            print(callvar.get_state())
            self._voice.delete_call_sync(callvar.get_path(), None)



if __name__ == "__main__":
    dialer = Dialer()
    # threading.Thread(target=dialer.dial).start()
    dialer.dial()

    # main_loop = GLib.MainLoop()

    # try:
    #     main_loop.run()
    # except KeyboardInterrupt:
    #     pass



    dialer.cleanup()
