# gsc
Glorious SPL Compiler

## Design decisions
- Dynamic allocation of memory (e.g. lists) is done by using the heap. This means that all globally and locally defined lists are stored on the heap and a stack frame of a function has pointers to the heap when refering to these lists. This issue does not arise for tuples sinces all of the variables are statically typed thus redefinition of a tuple cannot change its memory size.
