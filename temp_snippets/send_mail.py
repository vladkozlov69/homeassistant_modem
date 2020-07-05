#!/usr/bin/env python

import requests

headers = {
    'Authorization': 'Bearer ****',
    'Content-Type': 'application/json',
}

data = '{"personalizations": [{"to": [{"email": "vkozloff@gmail.com"}]}],"from": {"email": "vkozlov69@gmail.com"},"subject": "test subj1","content": [{"type": "text/plain", "value": "test body"}]}'

response = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers, data=data) 
