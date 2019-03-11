Lexer
- Keyword an value/type literals should be followed by a non-alphanumeric character
- Accessors can not be preceded by whitespace
- Comments are whitespace
- Keywords cannot be used for identifiers.
- Symbols with meaning in syntax (i.e. ->, ::, ',', =) are reserved for clarity


Parser

- We define a special class that has similar behaviour to namedtuple, i.e. this class allows us to define objects that have accessors and are also itertable. This is useful for syntax elements that have a variable amount of children, for example FunDecl has a sub element FArgs that can consist of zero or more elements.
-
-

