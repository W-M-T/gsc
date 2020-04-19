#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Token
import parsec as ps
from AST import AST, FunKind, Accessor
from AST_prettyprinter import flatten, printAST


@ps.generate
def SPL():
    found_imports = yield ps.many(ImportDecl)
    found_decls = yield ps.many(Decl)
    return AST.SPL(imports=found_imports, decls=found_decls)

AnyId = ps.token(TOKEN.IDENTIFIER) ^ ps.token(TOKEN.TYPE_IDENTIFIER) ^ ps.token(TOKEN.OP_IDENTIFIER)

@ps.generate
def SpecificImport():
    yield ps.token(TOKEN.FROM)
    found_name = yield ps.token(TOKEN.FILENAME)
    yield ps.token(TOKEN.IMPORT)
    found_importlist = yield ImportListStrict
    return AST.IMPORT(name=found_name, importlist=found_importlist)

@ps.generate
def AllImport():
    yield ps.token(TOKEN.IMPORTALL)
    found_name = yield ps.token(TOKEN.FILENAME)
    return AST.IMPORT(name=found_name, importlist=None)

ImportDecl = SpecificImport ^ AllImport

@ps.generate
def ImportListStrict():
    n = yield ImportName
    ns = yield ps.many(ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == ",")) >> ImportName)
    return [n, *ns]

@ps.generate
def ImportName():
    found_name = yield AnyId
    found_alias = yield ps.times(ps.token(TOKEN.AS) >> AnyId,0,1)
    found_alias = found_alias[0] if len(found_alias) > 0 else None
    return AST.IMPORTNAME(name=found_name, alias=found_alias)

# DECLS ===========================================================
@ps.generate
def Decl():
    found_val = yield VarDecl ^ FunDecl ^ TypeSyn ^ PrefixOpDecl ^ InfixOpDecl
    return AST.DECL(val=found_val)

Accessor_lookup = {
    ".hd" : Accessor.HD,
    ".tl" : Accessor.TL,
    ".fst" : Accessor.FST,
    ".snd" : Accessor.SND
}

@ps.generate
def IdField():
    i = yield ps.token(TOKEN.IDENTIFIER)
    found_fields = yield ps.many(ps.token(TOKEN.ACCESSOR))
    found_fields = list(map(lambda x: Accessor_lookup[x.val], found_fields))
    return AST.VARREF(id=i, fields=found_fields)

@ps.generate
def PrefixOpDecl():
    yield ps.token(TOKEN.PREFIX)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    varname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    typesig = yield ps.times(PreFunTypeSig,0,1)
    typesig = typesig[0] if len(typesig) > 0 else None
    yield ps.token(TOKEN.CURL_OPEN)
    decls = yield ps.many(VarDecl)
    found_stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return AST.FUNDECL(kind=FunKind.PREFIX, fixity=None, id=operator, params=[varname], type=typesig, vardecls=decls, stmts=found_stmts)

@ps.generate
def InfixOpDecl():
    side = yield (ps.token(TOKEN.INFIXL) ^ ps.token(TOKEN.INFIXR))
    if side.typ is TOKEN.INFIXL:
        found_kind = FunKind.INFIXL
    elif side.typ is TOKEN.INFIXR:
        found_kind = FunKind.INFIXR
    else:
        raise Exception("Should never happen")
    found_fixity = yield ps.token(TOKEN.INT)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    a = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ","))
    b = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    typesig = yield ps.times(InfFunTypeSig,0,1)
    typesig = typesig[0] if len(typesig) > 0 else None
    yield ps.token(TOKEN.CURL_OPEN)
    decls = yield ps.many(VarDecl)
    found_stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return AST.FUNDECL(kind=found_kind, fixity=found_fixity, id=operator, params=[a,b], type=typesig, vardecls=decls, stmts=found_stmts)

@ps.generate
def VarDecl():
    typ = yield (ps.token(TOKEN.VAR) | Type)
    typ = None if type(typ) == Token and typ.typ == TOKEN.VAR else typ
    varname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "="))
    found_expr = yield Exp
    yield ps.token(TOKEN.SEMICOLON)
    return AST.VARDECL(type=typ, id=varname, expr=found_expr)

@ps.generate
def FunDecl():
    fname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    args = yield ps.times(FArgs,0,1)
    args = args[0] if len(args) > 0 else args
    yield ps.token(TOKEN.PAR_CLOSE)
    typesig = yield ps.times(FunTypeSig,0,1)
    typesig = typesig[0] if len(typesig) > 0 else None
    yield ps.token(TOKEN.CURL_OPEN)
    decls = yield ps.many(VarDecl)
    found_stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return AST.FUNDECL(kind=FunKind.FUNC, fixity=None, id=fname, params=args, type=typesig, vardecls=decls, stmts=found_stmts)

@ps.generate
def FArgs():
    x = yield ps.token(TOKEN.IDENTIFIER)
    xs = yield ps.many(ps.token(TOKEN.OP_IDENTIFIER, (lambda x : x == ",")) >> ps.token(TOKEN.IDENTIFIER))
    return [x, *xs]

@ps.generate
def TypeSyn():
    yield ps.token(TOKEN.TYPESYN)
    identifier = yield ps.token(TOKEN.TYPE_IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == '='))
    other_type = yield Type
    return AST.TYPESYN(type_id=identifier, def_type=other_type)


# TYPES =====================================
@ps.generate
def Type():
    found_val = yield BasicType ^ TupType ^ ListType ^ ps.token(TOKEN.TYPE_IDENTIFIER)
    return AST.TYPE(val=found_val)

BasicTypeChoice = ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Int")) | ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Bool")) | ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Char"))

@ps.generate
def BasicType():
    a = yield BasicTypeChoice
    return AST.BASICTYPE(type_id=a)

@ps.generate
def TupType():
    yield ps.token(TOKEN.PAR_OPEN)
    el1 = yield Type
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ","))
    el2 = yield Type
    yield ps.token(TOKEN.PAR_CLOSE)
    return AST.TUPLETYPE(a=el1, b=el2)

@ps.generate
def ListType():
    yield ps.token(TOKEN.BRACK_OPEN)
    a = yield Type
    yield ps.token(TOKEN.BRACK_CLOSE)
    return AST.LISTTYPE(type=a)

# Check this:
# results in type id token instead of type node with type id token
RetType = ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Void")) ^ Type

@ps.generate
def FunType():
    a = yield ps.many(Type)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == "->"))
    b = yield RetType
    return AST.FUNTYPE(from_types=a, to_type=b)

@ps.generate
def FunTypeSig():
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "::"))
    a = yield FunType
    return a

@ps.generate
def PreFunType():
    a = yield Type
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == "->"))
    b = yield Type
    return AST.FUNTYPE(from_types=[a], to_type=b)

@ps.generate
def PreFunTypeSig(): # TODO maybe get rid of the typesig ones and move the :: to the decl
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "::"))
    a = yield PreFunType
    return a

@ps.generate
def InfFunType():
    a = yield Type
    b = yield Type
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == "->"))
    out = yield Type
    return AST.FUNTYPE(from_types=[a, b], to_type=out)

@ps.generate
def InfFunTypeSig():
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "::"))
    a = yield InfFunType
    return a


# CONTROL FLOW ==================================================
@ps.generate
def Stmt():
    found_val = yield StmtIfElse ^ StmtWhile ^ StmtFor ^ StmtActSem ^ StmtRet ^ StmtBreak ^ StmtContinue
    return AST.STMT(val=found_val)

@ps.generate
def StmtIfElse():
    yield ps.token(TOKEN.IF)
    yield ps.token(TOKEN.PAR_OPEN)
    condition = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    if_contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    first_cond = AST.CONDBRANCH(expr=condition, stmts=if_contents)

    elifs = yield ps.many(StmtElif)
    elses = yield ps.times(StmtElse, 0,1)
    return AST.IFELSE(condbranches=[first_cond, *elifs, *elses])

@ps.generate
def StmtElif():
    yield ps.token(TOKEN.ELIF)
    yield ps.token(TOKEN.PAR_OPEN)
    condition = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return AST.CONDBRANCH(expr=condition, stmts=contents)

@ps.generate
def StmtElse():
    yield ps.token(TOKEN.ELSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return AST.CONDBRANCH(expr=None, stmts=contents)

@ps.generate
def StmtWhile():
    yield ps.token(TOKEN.WHILE)
    yield ps.token(TOKEN.PAR_OPEN)
    condition = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)

    return AST.LOOP(init=None, cond=condition, update=None, stmts=contents)

@ps.generate
def StmtFor():
    yield ps.token(TOKEN.FOR)
    yield ps.token(TOKEN.PAR_OPEN)
    initial = yield ps.times(ActStmt, 0,1)
    initial = initial[0] if len(initial) > 0 else None
    yield ps.token(TOKEN.SEMICOLON)
    condition = yield ps.times(Exp, 0,1)
    condition = condition[0] if len(condition) > 0 else None
    yield ps.token(TOKEN.SEMICOLON)
    update = yield ps.times(ActStmt, 0,1)
    update = update[0] if len(update) > 0 else None
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return AST.LOOP(init=initial, cond=condition, update=update, stmts=contents)

@ps.generate
def StmtActSem():
    a = yield ActStmt
    yield ps.token(TOKEN.SEMICOLON)
    return a

@ps.generate
def StmtRet():
    yield ps.token(TOKEN.RETURN)
    found_expr = yield ps.times(Exp, 0,1)
    found_expr = found_expr[0] if len(found_expr) > 0 else None
    yield ps.token(TOKEN.SEMICOLON)
    return AST.RETURN(expr=found_expr)

@ps.generate
def StmtBreak():
    yield ps.token(TOKEN.BREAK)
    yield ps.token(TOKEN.SEMICOLON)
    return AST.BREAK()

@ps.generate
def StmtContinue():
    yield ps.token(TOKEN.CONTINUE)
    yield ps.token(TOKEN.SEMICOLON)
    return AST.CONTINUE()


# EXPRESSIONS ===================================================

@ps.generate
def Exp():
    a = yield ConvExp
    b = yield ps.many(ExpMore)

    b = flatten(b)
    return AST.DEFERREDEXPR(contents=[a, *b])

@ps.generate
def ExpMore():
    op = yield ps.token(TOKEN.OP_IDENTIFIER)
    exp = yield ConvExp
    return [op, exp]

@ps.generate
def PrefixOpExp():
    op = yield ps.token(TOKEN.OP_IDENTIFIER)
    exp = yield Exp
    return AST.FUNCALL(kind=FunKind.PREFIX, id=op, args=[exp])

@ps.generate
def ExpLiteral():
    tok = yield ps.token(TOKEN.INT) ^ ps.token(TOKEN.CHAR) ^ ps.token(TOKEN.STRING) ^ ps.token(TOKEN.BOOL) ^ ps.token(TOKEN.EMPTY_LIST)
    return tok

@ps.generate
def ExpSub():
    yield ps.token(TOKEN.PAR_OPEN)
    subexp = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    return subexp

@ps.generate
def ConvExp():
    a = yield FunCall ^ IdField ^ PrefixOpExp ^ ExpLiteral ^ ExpSub
    return a

# STATEMENTS ====================================================
@ps.generate
def FunCall():
    fname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    found_args = yield ps.times(ActArgs, 0,1)
    found_args = found_args[0] if len(found_args) > 0 else None
    yield ps.token(TOKEN.PAR_CLOSE)
    return AST.FUNCALL(id=fname, kind=FunKind.FUNC, args=found_args)

# Kijk naar de "seperated" combinator
@ps.generate
def ActArgs():
    a = yield Exp
    b = yield ps.many(ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ',')) >> Exp)
    return [a, *b]

@ps.generate
def Ass():
    var = yield IdField
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "="))
    expression = yield Exp
    return AST.ASSIGNMENT(varref=var, expr=expression)

@ps.generate
def ActStmt():
    found_val = yield Ass ^ FunCall
    return AST.ACTSTMT(val=found_val)



def parseTokenStream(instream):
    return SPL.parse_strict(list(instream), infile)


prefixtest = '''

prefix *%* (a) { }
'''

infixtest = '''

infixl 2 *%*(a,a) { }
'''

prefixtest2 = '''

prefix *%* (a) :: { }
'''

importtest = '''

from TestFile import abs,pow as power, cons_pi as pi
from StdIO import print
from math import *

var element = no;
Int element2 = no;

type String = [Char]

prefix *%* (a) { break; }
infixl 4 <! (a,b) { break; }
infixr 4 <! (a,b) { break; }

power (a,b) :: Int Int -> Int {
    if (x == 1) {
        return 2;
    }
    elif (x==3) {
        return 4;
    }
    else {
        return 88;
    }
    f(22);

    while (True) {
        break;
    }

    for(f(x);x==1;x= x + 1) {
        continue;
    }
}
'''

extratest = '''
facR ( n ) :: Int -> Int {
    if ( n < 2 ) {
        return 1;
    } else {
        return n * facR ( n - 1 );
    }
}
'''
if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Parser")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()


    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        tokenlist = list(tokenstream)
        #print(tokenlist)
        #x = SPL.parse_strict(tokenlist, infile)
        #print(x.tree_string())
        #print(printAST(x))


    test1 = [
        Token(None, TOKEN.TYPESYN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "String"),
        Token(None, TOKEN.OP_IDENTIFIER, "="),
        
    ]
    test2 = [
        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    test3 = [
        Token(None, TOKEN.TYPESYN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "String"),
        Token(None, TOKEN.OP_IDENTIFIER, "="),
        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    #TypeSyn.parse(test3)
    import io
    testprog = io.StringIO('''
prefix !! (x){
    return x;
}
''')
    testprog2 = io.StringIO('''
Int -> Void
''')

    testprog = io.StringIO('''
a + + b - 2 * "heyo" - - False + (2*2) - []
''')

    testprog3 = io.StringIO('''
("heyo" + + False) - myvar.snd
''')

    testexpr = io.StringIO('''
        a + b + 5
    ''')

    testerror = io.StringIO('''
        prefix !! (x){
            return (a + b;
        }
    ''')

    #print(list(tokenize(testprog)))
    #Type.parse(test2)

    print(dir(Exp.fn))

    tokens = list(tokenize(testerror))
    print(tokens)
    x = SPL.parse_strict(tokens, testerror)
    print("PARSED X =============================")
    print(x.tree_string())
    #print(list(tokenize(testprog)))
    #Exp.parse_strict(list(tokenize(testprog3)))

    #tokens = list(tokenize(io.StringIO(importtest)))
    #print(tokens)
    #x = SPL.parse_strict(tokens)
    #print("PARSED X =============================")
    #print(x.tree_string())

    exit()

    print("DONE")
