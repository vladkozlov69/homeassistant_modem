import sys, signal, gi, time, threading

gi.require_version('ModemManager', '1.0')
from gi.repository import GLib, GObject, Gio, ModemManager


class Dialer:

    def on_call_started(self, source_object, res, *user_data):
        for x in range(1,20):
            print(source_object.get_state(), user_data[0][1].get_state())
            time.sleep(1)
        user_data[0][0].quit()


    def dial(self, number):
        call_properties = ModemManager.CallProperties.new()
        call_properties.set_number(number)

        main_loop = GLib.MainLoop()
        # Connection to ModemManager
        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync(connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
        if manager.get_name_owner() is None:
            sys.stderr.write('ModemManager not found in bus')
            sys.exit(2)

        for obj in manager.get_objects():
            print(obj)
            # get instance of ModemManager.ModemVoice
            voice = obj.get_modem_voice()

            try:
                call = voice.create_call_sync(call_properties, None)
                call.start(cancellable=None, callback=self.on_call_started, user_data=(main_loop,call_properties))

                main_loop.run()

            except Exception as e:
                main_loop.quit()
                raise e
            finally:
                print('cleanup current call:', call.get_path())
                print(call.get_state())
                voice.delete_call_sync(call.get_path(), None)
                for callvar in voice.list_calls_sync():
                    print('calls:', callvar.get_path())
                    if (ModemManager.CallState.TERMINATED == callvar.get_state()):
                        print(callvar.get_state())
                        voice.delete_call_sync(callvar.get_path(), None)


if __name__ == "__main__":
    dialer = Dialer()
    # threading.Thread(target=dialer.dial).start()
    dialer.dial('067683837')
