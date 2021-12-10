# homeassistant_modem

```
sudo apt-get install build-essential python3-pip python3-dev python3-venv python3-setuptools python3-wheel libffi-dev python3-venv python3.9-venv python3.9-dev libssl-dev libjpeg-dev zlib1g-dev libopenjp2-7 libtiff5  tcpdump libpcap0.8-dev

python3 -m venv homeassistant
cd homeassistant
source bin/activate
pip install wheel
python3 -m pip install homeassistant
hass --open-ui


CONFIGURE GSM MODEM

sudo apt install avahi-daemon mosquitto htop mc build-essential modemmanager
sudo apt install gir1.2-nm-1.0 libmm-glib-dev libglib2.0-dev pkg-config libgirepository1.0-dev libcairo2-dev libqmi-utils udhcpc
sudo apt install build-essential libdbus-glib-1-dev libgirepository1.0-dev

(in venv) 
  pip install python-networkmanager
  pip install gobject PyGObject


sudo usermod -a -G dialout `whoami`


sudo nano /usr/share/polkit-1/actions/org.freedesktop.ModemManager1.policy

In the line starting with <allow_active>, replace auth_self_keep with yes.

========
if you want to use mmcli without superuser rights, you need to create the following file
(you will also need to create intermediate directories in their absence)
/etc/polkit-1/localauthority/50-local.d/ModemManager.pkla


[ModemManager]
Identity=unix-user:*
Action=org.freedesktop.ModemManager1.*
ResultAny=yes
ResultActive=yes
ResultInactive=yes

[NetworkManager]
Identity=unix-user:*
Action=org.freedesktop.NetworkManager.*
ResultAny=yes
=========



https://github.com/vladkozlov69/homeassistant_modem.git
git pull && cp *.py ../hass/custom_components/mm_modem/



dietpi@DietPi:~/homeassistant_modem$ sudo ls -la /etc/NetworkManager/dispatcher.d/02-wwan
-rwxr-xr-x 1 root root 524 Jul 12 12:20 /etc/NetworkManager/dispatcher.d/02-wwan
dietpi@DietPi:~/homeassistant_modem$ sudo cat /etc/NetworkManager/dispatcher.d/02-wwan
#!/usr/bin/env bash

interface=$1
event=$2

echo "$interface => $event"  >> /home/dietpi/wwanlog

if [ $interface = "wwan0" ]
then
  if [ $event = "up" ]
  then
    ip route del default
    ip route add 0.0.0.0/0 dev wwan0
    echo "Routing via WWAN0"
  fi
fi

if [ $interface = "cdc-wdm0" ]
then
  if [ $event = "down" ]
  then
    ip route del default
    ip route add default via 192.168.1.1 dev wlan0 proto dhcp metric 600
#    ip route add default via 192.168.4.1 dev wlan0
    echo "Routing via WLAN0"
  fi
fi
```
