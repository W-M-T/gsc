#!/usr/bin/env python3

from lib.analysis.error_handler import *
from lib.imports.imports import resolveFileName, OBJECT_EXT

from lib.parser.lexer import REG_FIL

from collections import OrderedDict

import os

'''
TODO Validate filenames using REG_FIL from lexer
'''

OBJECT_COMMENT_PREFIX = "// "

OBJECT_FORMAT = {
    "depend"    : "DEPENDENCIES:",
    "dependitem": "DEPEND ",
    "init"      : "INIT SECTION:",
    "entrypoint": "ENTRYPOINT:",
    "globals"   : "GLOBAL SECTION:",
    "funcs"     : "FUNCTION SECTION:",
    "main"      : "MAIN:"
}

def getSlice(text, start, end):
    start_ix = text.find(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT[start]) if start is not None else 0
    end_ix = text.find(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT[end]) if end is not None else len(text)
    if start_ix == -1 or end_ix == -1:
        raise Exception("Malformed object file")
    res = text[start_ix:end_ix].split("\n",1)[1].strip()
    text = text[:start_ix] + text[end_ix:]
    return res, text

def parseObjectFile(data):
    deps, data = getSlice(data, "depend", "init")
    inits, data = getSlice(data, "init", "entrypoint")
    globs, data = getSlice(data, "globals", "funcs")
    funcs, data = getSlice(data, "funcs", "main")
    main, data = getSlice(data, "main", None)

    modnames = set()
    for line in [x for x in deps.split("\n") if len(x) > 0]:
        if line.startswith(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['dependitem']):
            found = line[len(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['dependitem']):]
            modnames.add(found)
        elif line.startswith(OBJECT_COMMENT_PREFIX):
            pass
        else:
            raise Exception("Malformed "+line)
    modnames = list(modnames)
    #print(modnames)
    temp = OrderedDict([
        ("dependencies", modnames),
        ("global_inits", inits),
        ("global_mem", globs),
        ("functions", funcs)
    ])
    return temp

def getObjectFiles(main_filehandle, main_filename, local_dir, file_mapping_arg={}, lib_dir_path=None, lib_dir_env=None):
    main_mod_name = os.path.splitext(os.path.basename(main_filename))[0]
    #print(main_mod_name)

    res = []
    seen = set([main_mod_name])
    closed = {}
    # openlist is list of open file handles that need to be read still
    openlist = [(main_filehandle, main_filename)]
    while openlist:
        cur_handle, cur_name = openlist.pop()
        #print("Reading", cur_name)
        data = cur_handle.read()
        cur_handle.close()
        obj_struct = parseObjectFile(data)
        res.append(obj_struct)
        for dep in obj_struct['dependencies']:
            if dep not in seen:
                found = resolveFileName(
                    dep,
                    OBJECT_EXT,
                    local_dir,
                    file_mapping_arg=file_mapping_arg,
                    lib_dir_path=lib_dir_path,
                    lib_dir_env=lib_dir_env
                )
                #print(found)
                seen.add(dep)
                openlist.append(found)

    ERROR_HANDLER.checkpoint()
    return res