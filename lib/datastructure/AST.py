#!/usr/bin/env python3

import sys as _sys
from keyword import iskeyword as _iskeyword
from enum import IntEnum

from lib.datastructure.token import Token

def syntaxnode(typename, *field_names, module=None):
    # Factory method for syntax construct classes
    # field_dict is name:
    typename = _sys.intern(str(typename))
    field_names = list(field_names)

    class_attrs = list(map(_sys.intern, ['_start_pos']))

    for name in [typename] + field_names:
        if type(name) is not str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid identifiers: {!r}'.format(name))
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a keyword: {!r}'.format(name))

    seen = set()
    for name in field_names:
        if name.startswith('_'):
            raise ValueError('Field names cannot start with an underscore: {!r}'.format(name))
        if name in seen:
            raise ValueError('Encountered duplicate field name: {!r}'.format(name))
        seen.add(name)


    # Variables used in the methods and docstrings
    field_names = tuple(map(_sys.intern, field_names))
    arg_list = repr(field_names).replace("'", "")[1:-1]
    repr_fmt = '(' + ', '.join('{}={{{}}}'.format(name, name) for name in field_names) + ')'

    # Create all the named methods to be added to the class namespace


    def __new__(cls):
        self = super().__new__(cls)
        return self


    def __init__(self, **kwargs):
        if not set(kwargs) == set(field_names):
            raise KeyError("Keyword arguments do not match: {} != {}".format(list(set(kwargs)), list(set(field_names))))
        for key, val in kwargs.items():
            setattr(self, key, val)
        for key in class_attrs:
            setattr(self, key, None)


    def __iter__(self):
        field_values = list(map(lambda x: getattr(self, x), field_names))
        return iter(field_values)


    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + repr_fmt.format(**{key: getattr(self,key) for key in self._fields})

    def __serial__(self):
        'Return a string fit for serialisation'
        def rep_tok(tok):
            if type(tok) is Token:
                return '"{}"'.format(tok.val)
            elif type(tok) is list:
                return '[{}]'.format(','.join(t.__serial__() for t in tok))
            else:
                return tok.__serial__()
        key_val = {key: getattr(self,key) for key in self._fields}
        key_val = dict([(k, rep_tok(v)) for (k, v) in key_val.items()])
        temp = self.__class__.__name__ + repr_fmt.format(**key_val)
        return temp

    def __setitem__(self, key, value):
        if not (key in field_names or key in class_attrs):
            raise KeyError("No such attribute name")
        setattr(self, key, value)

    # TODO: Figure out why this collides with the first if statement from parseAtom
    # Commented it out since it was introduced it for debugging in the first place.
    #def __getitem__(self, key):
    #    if not key in field_names:
    #        raise KeyError("No such attribute name")
    #    getattr(self, key)

    def tree_string(self):
        def sub_tree_str(x):
            attr = getattr(self, x)
            if type(attr) == list:
                res = "{} = [\n".format(x)
                for el in attr:
                    if 'tree_string' in dir(el):
                        res += "\n".join(map(lambda y: "\t" + y if len(y) > 0 else y, el.tree_string().split("\n"))) + "\n"
                    else:
                        res += "\t" + el.__repr__() + "\n"
                res += "]\n"
                return res
            elif 'tree_string' in dir(attr):
                return "{} = {}".format(x, attr.tree_string())
            else:
                return "{} = {}".format(x, attr.__repr__() + "\n")

        substrings = list(map(sub_tree_str, field_names))
        indented = "\n".join(list(map(lambda x: "\n".join(map(lambda y: "    " + y, x.rstrip().split("\n"))), substrings)))
        '''return "{} {}:\n{}".format(self.__class__.__name__, "@" + repr(self._start_pos), indented)'''
        return "{}:\n{}".format(self.__class__.__name__, indented)

    def items(self):
        key_values = list(map(lambda x: (x, getattr(self, x)), field_names))
        return iter(key_values)

    # Modify function metadata to help with introspection and debugging

    for method in (__new__, __init__, __iter__, __repr__, __serial__, __setitem__, tree_string , items):
        method.__qualname__ = '{}.{}'.format(typename, method.__name__)

    # Build-up the class namespace dictionary
    # and use type() to build the result class
    class_namespace = {
        '__doc__': '{}({})'.format(typename, arg_list),
        '__slots__': tuple((*(i for i in field_names),*(i for i in class_attrs))),
        '_fields': field_names,
        '__init__':__init__,
        '__iter__':__iter__,
        '__repr__': __repr__,
        '__serial__':__serial__,
        '__setitem__':__setitem__,
        #'__getitem__':__getitem__,
        'tree_string': tree_string,
        'items': items
    }


    result = type(typename, (object,), class_namespace)

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in environments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython), or where the user has
    # specified a particular module.
    if module is None:
        try:
            module = _sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        result.__module__ = module

    return result


class FunKind(IntEnum):
    FUNC   = 1
    PREFIX = 2
    INFIXL = 3
    INFIXR = 4

class Accessor(IntEnum):
    HD  = 1
    TL  = 2
    FST = 3
    SND = 4

class FunUniq(IntEnum):
    FUNC   = 1
    PREFIX = 2
    INFIX  = 3

def FunKindToUniq(kind):
    return {FunKind.FUNC: FunUniq.FUNC,
            FunKind.PREFIX: FunUniq.PREFIX,
            FunKind.INFIXL: FunUniq.INFIX,
            FunKind.INFIXR: FunUniq.INFIX}[kind]

# Where do we track type information of expressions / variables / functions?
# Also: where do we document the types of the attributes of these nodes?
class AST:
    SPL = syntaxnode("SPL", "imports", "decls")

    # NOTE: if importlist None then *

    IMPORT = syntaxnode("IMPORT", "name", "importlist")
    IMPORTNAME = syntaxnode("IMPORTNAME", "name", "alias")

    # val :: AST.VARDECL or AST.FUNDECL or AST.TYPESYN
    DECL = syntaxnode("DECL", "val")

    # type :: AST.TYPE or None, id :: TOKEN, expr :: AST.EXPR
    VARDECL = syntaxnode("VARDECL", "type", "id", "expr")
    # kind :: FunKind, fixity :: int or None, id :: TOKEN, params :: [TOKEN], type :: AST.FUNTYPE or None, vardecls :: [AST.VARDECL], stmts :: [AST.STMT]
    FUNDECL = syntaxnode("FUNDECL", "kind", "fixity", "id", "params", "type", "vardecls", "stmts")
    # type_id :: TOKEN, def_type :: AST.TYPE
    TYPESYN = syntaxnode("TYPESYN", "type_id", "def_type")

    # val :: AST.BASICTYPE or AST.TUPLETYPE or AST.LISTTYPE or TOKEN
    # TODO how to capture naked type id (i.e. a typevar)
    TYPE = syntaxnode("TYPE", "val")
    # type_id :: TOKEN
    BASICTYPE = syntaxnode("BASICTYPE", "type_id")
    # a :: AST.TYPE, b :: AST.TYPE
    TUPLETYPE = syntaxnode("TUPLETYPE", "a", "b")
    # type :: AST.TYPE
    LISTTYPE = syntaxnode("LISTTYPE", "type")
    # from_types :: [AST.TYPE], to_type :: AST.TYPE
    FUNTYPE = syntaxnode("FUNTYPE", "from_types", "to_type")

    # Only used in type synonym rewriting:
    MOD_TYPE = syntaxnode("MOD_TYPE", "module", "orig_id")

    # val :: AST.IFELSE or AST.LOOP or AST.ACTSTMT or AST.RETURN or AST.BREAK or AST.CONTINUE
    STMT = syntaxnode("STMT", "val")

    # condbranches :: [AST.CONDBRANCH]
    IFELSE = syntaxnode("IFELSE", "condbranches")

    # expr :: AST.EXPR or None, stmts :: [AST.STMT]

    CONDBRANCH = syntaxnode("CONDBRANCH", "expr", "stmts")
    # init :: AST.ACTSTMT, cond :: EXPR, update :: AST.ACTSTMT

    LOOP = syntaxnode("LOOP", "init", "cond", "update", "stmts")
    
    # val :: AST.FUNCALL or AST.ASSIGNMENT
    ACTSTMT = syntaxnode("ACTSTMT", "val")

    # expr :: AST.EXPR
    RETURN = syntaxnode("RETURN", "expr")
    BREAK = syntaxnode("BREAK")
    CONTINUE = syntaxnode("CONTINUE")

    # varref :: AST.VARREF, expr :: AST.EXPR
    ASSIGNMENT = syntaxnode("ASSIGNMENT", "varref", "expr")
    # id :: TOKEN, kind :: FunKind, args :: [AST.EXPR]
    FUNCALL = syntaxnode("FUNCALL", "id", "kind", "args")

    # contents :: [literal token or operator token or funcall or identifier or AST.DEFERREDEXPR]
    DEFERREDEXPR = syntaxnode("DEFERREDEXPR", "contents")

    # a :: AST.EXPR, b :: AST.EXPR
    TUPLE = syntaxnode("TUPLE", "a", "b")
    # val :: AST.FUNCALL or literal or identifier
    PARSEDEXPR = syntaxnode("PARSEDEXPR", "val")

    # id :: TOKEN, fields :: [Accessor]
    VARREF = syntaxnode("VARREF", "id", "fields")


    # Name Resolution nodes ===========================================================
    # val :: AST.RES_GLOBAL or AST.RES_NONGLOBAL
    RES_VARREF = syntaxnode("RES_VARREF", "val")

    # module :: string of module name, id :: TOKEN, fields :: [Accessor]
    RES_GLOBAL = syntaxnode("RES_GLOBAL", "module", "id", "fields")

    # scope :: NonGlobalScope, id :: TOKEN, fields :: [Accessor]
    # scope = local or argument.
    RES_NONGLOBAL = syntaxnode("RES_NONGLOBAL", "scope", "id", "fields")

    # Typed nodes =====================================================================

    # oid = Overloaded id, module = module name, returns = True if the function returns a value.
    TYPED_FUNCALL = syntaxnode("TYPED_FUNCALL", "id", "uniq", "args", "oid", "module", "returns")

    # Create node list to support __contains__ and __iter__: TODO make this not hacky
    nodes = [
        SPL,
        IMPORT,
        IMPORTNAME,
        DECL,
        VARDECL,
        FUNDECL,
        TYPESYN,
        TYPE,
        BASICTYPE,
        TUPLETYPE,
        LISTTYPE,
        FUNTYPE,
        MOD_TYPE,
        STMT,
        IFELSE,
        CONDBRANCH,
        LOOP,
        ACTSTMT,
        RETURN,
        BREAK,
        CONTINUE,
        ASSIGNMENT,
        FUNCALL,
        DEFERREDEXPR,
        TUPLE,
        PARSEDEXPR,
        VARREF,
        RES_VARREF,
        RES_GLOBAL,
        RES_NONGLOBAL,
        TYPED_FUNCALL
    ]

    def equalVals(node1, node2): # Same structure and values (not necessarily same tokens)
        if type(node1) == type(node2):
            if type(node1) in AST.nodes:
                list1 = list(node1)
                list2 = list(node2)
                if len(list1) == len(list2):
                    return all(map(lambda x: AST.equalVals(x[0],x[1]), zip(list1,list2)))
                else:
                    return False

            elif type(node1) is Token:
                return node1.val == node2.val
            elif type(node1) is list:
                if len(node1) == len(node2):
                    return all(map(lambda x: AST.equalVals(x[0],x[1]), zip(node1,node2)))
                else:
                    return False
            elif type(node1) in [FunKind, Accessor, type(None)]:
                return node1 == node2
            else:
                raise Exception("AST.equalVals encountered type {}".format(type(node1)))

        else:
            return False




if __name__ == "__main__":
    #print(AST.BASICTYPE(name = "String").tree_string())
    print(AST.TYPESYN(
        type_id = AST.BASICTYPE(
            type_id = "String"
            ),
        def_type = AST.LISTTYPE(
            type = AST.BASICTYPE(
                type_id = "Char"
                )
            )
        ).tree_string())
