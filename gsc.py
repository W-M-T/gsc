#!/usr/bin/env python3

from argparse import ArgumentParser
from lib.analysis.imports import resolveFileName

def main():
    argparser = ArgumentParser(description="SPL Compiler & Linker")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import object files from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated object_file:path mapping list, to explicitly specify import paths", type=str)
    argparser.add_argument("-o", help="Produce an object file instead of an executable", action="store_true")
    args = argparser.parse_args()

    import_mapping = list(map(lambda x: x.split(":"), args.im.split(","))) if args.im is not None else []
    if not (all(map(lambda x: len(x)==2, import_mapping)) and all(map(lambda x: all(map(lambda y: len(y)>0, x)), import_mapping))):
        print("Invalid import mapping")
        exit()
    #print(import_mapping)
    import_mapping = {a:b for (a,b) in import_mapping}
    print("Imports:",import_mapping)

    if not args.infile.endswith(".spl"):
        print("Input file needs to be .spl")
        exit()




if __name__ == "__main__":
    main()