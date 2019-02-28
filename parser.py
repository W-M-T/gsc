#!/usr/bin/env python3



'''
Zaken als +, -, :, / etc zijn built-in methodes
String is een built-in typesynoniem

'''

'''
consumeert keywords als deze niet door iets alfabetisch gevolgd worden

=-teken wordt gewoon gelext als assignment -> dus geen geldige operatornaam
eindigen in comment-mode is error
multiline comment mode sluiten zonder flag is error -> */ geen geldige operatornaam
Vinden van commentsymbolen buiten string mode begint altijd comment
oftewel //* en /* geen geldige operatornamen


'''


if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Lexer")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()

    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        print(tokenstream.__next__())
