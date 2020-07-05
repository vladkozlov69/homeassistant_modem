#!/bin/bash

DT=$(date)

echo $DT' exec' >> /home/dietpi/send_test.log


nmcli c up Unite >> /home/dietpi/send_test.log

sleep 5

route >> /home/dietpi/send_test.log


ping -W 60  8.8.8.8 -c 1 > /dev/null

GW=$(/sbin/ip route | grep 'scope link' | awk '/default/ { print $3 }')


if [ "$GW" = "wwan0" ]; then
  echo $DT' Modem routing on' >> /home/dietpi/send_test.log
fi

if [ "$?" -eq "0" ]; then
  echo $DT' connected' >> /home/dietpi/send_test.log

  SENDGRID_API_KEY=""
  EMAIL_TO="vkozloff@gmail.com"
  FROM_EMAIL="vkozlov69@gmail.com"
  SUBJECT="$GW $DT"

  bodyHTML="Email body goes here"

  maildata='{"personalizations": [{"to": [{"email": "'${EMAIL_TO}'"}]}],"from": {"email": "'${FROM_EMAIL}'"},
          "subject": "'${SUBJECT}'","content": [{"type": "text/html", "value": "'${bodyHTML}'"}]}'

  echo $maildata;

  curl --request POST --url https://api.sendgrid.com/v3/mail/send --header 'Authorization: Bearer '$SENDGRID_API_KEY --header 'Content-Type: application/json' --data "'$maildata'";

  echo $DT' sent' >> /home/dietpi/send_test.log

else
  echo $DT' not connected' >> /home/dietpi/send_test.log
fi

nmcli c down Unite

