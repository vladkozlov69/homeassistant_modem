# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass


@dataclass
class SmsMessage:
    path: str
    number: str
    text: str
    timestamp: str
