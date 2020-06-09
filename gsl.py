#!/usr/bin/env python3

from argparse import ArgumentParser
from lib.imports.imports import resolveFileName, OBJECT_EXT
import os.path


def link(file_dict):
    pass


def main():
    argparser = ArgumentParser(description="SPL Linker")
    argparser.add_argument("infiles", metavar="INPUT", help="Object files to link", nargs="+", default=[])
    argparser.add_argument("-m", "--main", metavar="NAME", help="Module to use as entrypoint", type=str)
    argparser.add_argument("-o", metavar="OUTPUT", help="Output filename", type=str) # Make sure not to overwrite things that exist here
    args = argparser.parse_args()

    # Check if the files exist (does not prevent race conditions)
    if not all(map(os.path.isfile, args.infiles)):
        print("Not all input files exist!")
        exit()

    # Check if the files have the correct extension
    if not all(map(lambda x: os.path.basename(x).endswith(OBJECT_EXT), args.infiles)):
        print("Not all input files have a '{}' extension!".format(OBJECT_EXT))
        exit()

    # Open all input files
    handle_dict = {}
    try:
        for filename in args.infiles:
            temp_handle = open(filename,"r")
            handle_dict[filename] = temp_handle
    except Exception as e:
        print("Error opening input files:")
        print(e)

    link(handle_dict)

    # Close the input files
    for k,v in handle_dict.items():
        v.close()


if __name__ == "__main__":
    main()