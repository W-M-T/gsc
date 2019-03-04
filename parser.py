#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Node

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

'''
Top-down parser
Leftmost derivation
Non-ambigue grammatica
Geen left-recursion
LL(1) (1 token lookahead)

Eindige recursie-diepte dmv stack.


De taal is zo gespecificeerd dat de eerstvolgende token altijd maar bij 1 regel zou moeten passen.
Zo niet geef een !!COMPILER ERROR!! want dan zijn dingen goed fout.
Een regel/parser specificeert een verwachte token + een filterfunctie (i.e. TOKEN.OP_ID met value == "="). Default is lambda _: True
Afhankelijk van je positie in de parser heb je meerdere mogelijke opties van regels/parsers.
Als een nonterminal een optie is beschouw je deze gewoon als een lijst van al diens alternatieven naar hetzelfde niveau getild als de huidige.
Houd een soort stack bij van hoe je regels afdaalt. Als het een optie is om de huidige te beeindigen (maar nog niet verplicht) bechouw je ook de regel erboven.


Als zeker is dat de huidige regel afgesloten wordt moet een waarde ge-emit worden. Deze wordt in de regel erboven gebruikt voor het emitten van diens waarde.

Second pass:
Fix de expressie-associativiteit en bindingssterkte aan de hand van de operator-definities


Accessors worden vertaald naar functiecalls met builtin functies.
Moeten ook al een soort symbol-table maken van operator-definities
'''


if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Lexer")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()

    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        tokenlist = list(tokenstream)
        import random
        randtoken = random.choice(tokenlist)
        print(randtoken)
        print(pointToPosition(infile, randtoken.pos))
