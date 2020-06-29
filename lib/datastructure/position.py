class Position():
    def __init__(self, line = 1, col = 1):
        self.line = line
        self.col  = col

    def __repr__(self):
        return "line {} :col {}".format(self.line, self.col)

    def copy(self):
        return Position(self.line, self.col)