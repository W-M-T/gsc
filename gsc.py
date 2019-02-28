#!/usr/bin/env python3

from argparse import ArgumentParser

def main():
    argparser = ArgumentParser(description="SPL Compiler")
    argparser.add_argument("infile", metavar="INPUT", help="Input file")
    args = argparser.parse_args()


if __name__ == "__main__":
    main()