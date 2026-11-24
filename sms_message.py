from dataclasses import dataclass


@dataclass
class SmsMessage:
    path: str
    number: str
    text: str
    timestamp: str
