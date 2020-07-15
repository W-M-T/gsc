#!/usr/bin/env python3

from lib.debug.AST_prettyprinter import print_node, subprint_type
from lib.datastructure.AST import FunUniq
from collections import OrderedDict

# TODO handle external symbol table the same as the regular one maybe?
'''
typesyns:
    gewone: type id naar definitienode
    externe: type id naar dict originele id, module, gedefinieerd type = ('def_type', 'module', 'orig_id')

globals:
    gewone: identifier naar definitienode ("type", "id", "expr")
    externe: identifier naar externe node ("module", "orig_id", "type")

functions:
    gewone: (uniq, id) naar lijst. lijst van dicts ("type", "def", "arg_vars", "local_vars")
    extern: (uniq, id) naar lijst. lijst van dicts ("type", "module", "orig_id", "fixity", "kind")

'''




# Keep track if a local is an arg?
# How to handle symbol table merging in case of imports?
# Vars with or without type. Should be able to add type to func params
# Do not forget that even when shadowing arguments or globals, before the definition of this new local, the old one is still in scope (i.e. in earlier vardecls in that function)
class SymbolTable():
    def __init__(self, global_vars = {}, functions = {}, type_syns = {}):
        # mapping of identifier to definition node
        self.global_vars = OrderedDict(global_vars)

        # (FunUniq, id) as identifier key
        # maps to list of dicts
        # dict has keys "type", "def", "arg_vars", "local_vars"
        # arg_vars is dict of identifiers to dict: {"id":id-token, "type":Type}
        # local_vars is dict of identifiers to vardecl def nodes
        # def is None for BUILTINS
        self.functions = OrderedDict(functions)
        # mapping of type_id to definition type
        self.type_syns = OrderedDict(type_syns)

    '''
    def getFunc(self, uniq, fid, normaltype):
        flist = self.functions[(uniq, fid)]
        #x for x in flist if 
        return
    '''


    def repr_funcs(self):
        temp = "\n=Regular:{}\n=Prefix:{}\n=Infix:{}"
        filtered_uniqs = list(map(lambda y: list(filter(lambda x: x[0][0] == y, self.functions.items())), FunUniq))
        filtered_uniqs = list(map(lambda x: "".join(list(map(SymbolTable.repr_func_uniq, x))), filtered_uniqs))
        return temp.format(*filtered_uniqs)

    def repr_func_uniq(func):
        deflist = "\n".join(list(map(lambda x:
            "{} :: {}".format(func[0][1], subprint_type(x["type"]), list(x["arg_vars"]), list(x["local_vars"])),
            func[1])))
        return "\n"+deflist

    def repr_short(self):
        temp_types = list(map(lambda x: "\n{} = {}".format(x[0], print_node(x[1]["def_type"])), self.type_syns.items()))
        return "=== Symbol table:\n== Global vars: {}\n== Functions: {}\n== Type synonyms: {}".format(
            list(self.global_vars.keys()),
            self.repr_funcs(),
            "".join(temp_types))

    def __repr__(self):
        return self.repr_short()

    '''
    def __repr__(self):
        return "Symbol table:\nGlobal vars: {}\nFunctions: {}\nFunArgs: {}\nLocals: {}\nType synonyms: {}".format(self.global_vars, self.functions, self.funarg_vars, self.local_vars, self.type_syns)
    '''


class ExternalTable(SymbolTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def repr_funcs(self):
        temp = "\n=Regular:{}\n=Prefix:{}\n=Infix:{}"
        filtered_uniqs = list(map(lambda y: list(filter(lambda x: x[0][0] == y, self.functions.items())), FunUniq))
        filtered_uniqs = list(map(lambda x: "".join(list(map(ExternalTable.repr_func_uniq, x))), filtered_uniqs))
        return temp.format(*filtered_uniqs)

    def repr_func_uniq(func):
        deflist = "\n".join(list(map(lambda x:
            "{}({}@{}) :: {}".format(func[0][1], x['orig_id'], x['module'], subprint_type(x['type'])),
            func[1])))
        return "\n"+deflist

    def repr_short(self):
        temp_types = list(map(lambda x: "\n{}({}@{}) = {}".format(x[0], x[1]['orig_id'], x[1]['module'], print_node(x[1]['def_type'])), self.type_syns.items()))
        return "=== External table:\n== Global vars: {}\n== Functions: {}\n== Type synonyms: {}".format(
            list(self.global_vars.keys()),
            self.repr_funcs(),
            "".join(temp_types))