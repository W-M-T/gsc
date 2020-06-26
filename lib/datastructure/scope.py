#!/usr/bin/env python3

from enum import IntEnum

class NONGLOBALSCOPE(IntEnum):
    GlobalVar   = 1
    ArgVar      = 2
    LocalVar    = 3