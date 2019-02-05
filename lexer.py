#!/usr/bin/env python3

import time
import sys


def tokenize(filename):
    with open(filename, "r") as infile:
        while True:
            c = infile.read(1)
            if not c:
                break
            yield(c)


if __name__ == "__main__":
    for t in tokenize("./example programs/p1_example.spl"):
        print(t, end="")
        sys.stdout.flush()
        time.sleep(0.05)