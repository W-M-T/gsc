#!/usr/bin/env python3

from lib.analysis.error_handler import ERROR_HANDLER
import os

HEADER_EXT = ".spld"

def resolveImports(ast, filename, file_mapping_arg, lib_dir_path, lib_dir_env): # TODO consider what happens when there is a lexing / parse error in one of the imports
    local_dir = os.path.dirname(os.path.realpath(filename))

    filename_asimport = os.path.basename(filename).rstrip(".spl")

    print("Resolving imports..")

    file_graph = [] # Mapping of checked imports to their path and their child imports.

    openlist = [(ast, filename_asimport, os.path.realpath(filename))] # list of imports that have been parsed but haven't had their imports checked yet
    while openlist:
        current = openlist.pop()
        cur_ast, cur_importname, cur_filename = current

        cur_file_vertex = {"filename": cur_filename, "importname": cur_importname, "ast": cur_ast, "imports": set()}
        importlist = cur_ast.imports

        for imp in importlist:
            importname = imp.name.val

            cur_file_vertex["imports"].add(importname)

            if importname in map(lambda x: x["importname"], file_graph):
                # Already found, don't parse
                continue

            # Open file, parse, close and add to list of files to get imports of
            try:
                filehandle, filename = resolveFileName(importname, local_dir, file_mapping_arg=file_mapping_arg, lib_dir_path=lib_dir_path, lib_dir_env=lib_dir_env)
                tokenstream = tokenize(filehandle)
                tokenlist = list(tokenstream)

                x = parseTokenStream(tokenstream, filehandle)
                #print(x.tree_string())
                openlist.append((x, importname, filename))
                filehandle.close()
            except FileNotFoundError as e:
                print("Could not locate import: {}".format(importname))
                exit()
        file_graph.append(cur_file_vertex)

    print("Imported the following files:")
    for vertex in file_graph:
        print(vertex["importname"])
    return file_graph

'''
In order of priority:
1: File specific compiler arg
2: Library directory compiler arg
3: Environment variable
4: Local directory
'''
def resolveFileName(name, local_dir, file_mapping_arg=None, lib_dir_path=None, lib_dir_env=None):
    #print(name.name.val,local_dir)
    #option = "{}/{}.spl".format(local_dir, name)
    #print(os.path.isfile(option))

    # Try to import from the compiler argument-specified path for this specific import
    if name in file_mapping_arg:
        try:
            option = file_mapping_arg[name]
            infile = open(option)
            return infile, option
        except Exception as e:
            print(e)
    # Try to import from the compiler argument-specified directory
    if lib_dir_path is not None:
        try:
            option = "{}/{}.spl".format(lib_dir_path, name)
            infile = open(option)
            return infile, option
        except Exception as e:
            pass
    # Try to import from the environment variable-specified directory
    if lib_dir_env is not None:
        try:
            option = "{}/{}.spl".format(lib_dir_env, name)
            infile = open(option)
            return infile, option
        except Exception as e:
            pass
    # Try to import from the same directory as our source file
    try:
        option = "{}/{}.spl".format(local_dir, name)
        infile = open(option)
        return infile, option
    except Exception as e:
        pass
    raise FileNotFoundError
