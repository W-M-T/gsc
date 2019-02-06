#!/usr/bin/env python3




'''
Zaken als +, -, :, / etc zijn built-in methodes
String is een built-in typesynoniem

TODO
Verplaats datastructuren naar een apart bestand
'''

'''
Lexer heeft string flag
single line comment flag
multiline comment flag
type-of-waarde-context flag (voor -> en , en []), geactiveerd via ::

consumeert keywords als deze niet door iets alfabetisch gevolgd worden

=-teken wordt gewoon gelext als assignment -> dus geen geldige operatornaam
eindigen in comment-mode is error
multiline comment mode sluiten zonder flag is error -> */ geen geldige operatornaam
Vinden van commentsymbolen buiten string mode begint altijd comment
oftewel //* en /* geen geldige operatornamen


'''


