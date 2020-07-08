from enum import IntEnum

class ANNOT(IntEnum):
    RET = 1
    BRK = 2
    CON = 3

class INSTR():
    def __init__(self, line, annot=None):
        self.line = line
        self.annot = annot

    def __repr__(self):
        return "INSTR: {}{}".format(line,annot.val if not annot is None else "")