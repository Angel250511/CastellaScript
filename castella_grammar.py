# castella_grammar.py

"""
Gramática para el lenguaje Castella, basada en la sintaxis del español
e inspirada en Python. Diseñada para ser procesada por Lark con el parser LALR(1).
"""

// Directivas de Lark para importaciones y tokens ignorados
%import common.WS // Importa la definición estándar de espacios en blanco de Lark.
%ignore WS         // Le dice al lexer que se salte los espacios en blanco (WS).
%import common.C_COMMENT // Importa comentarios de bloque como C_COMMENT
%import common.ESCAPED_STRING // Importa cadenas con escapes (usada por 'cadena')
%import common.FLOAT // Importa números flotantes (usada por 'numero')
%import common.INT // Importa números enteros (usada por 'numero')

// Definición explícita de comentarios de línea (para ignorarlos)
LINE_COMMENT: "//" /[^\n]*/ "\n"
%ignore LINE_COMMENT
// Alias para comentarios de bloque para usar en el transformer (docstrings)
MULTILINE_STRING: C_COMMENT


// =============================================================================
// TOKENS (Palabras Clave y Operadores en Español)
// =============================================================================

// Palabras clave
LET_KW: "let"          // Para declaraciones de variables
SI_KW: "si"            // if
ELIF_KW: "sino si"     // elif
SINO_KW: "sino"        // else
MIENTRAS_KW: "mientras" // while
PARA_KW: "para"        // for
EN_KW: "en"            // in (for loops and membership)
ROMPER: "romper"       // break
CONTINUAR: "continuar" // continue
PASAR: "pasar"         // pass
FUNCION_KW: "funcion"  // def
CLASE_KW: "clase"      // class
DESDE: "desde"         // from (import)
IMPORT_KW: "importar"  // import
RETORNAR_KW: "retornar"// return
TRY_KW: "intentar"     // try
CATCH_KW: "capturar"   // except
FINALLY_KW: "finalmente" // finally
WITH_KW: "con" # Using 'con' for 'with'
COMO: "como"           // as (import, except)
NUEVA_KW: "nueva"      // new (instance creation)
IMPRIMIR: "imprimir"   // print
LAMBDA_KW: "lambda"    // lambda
VERDADERO_KW: "verdadero" // True
FALSO_KW: "falso"      // False
NINGUNO_KW: "ninguno"   // None
ES_KW: "es"            // is
ES_NO: "es no"         // is not
NO_EN: "no en"         // not in
Y_OP: "y"              // and
O_OP: "o"              // or
NO_OP: "no"            // not
GRAFICAR: "graficar"   // For plotting

// Operadores y Puntuación (en español o símbolos comunes)
IGUAL: "="             // Assignment
PLUS: "+"              // Addition, Unary Plus
MINUS: "-"             // Subtraction, Unary Minus
STAR: "*"              // Multiplication, Star-args
SLASH: "/"             // Division
PERCENT: "%"           // Modulo
DOUBLE_STAR: "**"      // Power
DOUBLE_SLASH: "//"     // Floor Division
AT_OP: "@"             // Matrix Multiplication (@)
AMPERSAND_OP: "&"      // Bitwise AND
PIPE_OP: "|"           // Bitwise OR
CARET_OP: "^"          // Bitwise XOR
TILDE_OP: "~"          // Bitwise NOT (Unary)
LSHIFT_OP: "<<"        // Left Shift
RSHIFT_OP: ">>"        // Right Shift

// Operadores Aumentados (Assignment Operators)
PLUS_EQUAL: "+="
MINUS_EQUAL: "-="
STAR_EQUAL: "*="
SLASH_EQUAL: "/="
PERCENT_EQUAL: "%="
DOUBLE_STAR_EQUAL: "**="
DOUBLE_SLASH_EQUAL: "//="
AMPERSAND_EQUAL: "&="
PIPE_EQUAL: "|="
CARET_EQUAL: "^="
LSHIFT_EQUAL: "<<="
RSHIFT_EQUAL: ">>="
AT_EQUAL: "@=" // Augmented Matrix Multiplication Assignment

// Operadores de Comparación (usando símbolos comunes o palabras clave)
LE: "<="               // Less than or Equal
GE: ">="               // Greater than or Equal
EQ: "=="               // Equal
NE: "!="               // Not Equal
LT: "<"                // Less Than
GT: ">"                // Greater Than

// Puntuación y Delimitadores
LPAR: "("              // Left Parenthesis
RPAR: ")"              // Right Parenthesis
LBRACKET: "["          // Left Square Bracket
RBRACKET: "]"          // Right Square Bracket
LBRACE: "{"            // Left Curly Brace
RBRACE: "}"            // Right Curly Brace
COMA: ","              // Comma
DOT: "."               // Dot access
COLON: ":"             // Colon
SEMICOLON: ";"         // Semicolon
QUESTION: "?"          // Ternary operator part (condition ? true : false)
ARROW: "->"            // Return type hint
ARROBA: "@"            // Decorator start

// Literales
// Re-usar Lark common para números y cadenas, redefinir o añadir tipos específicos.
numero: INT | FLOAT
cadena: ESCAPED_STRING
// Comentario de bloque aliasado a MULTILINE_STRING para docstrings.
// MULTILINE_STRING ya definida arriba como alias de C_COMMENT

// Literales numéricos complejos e imaginarios
imaginary_literal: /[0-9]+j/ | FLOAT "j" | INT "j" // e.g., 5j, 1.2j, 5.j (need to be careful with float regex interaction)
// Simpler regex that might be safer with float/int
imaginary_literal: /((\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)(j|J)/ // Matches float or int followed by j/J
complex_literal: numero (PLUS|MINUS) imaginary_literal // e.g., 3 + 4j, 1.5 - 2j

// Identificadores (nombres de variables, funciones, clases, etc.)
IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/

// Asterisco para importaciones *
STAR: "*" // Needed for `from ... import *`

// Citas para forward references en type hints (ej. 'MiClase')
QUOTE: "'"

// =============================================================================
// REGLAS GRAMATICALES (Sintaxis de Castella)
// =============================================================================

// Regla de inicio: secuencia de elementos de nivel superior.
// Los decoradores deben preceder inmediatamente a una definición de función o clase.
start: (decorator | class_def | func_def | stmt | MULTILINE_STRING)*

// Sentencias principales (stmt). Todas las reglas que terminan en SEMICOLON son tipos de sentencia.
stmt: declaration | asignacion | importar | graficar | expr_stmt
    | if_stmt | for_stmt | while_stmt | try_stmt | with_stmt
    | BREAK | CONTINUE | PASS_KW
    | print_stmt | unpack_assignment | augmented_assignment
    | return_stmt
    | call_stmt // Call as a standalone statement: `mi_funcion();`


// Sentencia de Declaración de Variable
// Soporta: let id; let id = val; let id : type; let id : type = val;
declaration: LET_KW WS? IDENT WS? type_hint? WS? initial_value? WS? SEMICOLON
type_hint: COLON WS? type
initial_value: IGUAL WS? expr

// Sentencia de Asignación (cubre acceso a atributos o índices)
// Usamos 'access' en el lado izquierdo ya que cubre IDENT, .access, [index]
asignacion: access WS? IGUAL WS? expr WS? SEMICOLON

// Sentencia de Graficar (matplotib.pyplot)
graficar: GRAFICAR WS? LPAR WS? expression_list? WS? RPAR WS? SEMICOLON

// Sentencia de Imprimir (print)
print_stmt: IMPRIMIR WS? LPAR WS? expression_list? WS? RPAR WS? SEMICOLON

// Sentencia de Expresión (una expresión sola, terminada por ;)
expr_stmt: expr WS? SEMICOLON

// Sentencia de Llamada (una llamada a función/método sola, terminada por ;)
// Esto es necesario si `access` puede ser una llamada con efectos secundarios y quieres permitirlo como sentencia `llamada();`.
call_stmt: access WS? SEMICOLON


// Sentencia de Desempaquetado (Unpack Assignment)
// Soporta: a, b = ...; (a, b) = ...; [a, b] = ...; a, b, = ...; etc.
unpack_assignment: unpack_destination WS? IGUAL WS? expr WS? SEMICOLON

// Destino de la asignación de desempaquetado
unpack_destination: IDENT // variable simple
                  | tuple_unpack_destination // (a, b, ...)
                  | list_unpack_destination // [a, b, ...]
                  | unpack_sequence // a, b, ... (secuencia sin paréntesis/corchetes)

// Reglas para secuencias de items con aplanamiento (-> items_rule_name)
// Esto genera una lista plana de los items reales (excluyendo comas y WS ignorados)
// en el AST para el transformer, facilitando su manejo.

// Secuencia de destinos de desempaquetado
unpack_sequence: unpack_item_dest (WS? COMA WS? unpack_item_dest)* [WS? COMA]? -> unpack_sequence_items
unpack_item_dest: IDENT | tuple_unpack_destination | list_unpack_destination

// Secuencia de expresiones (para llamadas, print, graficar, listas/tuplas/conjuntos literales)
expression_list: expr (WS? COMA WS? expr)* [WS? COMA]? -> expression_list_items

// Secuencia de pares clave-valor (para diccionarios literales)
key_value_list: key_value (WS? COMA WS? key_value)* [WS? COMA]? -> key_value_list_items
key_value: expr WS? COLON WS? expr

// Secuencia de parámetros (para definiciones de función lambda)
parameter_list: parameter_item (WS? COMA WS? parameter_item)* [WS? COMA]? -> parameter_list_items

// Secuencia de argumentos (para llamadas a función/método)
// El orden de las alternativas aquí importa para el parseo, aunque Python tiene un orden estricto
// (posicional, *args, keyword, **kwargs). La gramática permite cualquier orden, el transformer
// *podría* validarlo, pero no es estrictamente necesario para la traducción básica.
argument_list: argument (WS? COMA WS? argument)* [WS? COMA]? -> argument_list_items
argument: keyword_argument | star_arg | double_star_arg | expr // expr es el argumento posicional
keyword_argument: IDENT WS? IGUAL WS? expr
star_arg: STAR WS? expr
double_star_arg: DOUBLE_STAR WS? expr

// Secuencia de nombres importados (para from ... import ...)
imported_names_list: imported_name (WS? COMA WS? imported_name)* [WS? COMA]? -> imported_names_list_items
imported_name: IDENT [WS? COMO WS? IDENT]

// Secuencia de bases de herencia (para class ... desde ...)
inheritance_list: access (WS? COMA WS? access)* [WS? COMA]? -> inheritance_list_items

// Secuencia de argumentos de tipo (para tipos genéricos como List[int])
type_arguments: type (WS? COMA WS? type)* [WS? COMA]? -> type_arguments_items


// Sentencia de Asignación Aumentada (+=, -=, etc.)
augmented_assignment: access WS? AUG_ASSIGN_OP WS? expr WS? SEMICOLON
AUG_ASSIGN_OP: PLUS_EQUAL | MINUS_EQUAL | STAR_EQUAL | SLASH_EQUAL | PERCENT_EQUAL | DOUBLE_STAR_EQUAL | DOUBLE_SLASH_EQUAL | AMPERSAND_EQUAL | PIPE_EQUAL | CARET_EQUAL | LSHIFT_EQUAL | RSHIFT_EQUAL | AT_EQUAL

// Sentencia with
with_stmt: WITH_KW WS? expr [WS? COMO WS? IDENT] WS? block

// Sentencia return
return_stmt: RETORNAR_KW WS? [expr] WS? SEMICOLON

// Sentencias de control de flujo simples con punto y coma
BREAK: ROMPER WS? SEMICOLON -> BREAK_STMT
CONTINUE: CONTINUAR WS? SEMICOLON -> CONTINUE_STMT
PASS_KW: PASAR WS? SEMICOLON -> PASS_STMT


// Bloque de código delimitado por llaves
block: LBRACE WS? (MULTILINE_STRING | decorator | class_def | func_def | class_attribute | stmt)* WS? RBRACE

// Sentencias Condicionales (if/elif/else)
if_stmt: SI_KW WS? LPAR expr RPAR WS? block (WS? ELIF_KW WS? LPAR expr RPAR WS? block)* [WS? SINO_KW WS? block]?

// Sentencia Iterativa for
for_stmt: PARA_KW WS? IDENT WS? EN_KW WS? expr WS? block

// Sentencia Iterativa while
while_stmt: MIENTRAS_KW WS? LPAR expr RPAR WS? block

// Sentencia de Manejo de Excepciones (try/except/finally)
try_stmt: TRY_KW WS? block (WS? except_block)+ [WS? finally_block]?
except_block: CATCH_KW [WS? access [WS? COMO WS? IDENT]] WS? block
finally_block: FINALLY_KW WS? block

// Decorador
decorator: ARROBA WS? access

// Definición de Función
// Los parámetros usan la regla 'parameter_list' (secuencia de parameter_item).
func_def: FUNCION_KW WS? IDENT WS? LPAR WS? parameter_list? WS? RPAR WS? return_type? WS? block
return_type: ARROW WS? type

// Items de Parámetro (para definiciones de función/lambda)
// El orden de las alternativas aquí es importante para el parsing (posicional, default, *, **)
parameter_item: pos_param | default_param | star_param | double_star_param
pos_param: IDENT WS? type_hint?
default_param: IDENT WS? type_hint? WS? IGUAL WS? expr
// star_param y double_star_param son tokens STAR y DOUBLE_STAR seguidos de IDENT, handled by _convertir_nodo.

// Definición de Clase
// El cuerpo de la clase es una secuencia de class_body_element dentro de un block.
class_def: CLASE_KW WS? IDENT WS? inheritance? WS? block
inheritance: DESDE WS? inheritance_list
class_body_element: decorator | func_def | class_def | MULTILINE_STRING | class_attribute | stmt
class_attribute: IDENT WS? type_hint? WS? IGUAL WS? expr WS? SEMICOLON // Class attributes often require initialization.


// Sentencias de Importación
importar: import_module | from_import
import_module: IMPORT_KW WS? access WS? SEMICOLON // importar modulo.submodulo;
from_import: DESDE WS? access WS? IMPORT_KW WS? (imported_names_list | STAR) WS? SEMICOLON // desde modulo importar nombre, nombre2; desde modulo importar *;


// =============================================================================
// TIPOS (para Type Hinting)
// =============================================================================

type: basic_type | collection_type | union_type | forward_ref

// Tipos básicos (nombres que son simplemente accesos, ej. int, str, bool, MiClase)
basic_type: access

// Tipos de colección y otros tipos especiales que pueden tener argumentos de tipo
// Ejemplos: Lista[int], Diccionario[str, int], Tupla[int, ...], Opcional[str], Matriz[float]
collection_type: collection_type_name WS? type_arguments_suffix?
collection_type_name: LIST_TYPE | DICT_TYPE | TUPLE_TYPE | SET_TYPE | OPTIONAL_TYPE | RESULTADO_TYPE | MATRIZ_TYPE | TENSOR_TYPE | LLAMABLE_TYPE

// Argumentos de tipo para colecciones (ej. [int, str])
type_arguments_suffix: LBRACKET WS? type_arguments? WS? RBRACKET

// Tokens para nombres de tipos comunes (pueden mapear a typing, numpy, tensorflow)
LIST_TYPE: "Lista"
DICT_TYPE: "Diccionario"
TUPLE_TYPE: "Tupla"
SET_TYPE: "Conjunto"
OPTIONAL_TYPE: "Opcional" // Mapea a typing.Optional
RESULTADO_TYPE: "Resultado" // Placeholder, might map to typing.Any or a custom Result type
MATRIZ_TYPE: "Matriz" // Mapea a np.ndarray
TENSOR_TYPE: "Tensor" // Mapea a tf.Tensor
LLAMABLE_TYPE: "Llamable" // Mapea a typing.Callable

// Tipo Union (ej. Union[int, str])
union_type: UNION_TYPE WS? LBRACKET WS? type_arguments WS? RBRACKET
UNION_TYPE: "Union"

// Forward references (para tipos definidos más adelante, ej. 'MiClase')
forward_ref: QUOTE IDENT QUOTE


// =============================================================================
// EXPRESIONES
// Define el orden de precedencia de operadores.
// =============================================================================

// Nivel superior de expresión (puede ser una lambda o un ternario o una expresión simple)
expr: lambda_expr | ternary

// Operador Ternario (condicion ? verdadero : falso)
ternary: bool_or (WS? QUESTION WS? bool_or WS? COLON WS? bool_or)?

// Operadores Booleanos (or, and, not) - De menor a mayor precedencia
bool_or: bool_and (WS? O_OP WS? bool_and)*
bool_and: not_expr (WS? Y_OP WS? not_expr)*
not_expr: [NO_OP WS?] comparison

// Operadores de Comparación, Pertenencia, Identidad
comparison: bitwise_or_expr ((WS? COMP_OP WS? bitwise_or_expr) | (WS? MEMBERSHIP_OP WS? bitwise_or_expr) | (WS? IDENTITY_OP WS? bitwise_or_expr))*
COMP_OP: LE | GE | EQ | NE | LT | GT
MEMBERSHIP_OP: EN_KW | NO_EN // in, not in
IDENTITY_OP: ES_KW | ES_NO     // is, is not

// Operadores Bitwise - De menor a mayor precedencia
bitwise_or_expr: bitwise_xor_expr (WS? PIPE_OP WS? bitwise_xor_expr)*
bitwise_xor_expr: bitwise_and_expr (WS? CARET_OP WS? bitwise_and_expr)*
bitwise_and_expr: shift_expr (WS? AMPERSAND_OP WS? shift_expr)*

// Operadores de Desplazamiento (Shift)
shift_expr: additive_expr ((WS? LSHIFT_OP WS? additive_expr) | (WS? RSHIFT_OP WS? additive_expr))*

// Operadores Aritméticos (Suma, Resta, Multiplicación, División, Módulo, etc.) - De menor a mayor precedencia
additive_expr: multiplicative_expr ((WS? PLUS WS? multiplicative_expr) | (WS? MINUS WS? multiplicative_expr))*
multiplicative_expr: unary_expr ((WS? STAR WS? unary_expr) | (WS? SLASH WS? unary_expr) | (WS? PERCENT WS? unary_expr) | (WS? DOUBLE_SLASH WS? unary_expr) | (WS? AT_OP WS? unary_expr))* // Added AT_OP

// Operadores Unarios (Signo, Not bitwise)
unary_expr: [UNARY_OP WS?] power
UNARY_OP: MINUS | PLUS | TILDE_OP // Minus/Plus as unary, Bitwise NOT (~)

// Operador de Potencia (Derecha asociativa)
// power: access (WS? DOUBLE_STAR WS? power)? // Right-associative pattern
// Using left-associative pattern matching the _handle_binary_op logic:
power: access (WS? DOUBLE_STAR WS? unary_expr)*

// Acceso a elementos: acceso a atributos (.), indexación ([]), llamadas a función/método ()
// Combina una expresión primaria con cero o más sufijos de acceso.
access: primary (WS? DOT_ACCESS | WS? INDEX_ACCESS | WS? CALL_SUFFIX)*
DOT_ACCESS: DOT WS? IDENT
INDEX_ACCESS: LBRACKET WS? slice_expr WS? RBRACKET
CALL_SUFFIX: LPAR WS? argument_list? WS? RPAR

// Regla para definir slices en indexación [start:stop:step]
// Permite partes opcionales y hasta dos puntos.
slice_expr: slice_part_opt (WS? COLON WS? slice_part_opt)? (WS? COLON WS? slice_part_opt)? -> slice_items
slice_part_opt: expr? // Una parte opcional del slice (inicio, fin, paso)


// Expresiones Primarias
// Son los "átomos" de las expresiones: literales, identificadores, expresiones entre paréntesis, etc.
primary: numero | cadena | MULTILINE_STRING | list_literal | dict_literal | tuple_literal | set_literal | new_instance | NINGUNO_KW | IDENT | LPAR WS? expr WS? RPAR
       | list_comprehension | dict_comprehension | set_comprehension | generator_expression
       | imaginary_literal | complex_literal // Added complex and imaginary literals

// Literales de Colecciones
list_literal: LBRACKET WS? expression_list? WS? RBRACKET -> list_literal_expr
dict_literal: LBRACE WS? key_value_list? WS? RBRACE -> dict_literal_expr
// Tuple literal: () or (expr,) or (expr, expr, ...)
tuple_literal: LPAR WS? expression_list? WS? RPAR -> tuple_literal_expr # Ambiguous with (expr), handle in transformer.
// Set literal: {expr, expr, ...} (requires at least one item)
set_literal: LBRACE WS? non_empty_expression_list WS? RBRACE -> set_literal_expr
non_empty_expression_list: expr (WS? COMA WS? expr)* [WS? COMA]? -> expression_list_items // Re-use expression_list_items name

// Comprensiones de Lista, Diccionario y Conjunto, y Expresiones Generadoras
// Siguen el patrón: [expr for ... if ...] etc.
list_comprehension: LBRACKET WS? expr WS? comprehension_for WS? RBRACKET -> list_comprehension_expr
dict_comprehension: LBRACE WS? key_value WS? comprehension_for WS? RBRACE -> dict_comprehension_expr // Dict comprehension uses key_value
set_comprehension: LBRACE WS? expr WS? comprehension_for WS? RBRACE -> set_comprehension_expr
generator_expression: LPAR WS? expr WS? comprehension_for WS? RPAR -> generator_expression_expr

// La cláusula for de las comprensiones/generadores
comprehension_for: PARA_KW WS? IDENT WS? EN_KW WS? expr WS? comprehension_if? -> comprehension_for_clause
// La cláusula if opcional de las comprensiones/generadores
comprehension_if: SI_KW WS? expr -> comprehension_if_clause

// Expresión Lambda (lambda [parametros]: expresion)
lambda_expr: LAMBDA_KW WS? parameter_list? WS? COLON WS? expr -> lambda_expr_definition

// Creación de Instancia (nueva MiClase(...) )
new_instance: NUEVA_KW WS? access WS? CALL_SUFFIX -> new_instance_creation