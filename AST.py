#!/usr/bin/env python3

import sys as _sys
from keyword import iskeyword as _iskeyword
from operator import itemgetter as _itemgetter


def syntaxnode(typename, *field_names, module=None):
    # Factory method for syntax construct classes
    # field_dict is name:
    typename = _sys.intern(str(typename))
    field_names = list(field_names)

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


    def __iter__(self):
        field_values = list(map(lambda x: getattr(self, x), field_names))
        return iter(flatten(field_values))


    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + repr_fmt.format(**{key: getattr(self,key) for key in self._fields})

    def tree_string(self):
        substrings = list(map(lambda x: "{} = {}".format(x, getattr(self, x).tree_string() if 'tree_string' in dir(getattr(self, x)) else (getattr(self, x)).__repr__() + "\n"), field_names))
        indented = "\n".join(list(map(lambda x: "\n".join(map(lambda y: "    " + y, x.rstrip().split("\n"))), substrings)))
        return "{}:\n{}".format(self.__class__.__name__, indented)


    # Modify function metadata to help with introspection and debugging

    for method in (__new__, __init__, __iter__, __repr__, tree_string ):
        method.__qualname__ = '{}.{}'.format(typename, method.__name__)

    # Build-up the class namespace dictionary
    # and use type() to build the result class
    class_namespace = {
        '__doc__': '{}({})'.format(typename, arg_list),
        '__slots__': tuple(i for i in field_names),
        '_fields': field_names,
        '__init__':__init__,
        '__iter__':__iter__,
        '__repr__': __repr__,
        'tree_string': tree_string,
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



# Where do we track type information of expressions / variables / functions?
# Also: where do we document the types of the attributes of these nodes?
class AST:
    SPL     = syntaxnode("SPL", "imports", "decls")
    VARDECL = syntaxnode("VARDECL", "type", "id", "expr")

    BASICTYPE = syntaxnode("BASICTYPE", "name")# Change to something like TYPEID?
    # Check whether type variables are required. Not part of the starting grammar / current grammar.
    TUPLETYPE = syntaxnode("TUPLETYPE", "a", "b")
    LISTTYPE = syntaxnode("LISTTYPE", "type")
    FUNTYPE = syntaxnode("FUNTYPE", "from_type", "to_type")

    TYPESYN = syntaxnode("TYPESYN", "type_id", "def_type")

    FUNCALL = syntaxnode("FUNCALL", "id", "kind", "args")

    RETURN = syntaxnode("RETURN", "expr")



if __name__ == "__main__":
    #print(AST.BASICTYPE(name = "String").tree_string())
    print(AST.TYPESYN(
        type_id = AST.BASICTYPE(
            name = "String"
            ),
        def_type = AST.LISTTYPE(
            type = AST.BASICTYPE(
                name = "Char"
                )
            )
        ).tree_string())