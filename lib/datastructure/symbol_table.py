#!/usr/bin/env python3

from lib.debug.AST_prettyprinter import print_node, subprint_type
from lib.datastructure.AST import FunUniq

# Keep track if a local is an arg?
# How to handle symbol table merging in case of imports?
# Vars with or without type. Should be able to add type to func params
# Do not forget that even when shadowing arguments or globals, before the definition of this new local, the old one is still in scope (i.e. in earlier vardecls in that function)
class SymbolTable():
    def __init__(self, global_vars = {}, functions = {}, type_syns = {}):
        # mapping of identifier to definition node
        self.global_vars = global_vars

        # (FunUniq, id) as identifier key
        # maps to list of dicts
        # dict has keys "type", "def", "arg_vars", "local_vars"
        # arg_vars is dict of identifiers to dict: {"id":id-token, "type":Type}
        # local_vars is dict of identifiers to vardecl def nodes
        # def is None for BUILTINS
        self.functions = functions
        self.type_syns = type_syns

        self.order_mapping = {"global_vars":{}, "local_vars":{}, "arg_vars": {}} # Order doesn't matter for functions
        # This can be done more easily in newer versions of python, since dict order is deterministic there

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
                "{} :: {}\n\tArgs:{}\n\tLocals:{}".format(func[0][1], subprint_type(x["type"]), list(x["arg_vars"]), list(x["local_vars"])),
            func[1])))
        return "\n"+deflist

    def repr_short(self):
        return "=== Symbol table:\n== Global vars: {}\n== Functions: {}\n== Type synonyms: {}".format(
            list(self.global_vars.keys()),
            self.repr_funcs(),
            "".join(list(map(lambda x: "\n{} = {}".format(x[0], print_node(x[1])), sorted(self.type_syns.items())))))

    def __repr__(self):
        return self.repr_short()

    '''
    def __repr__(self):
        return "Symbol table:\nGlobal vars: {}\nFunctions: {}\nFunArgs: {}\nLocals: {}\nType synonyms: {}".format(self.global_vars, self.functions, self.funarg_vars, self.local_vars, self.type_syns)
    '''

