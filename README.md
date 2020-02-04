# Glorious SPL Compiler

## Grammar

We have made signifcant changes to the grammar to solve a few issues and to introduce new syntax which is required for our extensions:

<!--- 
Add some information about how we tackled left recursion etc.
-->
- One of our extensions makes it possible to define custom operators, which is defined by the `OpDecl` rule. On top of that the operator rule `op` was changed so that operators can consist of an arbitrary number of operator chars (`opChar`).
- Additionally we have added the `TypeSyn` rule which makes it possible to define Type Synonyms. 
- In addition to while loops, it is also possible to use for loops, this was achieved by changing the `Stmt` rule.
- We have added support for the import statement by introducing the `ImportDecl`, `ImportName` and `ImportList` rules.

## Lexer

## Parser

## Design decisions
- Dynamic allocation of memory (e.g. lists) is done by using the heap. This means that all globally and locally defined lists are stored on the heap and a stack frame of a function has pointers to the heap when refering to these lists. This issue does not arise for tuples sinces all of the variables are statically typed thus redefinition of a tuple cannot change its memory size.

## Extensions (for now)

### String literals


### For loops

### Type synonyms

### Custom infix operators

### elif keyword

### Structs

### Compile-time code-execution

### Qualified imports

## Testing

