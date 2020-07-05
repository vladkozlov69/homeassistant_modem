"""
Activate a connection by name
"""

import NetworkManager
import sys


# list of devices with active connection
devices = list(filter(lambda _device: _device.ActiveConnection is not None, NetworkManager.NetworkManager.GetAllDevices()))
# print the list
for index, device in enumerate(devices):
    print(index , ")" , device.Interface)

# get the active connection for that device.
active_connection = device.ActiveConnection
print(active_connection.Id)


# And connect
NetworkManager.NetworkManager.DeactivateConnection(active_connection)
