# castella_transformer.py

"""
Transformer para convertir el Árbol de Sintaxis Abstracta (AST) de Lark
generado por la gramática Castella en código Python.
Incluye soporte para las estructuras y operadores definidos en castella_grammar.py.
"""

from lark import Transformer, Tree, Token
# Importaciones necesarias para los tipos usados en type hints
from typing import Optional, Union, Any, List, Dict, Tuple, Set, Callable
# Importaciones para mapear tipos de Castella a Python (ej. Matriz -> np.ndarray)
import numpy as np
# Add tensorflow import example if Tensor type hint is used
# Use a try-except block in the generated code's preamble, but just import here if needed by transformer itself.
# The transformer only needs np and tf for string generation like "np.ndarray".
try:
    import tensorflow as tf
except ImportError:
    # Define a dummy object if tensorflow is not installed, so the transformer code runs.
    class tf:
        class Tensor: pass # Need a placeholder for the class used in string formatting.


# Note: The necessary imports for the *generated Python code* (like math, matplotlib.pyplot, requests, tensorflow try/except)
# are added as a preamble in the `start` method of this transformer, not imported here.

class CastellaTransformer(Transformer):
    """
    Transforma el árbol de sintaxis de Lark a código Python.
    """
    INDENT_SPACES = 4 # Define el número de espacios para la indentación en Python.

    def _indent_lines(self, lines_list: list[str], level: int) -> str:
        """
        Añade indentación a una lista de líneas de código.

        Args:
            lines_list: Una lista de strings (líneas de código) o un solo string.
                        Puede contener None o strings vacíos.
            level: El nivel de indentación (cada nivel añade INDENT_SPACES).

        Returns:
            Una sola cadena con las líneas indentadas y unidas por saltos de línea.
            Si la lista resultante está vacía, devuelve una línea con 'pass' indentado.
        """
        # Ensure input is list; handles None and single strings defensively.
        if not isinstance(lines_list, list):
             if lines_list is None: lines_list = []
             elif isinstance(lines_list, str): lines_list = [lines_list]
             else:
                   # If conversion to string fails, it's a significant internal error.
                   try: lines_list = [str(lines_list)]
                   except Exception:
                         raise TypeError(f"Error interno: Tipo de entrada inesperado para _indent_lines que no puede convertirse a str: {type(lines_list)}")

        filtered_lines = []
        for item_str in lines_list:
             if item_str is not None:
                  try:
                       # Ensure each item is treated as a string before splitting lines.
                       lines_from_item = str(item_str).splitlines()
                       for line in lines_from_item:
                            # Only include non-empty lines after stripping whitespace.
                            if line.strip():
                                filtered_lines.append(line)
                  except Exception as e:
                       # If an item causes error during str conversion, it's likely an internal translation bug.
                       raise TypeError(f"Error interno: Cannot convert translated item '{item_str!r}' (type {type(item_str)}) to string for indentation.") from e


        if not filtered_lines:
            # If the block is empty after filtering (e.g., just comments, or empty block {}), add 'pass'.
            return " " * self.INDENT_SPACES * level + "pass"

        indent_str = " " * self.INDENT_SPACES * level
        # Prepend indentation to each filtered line.
        indented_output = [indent_str + line for line in filtered_lines]
        return "\n".join(indented_output)


    def _convertir_nodo(self, nodo):
        """
        Convierte un nodo de Lark (Token o Tree) a su representación en Python.
        Delega a los métodos específicos del transformer para nodos Tree.
        Maneja la traducción directa para nodos Token.
        """
        if isinstance(nodo, (str, list)):
             # If it's already a string or list (presumably translated), return it directly.
             return nodo
        elif isinstance(nodo, Token):
            # Handle specific Terminal types or generic ones based on their type.
            # Most terminals just return their value (e.g. "let", "+", "(", IDENT string).
            # Some require specific translation (True/False, None, Multiline String content).

            # Explicit keyword translations
            if nodo.type == 'VERDADERO_KW': return "True" # Castella True -> Python True
            if nodo.type == 'FALSO_KW': return "False"   # Castella False -> Python False
            if nodo.type == 'NONE_KW': return "None"     # Castella nulo -> Python None

            # Multiline String conversion ### -> """
            if nodo.type == 'MULTILINE_STRING':
                 matched_text = nodo.value
                 if matched_text.startswith('###') and matched_text.endswith('###'):
                      # Remove the '###' delimiters and wrap in '"""' for Python docstrings/multiline strings.
                      return '"""' + matched_text[3:-3] + '"""'
                 # Fallback if format unexpected (shouldn't happen with correct regex).
                 return matched_text

            # Basic Terminals defined by regex (numbers, strings, identifiers). Return their raw value.
            # This includes the new complex and imaginary literals.
            if nodo.type in ['numero', 'cadena', 'imaginary_literal', 'complex_literal']:
                 return nodo.value

            if nodo.type == 'IDENT': return nodo.value   # Keep identifier string

            # Operators, Punctuation, Keywords that map directly to Python syntax.
            # Return their value as is (which is the string defined in the grammar).
            if nodo.type in ['PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT', 'DOUBLE_STAR', 'DOUBLE_SLASH',
                             'LSHIFT_OP', 'RSHIFT_OP', 'AMPERSAND_OP', 'CARET_OP', 'PIPE_OP', 'TILDE_OP',
                             'QUESTION', 'COLON', 'SEMICOLON', 'COMA', 'DOT', 'LPAR', 'RPAR', 'LBRACKET', 'RBRACKET',
                             'LBRACE', 'RBRACE', 'ARROBA', 'QUOTE', 'IGUAL', 'AT_OP']: # Added AT_OP
                 return nodo.value # e.g., "+" -> "+", "(" -> "(", "=" -> "=", "@" -> "@"

            # Comparison, Membership, Identity Operators
            # Their values are already the correct Python operators like "<=", "in", "is", except for negated ones.
            if nodo.type in ['LE', 'GE', 'EQ', 'NE', 'LT', 'GT', 'IN_KW', 'NO_EN', 'IS_KW', 'ES_NO']:
                 # Map Castella keywords like 'no en' to Python 'not in', 'es no' to 'is not'.
                 if nodo.type == 'NO_EN': return "not in"
                 if nodo.type == 'ES_NO': return "is not"
                 return nodo.value # Returns "<=", ">=", "==", "!=", "<", ">", "in", "is"

            # Augmented Assignment Operators
            # Their values are already the correct Python operators like "+=", "-=".
            if nodo.type in ['PLUS_EQUAL', 'MINUS_EQUAL', 'STAR_EQUAL', 'SLASH_EQUAL', 'PERCENT_EQUAL', 'DOUBLE_STAR_EQUAL',
                             'DOUBLE_SLASH_EQUAL', 'AMPERSAND_EQUAL', 'PIPE_EQUAL', 'CARET_EQUAL', 'LSHIFT_EQUAL', 'RSHIFT_EQUAL', 'AT_EQUAL']: # Added AT_EQUAL
                 return nodo.value # Returns "+=", "-=", etc.

            # Control Flow Keywords and other simple keywords that map directly.
            if nodo.type in ['ROMPER', 'CONTINUAR', 'PASAR']:
                # These map directly to their Python equivalents.
                if nodo.type == 'ROMPER': return "break"
                if nodo.type == 'CONTINUAR': return "continue"
                if nodo.type == 'PASAR': return "pass"
                # Note: IMPRIMIR, IMPORT_KW, DESDE, etc., are handled in their specific rule methods.

            # Type Keyword Terminals - Handled in type rules, returning value is intermediate.
            if nodo.type in ['LIST_TYPE', 'DICT_TYPE', 'TUPLE_TYPE', 'SET_TYPE', 'OPTIONAL_TYPE', 'RESULTADO_TYPE',
                             'MATRIZ_TYPE', 'TENSOR_TYPE', 'UNION_TYPE', 'LLAMABLE_TYPE']:
                 return nodo.value

            # Logical Operators (or, and, not) - Handled in expression rules, values are correct.
            if nodo.type in ['OR_OP', 'AND_OP', 'NOT_OP']:
                 return nodo.value

            # If we reach here, it's a Token type not explicitly handled but wasn't ignored.
            # Should ideally not happen if all terminals are covered or ignored.
            # Fallback: return the token's value string.
            # print(f"Warning: Unhandled Token type in _convertir_nodo: {nodo.type} with value {nodo.value!r}. Returning value.")
            return nodo.value


        elif isinstance(nodo, Tree):
            # If it's a Tree (represents a rule), find the corresponding transformer method.
            transformer_method = getattr(self, nodo.data, None)
            if transformer_method is None:
                  # If method for rule name (nodo.data) is not found, it's an unimplemented rule.
                  raise NotImplementedError(f"No hay método de transformer definido para la regla '{nodo.data}'")

            # Call the method, passing the node's children as arguments.
            return transformer_method(nodo.children)

        elif nodo is None:
             # Represents an optional part of the grammar that was not matched.
             return None

        else:
             # If node is none of expected types, it's an internal error.
             raise TypeError(f"Error interno del transformer: Tipo de nodo inesperado: {type(nodo)} - {nodo}")

    def _handle_binary_op(self, args):
        """
        Maneja la traducción de reglas de operadores binarios como `subrule (OPERATOR subrule)*`.
        Construye la cadena de expresión resultante.
        """
        if not args: return ""
        if len(args) == 1:
             return self._convertir_nodo(args[0])

        result = self._convertir_nodo(args[0])

        i = 1
        while i < len(args):
            if i + 1 >= len(args):
                 # This shouldn't happen with a correct grammar but is a safety check.
                 raise ValueError(f"Error interno: Expresión binaria incompleta detectada en el transformer. Nodo en el índice {i}: {args[i]}")

            op_node = args[i]
            right_node = args[i+1]

            op_str = self._convertir_nodo(op_node)
            right_str = self._convertir_nodo(right_node)

            if op_str is None: op_str = ""
            if right_str is None: right_str = ""

            # Add spaces around operators for readability in Python code.
            result = f"{result} {op_str} {right_str}"

            i += 2

        return result


    # === TOP LEVEL ===

    def start(self, items):
        """
        Procesa los elementos de nivel superior (definiciones, sentencias, decoradores).
        Añade el preámbulo de Python (imports, etc.).
        """
        translated_output_lines = []
        pending_decorators = []

        # Add standard Python imports at the top of the generated file.
        import_preamble = "# -*- coding: utf-8 -*-\n"
        import_preamble += "# Traducción de Castella a Python\n"
        import_preamble += "# Imports necesarios para tipos y librerías traducidas/utilizadas\n"
        import_preamble += "import sys\n"
        import_preamble += "import os\n"
        import_preamble += "import shutil\n"
        import_preamble += "import subprocess\n"
        import_preamble += "import re\n"
        # Import necessary types from typing module
        import_preamble += "from typing import Optional, Union, Any, List, Dict, Tuple, Set, Callable\n"
        # Import math if trigonometric/math functions are expected (common in complex calculations)
        import_preamble += "import math\n"
        # Imports for specific mapped types and common calculation libraries
        import_preamble += "import numpy as np\n" # Matriz -> np.ndarray, used in calculations
        import_preamble += "import matplotlib.pyplot as plt\n" # Needed if `graficar` translates to matplotlib calls
        # import_preamble += "import requests\n" # Keep if potentially used by Castella standard library features
        # Example import for Tensor type hint - include placeholder if not installed
        import_preamble += "try:\n    import tensorflow as tf\nexcept ImportError:\n    class tf: # Placeholder if tf is not installed\n        class Tensor: pass\n    # print('Warning: tensorflow not found. Tensor type hint might not work correctly.') # Avoid printing from translated code\n"

        import_preamble += "\n"

        translated_output_lines.append(import_preamble)

        for item in items:
            if isinstance(item, Token) and item.type in ['WS', 'LINE_COMMENT']:
                 continue

            if isinstance(item, Tree) and item.data == 'decorator':
                translated_decorator = self._convertir_nodo(item)
                if translated_decorator:
                    pending_decorators.append(translated_decorator)
                continue

            if isinstance(item, Tree) and item.data in ['func_def', 'class_def']:
                for decorator_line in pending_decorators:
                    translated_output_lines.append(decorator_line)
                pending_decorators = []

                translated_item = self._convertir_nodo(item)

                if translated_item is not None:
                     translated_output_lines.append(str(translated_item))

            elif isinstance(item, Token) and item.type == 'MULTILINE_STRING':
                 if pending_decorators:
                      raise ValueError(f"Error de gramática: Decoradores ('{pending_decorators[0]}') no pueden preceder a un docstring a nivel superior.")
                 translated_item = self._convertir_nodo(item)
                 if translated_item is not None:
                      translated_output_lines.append(str(translated_item))

            elif isinstance(item, Tree) and item.data == 'stmt':
                if pending_decorators:
                    stmt_type_node = item.children[0] if item.children else None
                    stmt_type_desc = getattr(stmt_type_node, 'data', getattr(stmt_type_node, 'type', 'UnknownStatementType'))
                    decorator_example = pending_decorators[0]
                    raise ValueError(f"Error de gramática: Decoradores ('{decorator_example}') deben preceder inmediatamente una definición de función o clase. Encontrada una sentencia de tipo '{stmt_type_desc}' en su lugar a nivel superior.")

                translated_item = self._convertir_nodo(item)

                if translated_item is not None:
                    translated_output_lines.append(str(translated_item))

            else:
                # Handle other unexpected top-level node types defensively.
                node_data = getattr(item, 'data', 'N/A')
                node_type = type(item)
                node_value = getattr(item, 'value', 'N/A')
                # In a real compiler, you might log this or raise a more specific error.
                # print(f"Debug: Unexpected node type at top level: Data={node_data}, Type={node_type}, Value={node_value}. Item: {item}")
                pass # Skip unexpected nodes but continue.


        if pending_decorators:
             decorator_example = pending_decorators[0]
             raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) sin una definición de función o clase que los siga al final del archivo.")

        python_lines = [line.rstrip() for line in translated_output_lines if line is not None]
        while python_lines and not python_lines[-1].strip():
             python_lines.pop()
        python_lines.append('')

        return "\n".join(python_lines)

    # === STATEMENT RULES ===

    def stmt(self, args):
         if len(args) != 1:
              raise ValueError(f"Error interno: Regla 'stmt' del transformer recibió un número de argumentos inesperado ({len(args)}). Args: {args}")
         return self._convertir_nodo(args[0])

    def asignacion(self, args): # access IGUAL expr SEMICOLON
        # Structure: [Tree('access'), Token(IGUAL), Tree('expr'), Token(SEMICOLON)]
        if len(args) != 4 or not isinstance(args[0], Tree) or args[0].data != 'access' or not isinstance(args[1], Token) or args[1].type != 'IGUAL' or not isinstance(args[2], Tree) or args[2].data != 'expr' or not isinstance(args[3], Token) or args[3].type != 'SEMICOLON':
             raise ValueError(f"Error en asignacion: Estructura incorrecta. Esperado [access, IGUAL, expr, SEMICOLON]. Recibido: {args}")

        target_access_str = self._convertir_nodo(args[0])
        value_expr_str = self._convertir_nodo(args[2])

        return f"{target_access_str} = {value_expr_str}"

    def declaracion(self, args): # LET_KW IDENT [COLON type] IGUAL expr SEMICOLON
        # Structure: [Token(LET_KW), Token(IDENT), ..., Token(IGUAL), Tree('expr'), Token(SEMICOLON)]
        # Translation is a standard Python assignment with optional type hint.
        if not isinstance(args[0], Token) or args[0].type != 'LET_KW' or not isinstance(args[1], Token) or args[1].type != 'IDENT' or not isinstance(args[-1], Token) or args[-1].type != 'SEMICOLON':
             raise ValueError(f"Error en declaracion: Estructura inicial o final incorrecta (LET_KW/IDENT/SEMICOLON). Recibido: {args}")

        expr_node = args[-2]
        if not isinstance(expr_node, Tree) or expr_node.data != 'expr':
             raise ValueError(f"Error en declaracion: Estructura incorrecta. Esperado 'expr' antes de SEMICOLON. Recibido {expr_node} en posición [-2]. Args: {args}")

        type_node = None

        # Find the IGUAL token position.
        igual_idx = -3
        if len(args) < 3 or not isinstance(args[igual_idx], Token) or args[igual_idx].type != 'IGUAL':
             raise ValueError(f"Error en declaracion: Token IGUAL no encontrado en la posición esperada. Esperado antes de expr y SEMICOLON. Args: {args}")

        # Check for type hint between IDENT (args[1]) and IGUAL (args[igual_idx]).
        nodes_between_ident_and_igual = args[2:igual_idx]

        if nodes_between_ident_and_igual:
             if len(nodes_between_ident_and_igual) == 2 and isinstance(nodes_between_ident_and_igual[0], Token) and nodes_between_ident_and_igual[0].type == 'COLON' and isinstance(nodes_between_ident_and_igual[1], Tree) and nodes_between_ident_and_iguales[1].data == 'type':
                  type_node = nodes_between_ident_and_iguales[1]
             else:
                 raise ValueError(f"Error en declaracion: Estructura incorrecta para declaración con tipo. Esperado [COLON, type] entre IDENT y IGUAL. Recibido: {nodes_between_ident_and_igual}. Args: {args}")

        var_name = self._convertir_nodo(args[1])
        value_expr_str = self._convertir_nodo(expr_node)

        type_hint_str = ""
        if type_node:
             translated_type = self._convertir_nodo(type_node)
             if translated_type:
                  type_hint_str = f": {translated_type}"

        return f"{var_name}{type_hint_str} = {value_expr_str}"


    def unpack_assignment(self, args): # unpack_target_list_or_single IGUAL expr SEMICOLON
        if len(args) != 4 or not isinstance(args[0], Tree) or args[0].data != 'unpack_target_list_or_single' or not isinstance(args[1], Token) or args[1].type != 'IGUAL' or not isinstance(args[2], Tree) or args[2].data != 'expr' or not isinstance(args[3], Token) or args[3].type != 'SEMICOLON':
             raise ValueError(f"Error en unpack_assignment: Estructura incorrecta. Esperado [target_node, IGUAL, expr, SEMICOLON]. Recibido: {args}")

        target_node = args[0]
        expr_node = args[2]

        translated_target = self._convertir_nodo(target_node)
        translated_expr = self._convertir_nodo(expr_node)

        return f"{translated_target} = {translated_expr}"

    def unpack_target_list_or_single(self, args):
         if len(args) == 1 and isinstance(args[0], Tree) and args[0].data == 'list_literal_target':
              return self._convertir_nodo(args[0])

         else:
              content_nodes = [arg for arg in args if not (isinstance(arg, Token) and arg.type == 'WS')]
              unpack_target_nodes = [arg for arg in content_nodes if isinstance(arg, Tree) and arg.data == 'unpack_target']
              has_trailing_comma = content_nodes and isinstance(content_nodes[-1], Token) and content_nodes[-1].type == 'COMA'

              translated_targets = [self._convertir_nodo(node) for node in unpack_target_nodes]

              result = ", ".join(translated_targets)

              if has_trailing_comma:
                   result += ","

              return result

    def unpack_target(self, args):
         if len(args) == 1 and isinstance(args[0], Token) and args[0].type == 'IDENT':
              return self._convertir_nodo(args[0])

         elif len(args) == 3 and isinstance(args[0], Token) and args[0].type == 'LPAR' and isinstance(args[2], Token) and args[2].type == 'RPAR' and isinstance(args[1], Tree) and args[1].data == 'unpack_target_list':
              inner_targets = self._convertir_nodo(args[1])
              return f"({inner_targets})"

         else:
              raise ValueError(f"Error interno: Estructura inesperada en unpack_target. Esperaba IDENT o (unpack_target_list). Recibido: {args}")

    def unpack_target_list(self, args):
        return ", ".join(self._convertir_nodo(arg) for arg in args)

    def list_literal_target(self, args):
         if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'LBRACKET' or not isinstance(args[2], Token) or args[2].type != 'RBRACKET' or not isinstance(args[1], Tree) or args[1].data != 'unpack_target_list':
              raise ValueError(f"Error en list_literal_target: Estructura incorrecta. Esperaba LBRACKET, unpack_target_list, RBRACKET. Recibido: {args}")
         target_list_node = args[1]
         if not isinstance(target_list_node, Tree) or target_list_node.data != 'unpack_target_list':
              raise ValueError(f"Error interno: Se esperaba un nodo unpack_target_list entre los corchetes. Recibido: {target_list_node}")

         inner_targets = self._convertir_nodo(target_list_node)
         return f"[{inner_targets}]"


    def print_stmt(self, args): # IMPRIMIR LPAR [expr (COMMA expr)*] RPAR SEMICOLON
         if not isinstance(args[0], Token) or args[0].type != 'IMPRIMIR' or not isinstance(args[1], Token) or args[1].type != 'LPAR' or not isinstance(args[-2], Token) or args[-2].type != 'RPAR' or not isinstance(args[-1], Token) or args[-1].type != 'SEMICOLON':
              raise ValueError(f"Error en print_stmt: Estructura incorrecta. Esperado IMPRIMIR, LPAR, ..., RPAR, SEMICOLON. Recibido: {args}")

         content_nodes = args[2:-2]
         expr_nodes = [arg for arg in content_nodes if isinstance(arg, Tree) and arg.data == 'expr']

         translated_exprs = [self._convertir_nodo(node) for node in expr_nodes]
         translated_exprs_str = ", ".join(translated_exprs)

         return f"print({translated_exprs_str})"


    def expr_stmt(self, args): # expr SEMICOLON
        if len(args) != 2 or not isinstance(args[0], Tree) or args[0].data != 'expr' or not isinstance(args[1], Token) or args[1].type != 'SEMICOLON':
             raise ValueError(f"Error en expr_stmt: Estructura incorrecta. Esperado [expr, SEMICOLON]. Recibido: {args}")
        return self._convertir_nodo(args[0])

    def call_stmt(self, args): # access SEMICOLON
         if len(args) != 2 or not isinstance(args[0], Tree) or args[0].data != 'access' or not isinstance(args[1], Token) or args[1].type != 'SEMICOLON':
              raise ValueError(f"Error en call_stmt: Estructura incorrecta. Esperado [access, SEMICOLON]. Recibido: {args}")
         translated_access = self._convertir_nodo(args[0])
         return translated_access

    def augmented_assignment(self, args): # access AUG_ASSIGN_OP expr SEMICOLON
        if len(args) != 4 or not isinstance(args[0], Tree) or args[0].data != 'access' or not isinstance(args[1], Token) or args[1].type != 'AUG_ASSIGN_OP' or not isinstance(args[2], Tree) or args[2].data != 'expr' or not isinstance(args[3], Token) or args[3].type != 'SEMICOLON':
             raise ValueError(f"Error en augmented_assignment: Estructura incorrecta. Esperado [access, AUG_ASSIGN_OP, expr, SEMICOLON]. Recibido: {args}")

        access_target_str = self._convertir_nodo(args[0])
        op_str = self._convertir_nodo(args[1]) # AUG_ASSIGN_OP token value is already correct.
        value_expr_str = self._convertir_nodo(args[2])

        return f"{access_target_str} {op_str} {value_expr_str}"

    # Note: BREAK, CONTINUE, PASS_KW rule methods are handled by _convertir_nodo
    # mapping ROMPER, CONTINUAR, PASAR tokens to "break", "continue", "pass".
    # The grammar rules are `BREAK: ROMPER WS? SEMICOLON`, etc.
    # The `stmt` rule will match these. The `stmt` method delegates to the rule name.
    # So methods named `BREAK`, `CONTINUE`, `PASS_KW` are needed, and they receive
    # the specific token and the SEMICOLON token. Let's add them explicitly for clarity.

    def BREAK(self, args): # ROMPER SEMICOLON (after ignoring WS) -> [Token(BREAK), Token(SEMICOLON)]
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'BREAK' or not isinstance(args[1], Token) or args[1].type != 'SEMICOLON':
             raise ValueError(f"Error en BREAK: Estructura incorrecta. Esperado [BREAK, SEMICOLON]. Recibido: {args}")
        return "break"

    def CONTINUE(self, args): # CONTINUAR SEMICOLON (after ignoring WS) -> [Token(CONTINUE), Token(SEMICOLON)]
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'CONTINUE' or not isinstance(args[1], Token) or args[1].type != 'SEMICOLON':
             raise ValueError(f"Error en CONTINUE: Estructura incorrecta. Esperado [CONTINUE, SEMICOLON]. Recibido: {args}")
        return "continue"

    def PASS_KW(self, args): # PASAR SEMICOLON (after ignoring WS) -> [Token(PASS_KW), Token(SEMICOLON)]
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'PASS_KW' or not isinstance(args[1], Token) or args[1].type != 'SEMICOLON':
             raise ValueError(f"Error en PASS_KW: Estructura incorrecta. Esperado [PASS_KW, SEMICOLON]. Recibido: {args}")
        return "pass"


    def return_stmt(self, args): # RETURN_KW [expr] SEMICOLON
        # Structure: [Token(RETURN_KW), Tree('expr')?, Token(SEMICOLON)]
        if not isinstance(args[0], Token) or args[0].type != 'RETURN_KW' or not isinstance(args[-1], Token) or args[-1].type != 'SEMICOLON':
             raise ValueError(f"Error en return_stmt: Estructura inicial/final incorrecta (RETURN_KW/SEMICOLON). Recibido: {args}")

        expr_node = args[1] if len(args) == 3 else None
        if len(args) == 3 and (not isinstance(expr_node, Tree) or expr_node.data != 'expr'):
             raise ValueError(f"Error en return_stmt: Si hay 3 argumentos, el 2ndo debe ser expr. Recibido {expr_node}. Args: {args}")
        elif len(args) not in [2, 3]:
             raise ValueError(f"Error en return_stmt: Número de argumentos inesperado ({len(args)}). Esperado 2 o 3. Args: {args}")

        translated_expr_str = self._convertir_nodo(expr_node) if expr_node is not None else ""

        return f"return {translated_expr_str}".strip()


    # === BLOCK AND CONTROL FLOW RULES ===

    def block(self, args):
         # block: LBRACE (MULTILINE_STRING | decorator | class_def | func_def | stmt)* RBRACE
         # args contain the nodes inside the braces, potentially including WS and LINE_COMMENT.
         translated_block_elements = []
         pending_decorators = []

         for item_node in args:
              if isinstance(item_node, Token) and item_node.type in ['WS', 'LINE_COMMENT', 'LBRACE', 'RBRACE']:
                  continue

              if isinstance(item_node, Tree) and item_node.data == 'decorator':
                   translated_decorator = self._convertir_nodo(item_node)
                   if translated_decorator:
                       pending_decorators.append(translated_decorator)
                   continue

              # Handle definitions (functions, classes) which can be decorated.
              if isinstance(item_node, Tree) and item_node.data in ['func_def', 'class_def'] :
                 if pending_decorators:
                      for decorator_line in pending_decorators:
                           translated_block_elements.append(decorator_line)
                      pending_decorators = []

                 translated_element = self._convertir_nodo(item_node)
                 if translated_element is not None:
                     translated_block_elements.append(str(translated_element))

              # Handle multiline strings (docstrings within a block).
              elif isinstance(item_node, Token) and item_node.type == 'MULTILINE_STRING':
                   if pending_decorators:
                       decorator_example = pending_decorators[0]
                       raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) no pueden preceder a una cadena multilínea/docstring dentro de un bloque.")

                   translated_element = self._convertir_nodo(item_node)
                   if translated_element is not None:
                        translated_block_elements.append(str(translated_element))

              # Handle all other statement types and class attributes that can appear in a block.
              elif isinstance(item_node, Tree) and item_node.data in ['stmt', 'class_attribute']: # stmt can appear in class body blocks
                   if pending_decorators:
                       node_type_desc = item_node.data if isinstance(item_node, Tree) else item_node.type
                       decorator_example = pending_decorators[0]
                       raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) sólo pueden preceder definiciones de función o clase anidada dentro del bloque. Encontrado un elemento '{node_type_desc}' sin una definición asociada.")

                   translated_element = self._convertir_nodo(item_node)

                   if translated_element is not None:
                       if isinstance(translated_element, list): # Handle rules like graficar that might return lists
                            translated_block_elements.extend(translated_element)
                       else:
                            translated_block_elements.append(str(translated_element))

              else:
                   # Skip other unexpected nodes but continue.
                   # print(f"Debug: Unexpected node in block: {item_node}")
                   pass


         if pending_decorators:
              decorator_example = pending_decorators[0]
              raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) sin definición de función o clase que los siga al final del bloque.")

         # Return the list of translated block elements. Indentation is applied by the caller (if/for/def etc.).
         return translated_block_elements


    def if_stmt(self, args):
        # if_stmt: IF_KW LPAR expr RPAR block [ELIF_KW LPAR expr RPAR block]* [ELSE_KW block]?
        python_code_parts = []
        i = 0

        while i < len(args):
            keyword_token = args[i]
            if not isinstance(keyword_token, Token) or keyword_token.type not in ['IF_KW', 'ELIF_KW', 'ELSE_KW']:
                raise ValueError(f"Error interno del transformer: Estructura inesperada en if_stmt. Se esperaba IF_KW, ELIF_KW o ELSE_KW. Recibido: {keyword_token} en índice {i}")

            keyword_type = keyword_token.type
            block_node = None
            condition_expr_str = None

            if keyword_type in ['IF_KW', 'ELIF_KW']:
                # Structure: [Keyword, LPAR, expr, RPAR, block]
                if (i + 4 >= len(args) or
                    not isinstance(args[i+1], Token) or args[i+1].type != 'LPAR' or
                    not isinstance(args[i+2], Tree)  or args[i+2].data != 'expr' or
                    not isinstance(args[i+3], Token) or args[i+3].type != 'RPAR' or
                    not isinstance(args[i+4], Tree)  or args[i+4].data != 'block'):
                    keyword_val = keyword_token.value
                    raise ValueError(f"Error en '{keyword_val}': Estructura incorrecta. Esperado LPAR, expr, RPAR, block. Recibido a partir del índice {i+1}: {args[i+1:]}")

                condition_node = args[i+2]
                block_node = args[i+4]
                condition_expr_str = self._convertir_nodo(condition_node)

                python_prefix = 'elif' if keyword_type == 'ELIF_KW' else 'if'
                python_code_parts.append(f"{python_prefix} {condition_expr_str}:")
                i += 5

            elif keyword_type == 'ELSE_KW':
                 # Structure: [Keyword, block]
                 if (i + 1 >= len(args) or
                     not isinstance(args[i+1], Tree) or args[i+1].data != 'block'):
                     raise ValueError(f"Error en '{keyword_token.value}': Estructura incorrecta después del token. Esperado block.")

                 block_node = args[i+1]
                 python_code_parts.append("else:")
                 i += 2

            if not isinstance(block_node, Tree) or block_node.data != 'block':
                raise ValueError(f"Error interno del transformer: Nodo esperado de tipo 'block' no encontrado para indentación después de la cláusula con token '{keyword_token.value}'.")

            block_content_list = self._convertir_nodo(block_node)
            indented_block = self._indent_lines(block_content_list, 1)
            python_code_parts.append(indented_block)

        return "\n".join(python_code_parts)

    def for_stmt(self, args): # FOR_KW IDENT IN_KW expr block
        if (len(args) != 5 or
            not isinstance(args[0], Token) or args[0].type != 'PARA_KW' or
            not isinstance(args[1], Token) or args[1].type != 'IDENT' or
            not isinstance(args[2], Token) or args[2].type != 'EN_KW' or
            not isinstance(args[3], Tree) or args[3].data != 'expr' or
            not isinstance(args[4], Tree) or args[4].data != 'block'):
            raise ValueError(f"Error en for_stmt: Estructura incorrecta. Esperado PARA_KW, IDENT, EN_KW, expr, block. Recibido: {args}")

        var_name = self._convertir_nodo(args[1])
        iterable_expr_str = self._convertir_nodo(args[3])

        block_node = args[4]
        block_content_list = self._convertir_nodo(block_node)
        indented_block = self._indent_lines(block_content_list, 1)

        return f"for {var_name} in {iterable_expr_str}:\n{indented_block}"

    def while_stmt(self, args): # WHILE_KW LPAR expr RPAR block
        if (len(args) != 5 or
            not isinstance(args[0], Token) or args[0].type != 'MIENTRAS_KW' or
            not isinstance(args[1], Token) or args[1].type != 'LPAR' or
            not isinstance(args[2], Tree) or args[2].data != 'expr' or
            not isinstance(args[3], Token) or args[3].type != 'RPAR' or
            not isinstance(args[4], Tree) or args[4].data != 'block'):
            raise ValueError(f"Error en while_stmt: Estructura incorrecta. Esperado MIENTRAS_KW, LPAR, expr, RPAR, block. Recibido: {args}")

        condition_expr_str = self._convertir_nodo(args[2])

        block_node = args[4]
        block_content_list = self._convertir_nodo(block_node)
        indented_block = self._indent_lines(block_content_list, 1)

        return f"while {condition_expr_str}:\n{indented_block}"

    def try_stmt(self, args): # TRY_KW block (except_block)+ [finally_block]?
        if len(args) < 2 or not isinstance(args[0], Token) or args[0].type != 'TRY_KW' or not isinstance(args[1], Tree) or args[1].data != 'block':
             raise ValueError(f"Error en try_stmt: Estructura inicial incorrecta. Esperado TRY_KW block. Recibido: {args}")

        try_block_node = args[1]

        python_code_parts = ["try:"]
        try_content_list = self._convertir_nodo(try_block_node)
        indented_try_block = self._indent_lines(try_content_list, 1)
        python_code_parts.append(indented_try_block)

        i = 2
        seen_finally = False

        while i < len(args):
            current_node = args[i]

            if not isinstance(current_node, Tree):
                 raise TypeError(f"Error interno del transformer: Nodo inesperado en la secuencia try/except/finally. Esperado un Tree. Recibido: {current_node} en índice {i}.")

            if current_node.data == 'except_block':
                if seen_finally:
                     raise ValueError(f"Error de gramática: La cláusula 'capturar' (except) aparece después de la cláusula 'finalmente' (finally) en una sentencia intentar (try).")
                python_code_parts.append(self._convertir_nodo(current_node))
                i += 1
            elif current_node.data == 'finally_block':
                if seen_finally:
                     raise ValueError(f"Error de gramática: Múltiples cláusulas 'finalmente' (finally) en una sentencia intentar (try).")
                seen_finally = True
                python_code_parts.append(self._convertir_nodo(current_node))
                i += 1
            else:
                raise ValueError(f"Error interno del transformer: Nodo inesperado en la secuencia try/except/finally. Esperado 'except_block' o 'finally_block'. Recibido: {current_node.data}")
        return "\n".join(python_code_parts)


    def except_block(self, args): # CATCH_KW [access [COMO IDENT]] block
        if not isinstance(args[0], Token) or args[0].type != 'CATCH_KW' or not isinstance(args[-1], Tree) or args[-1].data != 'block':
             raise ValueError(f"Error en except_block: Estructura inicial/final incorrecta. Esperado CATCH_KW ... block. Recibido: {args}")

        block_node = args[-1]
        block_content_list = self._convertir_nodo(block_node)
        indented_block = self._indent_lines(block_content_list, 1)

        except_line = "except"
        nodes_between = args[1:-1]

        if nodes_between:
            if not isinstance(nodes_between[0], Tree) or nodes_between[0].data != 'access':
                raise ValueError(f"Error en except_block: Estructura incorrecta después de CATCH_KW. Se esperaba un 'access' para el tipo de excepción. Recibido: {nodes_between[0]}")
            error_type_str = self._convertir_nodo(nodes_between[0])
            except_line += f" {error_type_str}"

            if len(nodes_between) > 1:
                if len(nodes_between) != 3 or not isinstance(nodes_between[1], Token) or nodes_between[1].type != 'COMO' or not isinstance(nodes_between[2], Token) or nodes_between[2].type != 'IDENT':
                    raise ValueError(f"Error en except_block: Estructura incorrecta para la cláusula 'como'. Se esperaba COMO IDENT después del tipo de excepción. Recibido: {nodes_between[1:]}")
                error_var_str = self._convertir_nodo(nodes_between[2])
                except_line += f" as {error_var_str}"

        except_line += ":"

        return f"{except_line}\n{indented_block}"

    def finally_block(self, args): # FINALLY_KW block
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'FINALLY_KW' or not isinstance(args[1], Tree) or args[1].data != 'block':
             raise ValueError(f"Error en finally_block: Estructura incorrecta. Esperado [FINALLY_KW, block]. Recibido: {args}")
        block_node = args[1]
        block_content_list = self._convertir_nodo(block_node)
        indented_block = self._indent_lines(block_content_list, 1)
        return f"finally:\n{indented_block}"

    def with_stmt(self, args): # WITH_KW expr [COMO IDENT] block
        if not isinstance(args[0], Token) or args[0].type != 'WITH_KW' or not isinstance(args[-1], Tree) or args[-1].data != 'block':
             raise ValueError(f"Error en with_stmt: Estructura inicial/final incorrecta. Esperado WITH_KW ... block. Recibido: {args}")

        context_expr_node = args[1]
        if not isinstance(context_expr_node, Tree) or context_expr_node.data != 'expr':
             raise ValueError(f"Error en with_stmt: Estructura incorrecta después de WITH_KW. Se esperaba una expresión. Recibido: {context_expr_node}")
        context_expr_str = self._convertir_nodo(context_expr_node)

        block_node = args[-1]
        block_content_list = self._convertir_nodo(block_node)
        indented_block = self._indent_lines(block_content_list, 1)

        with_line = f"with {context_expr_str}"

        nodes_between = args[2:-1] # Nodes between expr and block

        if nodes_between:
             if len(nodes_between) == 2 and isinstance(nodes_between[0], Token) and nodes_between[0].type == 'COMO' and isinstance(nodes_between[1], Token) and nodes_between[1].type == 'IDENT':
                  alias_name = self._convertir_nodo(nodes_between[1])
                  with_line += f" as {alias_name}"
             else:
                  raise ValueError(f"Error en with_stmt: Estructura incorrecta para la cláusula 'como'. Se esperaba COMO IDENT después de la expresión de contexto. Recibido: {nodes_between}")

        with_line += ":"

        return f"{with_line}\n{indented_block}"


    # === DEFINITION RULES (FUNCTION, CLASS) ===

    def func_def(self, args): # FUNCTION_KW IDENT LPAR [parameter_list] RPAR [ARROW type] block
        if len(args) < 4 or not isinstance(args[0], Token) or args[0].type != 'FUNCTION_KW' or not isinstance(args[1], Token) or args[1].type != 'IDENT':
            raise ValueError(f"Error en func_def: Estructura inicial incorrecta. Esperado FUNCTION_KW IDENT ... Recibido: {args}")

        castella_func_name = self._convertir_nodo(args[1])

        # Find components by type/data, allowing for ignored WS.
        lpar_node = next((arg for arg in args if isinstance(arg, Token) and arg.type == 'LPAR'), None)
        rpar_node = next((arg for arg in args if isinstance(arg, Token) and arg.type == 'RPAR'), None)
        param_list_node = next((arg for arg in args if isinstance(arg, Tree) and arg.data == 'parameter_list'), None)
        arrow_node = next((arg for arg in args if isinstance(arg, Token) and arg.type == 'ARROW'), None)
        # Find type node only if it immediately follows ARROW and is a type Tree.
        return_type_node = None
        if arrow_node:
             arrow_index = args.index(arrow_node)
             if arrow_index + 1 < len(args) and isinstance(args[arrow_index + 1], Tree) and args[arrow_index + 1].data == 'type':
                  return_type_node = args[arrow_index + 1]

        block_node = next((arg for arg in args if isinstance(arg, Tree) and arg.data == 'block'), None)

        if lpar_node is None or rpar_node is None or block_node is None:
             raise ValueError(f"Error gramática: Estructura de definición de función incompleta ('{castella_func_name}'). Faltan paréntesis de parámetros o bloque de código. Args: {args}")

        # Basic order check by finding indices
        try:
            idx_func_kw = args.index(args[0]) # Must be first arg
            idx_ident = args.index(args[1])   # Must be second arg
            idx_lpar = args.index(lpar_node)
            idx_rpar = args.index(rpar_node)
            idx_block = args.index(block_node)
        except ValueError as e:
             raise ValueError(f"Error interno: Elementos esperados no encontrados en args para func_def ('{castella_func_name}'). Error: {e}. Args: {args}")


        if not (idx_func_kw == 0 and idx_ident == 1 and idx_lpar > idx_ident and idx_rpar > idx_lpar and idx_block > idx_rpar):
            # Check if parameter_list/arrow/type are between RPAR and block if present
            expected_nodes_between_rpar_and_block = []
            if param_list_node: # parameter_list should be between LPAR and RPAR
                 if not (idx_lpar < args.index(param_list_node) < idx_rpar):
                      raise ValueError(f"Error gramática: parameter_list fuera de lugar en func_def ('{castella_func_name}'). Args: {args}")

            # Check nodes between RPAR and block
            intermediate_nodes = args[idx_rpar + 1 : idx_block]
            if intermediate_nodes:
                 if len(intermediate_nodes) == 2 and isinstance(intermediate_nodes[0], Token) and intermediate_nodes[0].type == 'ARROW' and isinstance(intermediate_nodes[1], Tree) and intermediate_nodes[1].data == 'type':
                      if arrow_node != intermediate_nodes[0] or return_type_node != intermediate_nodes[1]:
                           raise ValueError(f"Error interno: Nodos ARROW/type no coinciden en func_def ('{castella_func_name}'). Args: {args}")
                 else:
                      raise ValueError(f"Error gramática: Estructura incorrecta entre RPAR y block en func_def ('{castella_func_name}'). Esperado ARROW type. Recibido: {intermediate_nodes}")


        translated_params_str = self._convertir_nodo(param_list_node) if param_list_node else ""

        translated_return_type_str = ""
        if return_type_node:
             translated_type = self._convertir_nodo(return_type_node)
             if translated_type:
                  translated_return_type_str = f" -> {translated_type}"

        block_content_list = self._convertir_nodo(block_node)

        python_func_name = castella_func_name
        if castella_func_name == "iniciar":
             python_func_name = "__init__"

             # Validate __init__ signature: must start with 'self' as first pos_param.
             # Check the original parameter_list node children if available.
             if param_list_node and param_list_node.children:
                 first_param_node = param_list_node.children[0] # The first `param` rule child.
                 if isinstance(first_param_node, Tree) and first_param_node.data == 'pos_param' and first_param_node.children:
                      first_param_name_token = first_param_node.children[0] # The IDENT token child of pos_param.
                      if isinstance(first_param_name_token, Token) and first_param_name_token.type == 'IDENT':
                          first_param_name_str = self._convertir_nodo(first_param_name_token)
                          if first_param_name_str != "self":
                               raise ValueError(f"Error de gramática: La función '{castella_func_name}' ('__init__') debe tener 'self' como primer parámetro posicional. Encontrado '{first_param_name_str}'.")
                      else:
                            raise ValueError(f"Error interno del transformer: Estructura inesperada del primer parámetro posicional en '{castella_func_name}'. Esperaba IDENT.")
                 else:
                      raise ValueError(f"Error de gramática: La función '{castella_func_name}' ('__init__') debe comenzar con un parámetro posicional 'self'. Recibido parámetros de tipo diferente (e.g., default, *args, **kwargs).")
             elif not translated_params_str.strip():
                  # If no parameters were declared, add 'self'.
                  translated_params_str = "self"
             # If param_list_node exists but has no children, it implies empty `()` which is handled by `elif not translated_params_str.strip()`.


        indented_block_str = self._indent_lines(block_content_list, 1)

        return f"def {python_func_name}({translated_params_str}){translated_return_type_str}:\n{indented_block_str}"


    def parameter_list(self, args): # param (COMMA param)*
        translated_params = []
        # Process param nodes in the order they were parsed.
        for param_node in args:
             if not isinstance(param_node, Tree) or param_node.data not in ['pos_param', 'default_param', 'star_param', 'double_star_param']:
                  raise ValueError(f"Error interno: Nodo inesperado en la lista de parámetros. Esperado un nodo 'param'. Recibido: {param_node}")
             translated_params.append(self._convertir_nodo(param_node))

        return ", ".join(translated_params)

    def pos_param(self, args): # IDENT [COLON type]
        if not isinstance(args[0], Token) or args[0].type != 'IDENT':
             raise ValueError(f"Error en pos_param: Estructura incorrecta. Esperado IDENT. Recibido: {args}")

        param_name = self._convertir_nodo(args[0])
        type_hint_str = ""
        if len(args) == 3:
             if not isinstance(args[1], Token) or args[1].type != 'COLON' or not isinstance(args[2], Tree) or args[2].data != 'type':
                  raise ValueError(f"Error en pos_param: Estructura incorrecta para tipo. Esperado COLON type. Recibido: {args[1:]}")
             translated_type = self._convertir_nodo(args[2])
             if translated_type:
                  type_hint_str = f": {translated_type}"
        elif len(args) != 1:
             raise ValueError(f"Error en pos_param: Número de argumentos inesperado ({len(args)}). Esperado 1 o 3. Args: {args}")

        return f"{param_name}{type_hint_str}"

    def default_param(self, args): # IDENT [COLON type] IGUAL expr
        if not isinstance(args[0], Token) or args[0].type != 'IDENT' or not isinstance(args[-2], Token) or args[-2].type != 'IGUAL' or not isinstance(args[-1], Tree) or args[-1].data != 'expr':
             raise ValueError(f"Error en default_param: Estructura básica incorrecta. Esperado IDENT ... IGUAL expr. Recibido: {args}")

        param_name = self._convertir_nodo(args[0])
        default_value_str = self._convertir_nodo(args[-1])

        type_hint_str = ""
        # Check for optional type hint between IDENT and IGUAL.
        # args structure: [IDENT, (COLON, type)?, IGUAL, expr]
        nodes_between_ident_and_igual = args[1:-2] # Exclude IDENT, IGUAL, expr
        if nodes_between_ident_and_igual:
             if len(nodes_between_ident_and_igual) == 2 and isinstance(nodes_between_ident_and_igual[0], Token) and nodes_between_ident_and_igual[0].type == 'COLON' and isinstance(nodes_between_ident_and_igual[1], Tree) and nodes_between_ident_and_igual[1].data == 'type':
                   translated_type = self._convertir_nodo(nodes_between_ident_and_igual[1])
                   if translated_type:
                        type_hint_str = f": {translated_type}"
             else:
                  raise ValueError(f"Error en default_param: Estructura incorrecta para tipo. Esperado COLON type entre IDENT e IGUAL. Recibido: {nodes_between_ident_and_igual}. Args: {args}")

        return f"{param_name}{type_hint_str} = {default_value_str}"

    def star_param(self, args): # STAR IDENT
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'STAR' or not isinstance(args[1], Token) or args[1].type != 'IDENT':
             raise ValueError(f"Error en star_param: Estructura incorrecta. Esperado [STAR, IDENT]. Recibido: {args}")

        ident_str = self._convertir_nodo(args[1])
        return f"*{ident_str}"

    def double_star_param(self, args): # DOUBLE_STAR IDENT
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'DOUBLE_STAR' or not isinstance(args[1], Token) or args[1].type != 'IDENT':
             raise ValueError(f"Error en double_star_param: Estructura incorrecta. Esperado [DOUBLE_STAR, IDENT]. Recibido: {args}")

        ident_str = self._convertir_nodo(args[1])
        return f"**{ident_str}"

    def class_def(self, args): # CLASS_KW IDENT [DESDE inheritance_list] LBRACE (class_body_element)* RBRACE
        if len(args) < 2 or not isinstance(args[0], Token) or args[0].type != 'CLASS_KW' or not isinstance(args[1], Token) or args[1].type != 'IDENT':
             raise ValueError(f"Error en class_def: Estructura inicial incorrecta. Esperado CLASS_KW IDENT. Recibido: {args}")

        class_name = self._convertir_nodo(args[1])

        base_classes_str = ""
        body_elements_nodes_start_idx = 2

        if len(args) > 2 and isinstance(args[2], Token) and args[2].type == 'DESDE':
             if len(args) < 4 or not isinstance(args[3], Tree) or args[3].data != 'inheritance_list':
                  raise ValueError(f"Error gramática: La cláusula DESDE debe ir seguida de una lista de herencia. Recibido a partir de DESDE: {args[2:]}")
             inheritance_list_node = args[3]
             translated_bases = self._convertir_nodo(inheritance_list_node)
             base_classes_str = f"({translated_bases})"
             body_elements_nodes_start_idx = 4 # Body starts after DESDE and inheritance_list

        # Check for LBRACE after inheritance or IDENT, and RBRACE at the end (considering ignored tokens)
        # The body elements are all nodes after the LBRACE and before the RBRACE.
        # Since LBRACE/RBRACE are ignored, the args contain items between them after initial elements.
        # The nodes from `body_elements_nodes_start_idx` to the end are the class body elements.
        body_elements_nodes = args[body_elements_nodes_start_idx:]


        translated_body_elements = []
        pending_decorators_class = [] # Decorators specifically for methods/classes within the class body.

        for body_node in body_elements_nodes:
             if isinstance(body_node, Token) and body_node.type in ['WS', 'LINE_COMMENT', 'LBRACE', 'RBRACE']: # Include LBRACE/RBRACE as ignored here too for safety
                  continue

             if isinstance(body_node, Tree) and body_node.data == 'decorator':
                   translated_decorator = self._convertir_nodo(body_node)
                   if translated_decorator:
                       pending_decorators_class.append(translated_decorator)
                   continue

             if isinstance(body_node, Tree) and body_node.data in ['func_def', 'class_def'] :
                 if pending_decorators_class:
                      for decorator_line in pending_decorators_class:
                           translated_body_elements.append(decorator_line)
                      pending_decorators_class = []

                 translated_element = self._convertir_nodo(body_node)
                 if translated_element is not None:
                     translated_body_elements.append(str(translated_element))

             elif isinstance(body_node, Tree) and body_node.data in ['class_attribute'] or (isinstance(body_node, Token) and body_node.type == 'MULTILINE_STRING'):
                 if pending_decorators_class:
                       node_type_desc = body_node.data if isinstance(body_node, Tree) else body_node.type
                       decorator_example = pending_decorators_class[0]
                       raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) sólo pueden preceder definiciones de función o clase anidada dentro del cuerpo de la clase. Encontrado un elemento '{node_type_desc}' sin una definición asociada.")

                 translated_element = self._convertir_nodo(body_node)
                 if translated_element is not None:
                       translated_body_elements.append(str(translated_element))

             # Handle basic statements inside the class body (pass, assignments, etc.)
             elif isinstance(body_node, Tree) and body_node.data in ['stmt']:
                  if pending_decorators_class:
                       decorator_example = pending_decorators_class[0]
                       stmt_type_node = body_node.children[0] if body_node.children else None
                       stmt_type_desc = getattr(stmt_type_node, 'data', 'UnknownStatementType')
                       raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) sólo pueden preceder definiciones de función o clase anidada dentro del bloque. Encontrada sentencia básica de tipo '{stmt_type_desc}'")

                  translated_element = self._convertir_nodo(body_node)
                  if translated_element is not None:
                       if isinstance(translated_element, list): translated_body_elements.extend(translated_element)
                       else: translated_body_elements.append(str(translated_element))


             else:
                  # Skip other unexpected nodes but continue.
                  # print(f"Debug: Unexpected node in class body: {body_node}")
                  pass


        if pending_decorators_class:
              decorator_example = pending_decorators_class[0]
              raise ValueError(f"Error de gramática: Decoradores ({decorator_example}) sin definición de función o clase que los siga al final del cuerpo de la clase.")

        indented_body_str = self._indent_lines(translated_body_elements, 1)

        return f"class {class_name}{base_classes_str}:\n{indented_body_str}"

    def inheritance_list(self, args): # access (COMMA access)*
         return ", ".join(self._convertir_nodo(arg) for arg in args)

    def class_body_element(self, args): # decorator | func_def | MULTILINE_STRING | class_attribute | stmt
         if len(args) != 1:
              raise ValueError(f"Error interno: Regla 'class_body_element' del transformer recibió un número de argumentos inesperado ({len(args)}). Args: {args}")
         return self._convertir_nodo(args[0])

    def class_attribute(self, args): # IDENT [COLON type] IGUAL expr
        if not isinstance(args[0], Token) or args[0].type != 'IDENT' or not isinstance(args[-2], Token) or args[-2].type != 'IGUAL' or not isinstance(args[-1], Tree) or args[-1].data != 'expr':
             raise ValueError(f"Error en class_attribute: Estructura incorrecta. Esperado IDENT [COLON type] IGUAL expr. Recibido: {args}")

        name = self._convertir_nodo(args[0])
        value_str = self._convertir_nodo(args[-1])

        type_hint_str = ""
        # Check for optional type hint between IDENT and IGUAL.
        # args structure: [IDENT, (COLON, type)?, IGUAL, expr]
        nodes_between_ident_and_igual = args[1:-2] # Exclude IDENT, IGUAL, expr
        if nodes_between_ident_and_igual:
             if len(nodes_between_ident_and_igual) == 2 and isinstance(nodes_between_ident_and_igual[0], Token) and nodes_between_ident_and_igual[0].type == 'COLON' and isinstance(nodes_between_ident_and_igual[1], Tree) and nodes_between_ident_and_igual[1].data == 'type':
                   translated_type = self._convertir_nodo(nodes_between_ident_and_igual[1])
                   if translated_type:
                        type_hint_str = f": {translated_type}"
             else:
                  raise ValueError(f"Error en class_attribute: Estructura incorrecta para tipo. Esperado COLON type entre IDENT e IGUAL. Recibido: {nodes_between_ident_and_igual}. Args: {args}")


        return f"{name}{type_hint_str} = {value_str}"


    def decorator(self, args): # ARROBA access
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'ARROBA' or not isinstance(args[1], Tree) or args[1].data != 'access':
             raise ValueError(f"Error en decorator: Estructura incorrecta. Esperado [ARROBA, access]. Recibido: {args}")
        access_str = self._convertir_nodo(args[1])
        return f"@{access_str}"


    # === IMPORT RULES ===

    def importar(self, args): # import_module | from_import
         if len(args) != 1: raise ValueError(f"Error en importar: {args}")
         return self._convertir_nodo(args[0])

    def import_module(self, args): # IMPORT_KW access SEMICOLON
        if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'IMPORT_KW' or not isinstance(args[1], Tree) or args[1].data != 'access' or not isinstance(args[2], Token) or args[2].type != 'SEMICOLON':
            raise ValueError(f"Error en import_module: Estructura incorrecta. Esperado [IMPORT_KW, access, SEMICOLON]. Recibido: {args}")
        module_access_str = self._convertir_nodo(args[1])
        return f"import {module_access_str}"

    def from_import(self, args): # DESDE access IMPORT_KW (imported_names_list | STAR) SEMICOLON
        if len(args) != 5 or not isinstance(args[0], Token) or args[0].type != 'DESDE' or not isinstance(args[1], Tree) or args[1].data != 'access' or not isinstance(args[2], Token) or args[2].type != 'IMPORT_KW' or not isinstance(args[-1], Token) or args[-1].type != 'SEMICOLON':
            raise ValueError(f"Error en from_import: Estructura inicial/final o token intermedio incorrecto (DESDE/IMPORT_KW/SEMICOLON). Recibido: {args}")

        module_access_node = args[1]
        imported_part_node = args[3]

        if not isinstance(imported_part_node, Tree) and not (isinstance(imported_part_node, Token) and imported_part_node.type == 'STAR'):
             raise ValueError(f"Error en from_import: Estructura incorrecta después de IMPORT_KW. Esperado imported_names_list o STAR. Recibido: {imported_part_node}.")

        module_access_str = self._convertir_nodo(module_access_node)
        imported_part_str = self._convertir_nodo(imported_part_node)

        return f"from {module_access_str} import {imported_part_str}"

    def imported_names_list(self, args): # imported_name (COMMA imported_name)*
         return ", ".join(self._convertir_nodo(arg) for arg in args)

    def imported_name(self, args): # IDENT [COMO IDENT]
         if not isinstance(args[0], Token) or args[0].type != 'IDENT': raise ValueError(f"Error en imported_name: Expected IDENT. Recibido: {args}")
         name = self._convertir_nodo(args[0])

         if len(args) == 3:
              if not isinstance(args[1], Token) or args[1].type != 'COMO' or not isinstance(args[2], Token) or args[2].type != 'IDENT':
                   raise ValueError(f"Error en imported_name 'como': Estructura incorrecta. Esperado COMO IDENT. Recibido: {args[1:]}. Arg list: {args}")
              alias = self._convertir_nodo(args[2])
              return f"{name} as {alias}"
         elif len(args) != 1:
              raise ValueError(f"Error interno: Unexpected arguments in imported_name: {args}. Expected 1 or 3.")
         return name

    def STAR(self, args): # STAR token
         # This method is called if the rule explicitly mentions the STAR token as a child.
         # args should be empty for a direct token match.
         # The from_import rule uses `imported_names_list | STAR`.
         # When STAR is matched, this method `STAR(self, [])` is called.
         if args: # Safety check, should be empty
              # print(f"Warning: STAR token method received unexpected arguments: {args}")
              pass # Still return "*"

         return "*" # Return the literal "*" string for `from ... import *`.


    # === TYPE HINTING RULES ===

    def type(self, args): # basic_type | collection_type | union_type | forward_ref
        if len(args) != 1: raise ValueError(f"Error en type: Expected 1 argument. Recibido: {args}")
        return self._convertir_nodo(args[0])

    def basic_type(self, args): # access
        if len(args) != 1 or not isinstance(args[0], Tree) or args[0].data != 'access':
             raise ValueError(f"Error en basic_type: Expected access node. Recibido: {args}")
        return self._convertir_nodo(args[0])

    def collection_type(self, args): # (TYPE_TERMINAL | ...) (LBRACKET type_arguments RBRACKET)?
        if not args or not isinstance(args[0], Token) or args[0].type not in ['LIST_TYPE', 'DICT_TYPE', 'TUPLE_TYPE', 'SET_TYPE', 'OPTIONAL_TYPE', 'RESULTADO_TYPE', 'MATRIZ_TYPE', 'TENSOR_TYPE', 'LLAMABLE_TYPE']:
             raise ValueError(f"Error en collection_type: Expected a valid type keyword token as first argument. Recibido: {args[0]}. Args: {args}")

        type_token = args[0]

        # Map Castella type keyword value to Python/typing string.
        translated_name = {
            "Lista": "List",       "Diccionario": "Dict", "Tupla": "Tuple", "Conjunto": "Set",
            "Opcional": "Optional", "Resultado": "Any",
            "Matriz": "np.ndarray", # Requires `import numpy as np`
            "Tensor": "tf.Tensor",  # Requires `import tensorflow as tf`
            "Llamable": "Callable"  # Requires 'from typing import Callable'
        }.get(type_token.value, type_token.value) # Fallback to original Castella word if not in map.


        type_arguments_str = ""
        if len(args) > 1:
             type_arguments_node = args[1]
             if not isinstance(type_arguments_node, Tree) or type_arguments_node.data != 'type_arguments':
                 raise ValueError(f"Error interno: expected 'type_arguments' node after type keyword token in collection_type. Recibido: {type_arguments_node}. Args: {args}")

             translated_args = self._convertir_nodo(type_arguments_node)
             type_arguments_str = f"[{translated_args}]"

        elif len(args) != 1:
              raise ValueError(f"Error en collection_type: Número de argumentos inesperado ({len(args)}). Esperado 1 o 2.")

        return f"{translated_name}{type_arguments_str}"

    def union_type(self, args): # UNION_TYPE LBRACKET type_arguments RBRACKET
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'UNION_TYPE' or not isinstance(args[1], Tree) or args[1].data != 'type_arguments':
             raise ValueError(f"Error en union_type: Estructura incorrecta. Esperado [UNION_TYPE, type_arguments]. Recibido: {args}")

        type_arguments_node = args[1]
        translated_args = self._convertir_nodo(type_arguments_node)

        return f"Union[{translated_args}]" # Python requires "Union" name.

    def forward_ref(self, args): # QUOTE IDENT QUOTE
        if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'QUOTE' or not isinstance(args[1], Token) or args[1].type != 'IDENT' or not isinstance(args[2], Token) or args[2].type != 'QUOTE':
             raise ValueError(f"Error en forward_ref: Estructura incorrecta. Esperado [QUOTE, IDENT, QUOTE]. Recibido: {args}")

        ident_token = args[1]
        ident_str = self._convertir_nodo(ident_token)

        return f"'{ident_str}'"

    def type_arguments(self, args): # type (COMMA type)*
         return ", ".join(self._convertir_nodo(arg) for arg in args)


    # === EXPRESSION RULES ===

    def expr(self, args): # lambda_expr | ternary. Delegate to the single child.
        if len(args) != 1: raise ValueError(f"Error en expr: Expected 1 argument. Recibido: {args}")
        return self._convertir_nodo(args[0])

    def ternary(self, args): # bool_or [QUESTION bool_or COLON bool_or]
        if len(args) == 1 and isinstance(args[0], Tree) and args[0].data == 'bool_or':
             return self._convertir_nodo(args[0])
        elif len(args) == 5 and isinstance(args[0], Tree) and args[0].data == 'bool_or' and \
             isinstance(args[1], Token) and args[1].type == 'QUESTION' and \
             isinstance(args[2], Tree) and args[2].data == 'bool_or' and \
             isinstance(args[3], Token) and args[3].type == 'COLON' and \
             isinstance(args[4], Tree) and args[4].data == 'bool_or':

             cond_str = self._convertir_nodo(args[0])
             true_val_str = self._convertir_nodo(args[2])
             false_val_str = self._convertir_nodo(args[4])

             return f"{true_val_str} if {cond_str} else {false_val_str}"

        else:
             raise ValueError(f"Error interno: Estructura ternary inesperada. Recibido: {args}")

    # Boolean operators: bool_or, bool_and, not_expr
    def bool_or(self, args): # bool_and (OR_OP bool_and)*
         return self._handle_binary_op(args)

    def bool_and(self, args): # not_expr (AND_OP not_expr)*
        return self._handle_binary_op(args)

    def not_expr(self, args): # [NOT_OP] comparison
        if len(args) == 1 and isinstance(args[0], Tree) and args[0].data == 'comparison':
             return self._convertir_nodo(args[0])
        elif len(args) == 2 and isinstance(args[0], Token) and args[0].type == 'NOT_OP' and isinstance(args[1], Tree) and args[1].data == 'comparison':
             not_keyword_str = self._convertir_nodo(args[0])
             comparison_str = self._convertir_nodo(args[1])
             return f"{not_keyword_str} {comparison_str}"
        else:
             raise ValueError(f"Error interno: Estructura not_expr inesperada. Recibido: {args}. Esperado [comparison] o [NOT_OP, comparison]")

    # Comparison operators: comparison
    def comparison(self, args): # bitwise_or_expr ((COMP_OP | MEMBERSHIP_OP | IDENTITY_OP) bitwise_or_expr)*
         return self._handle_binary_op(args)

    # Bitwise, Shift, Arithmetic operators: Use _handle_binary_op for chains.
    def bitwise_or_expr(self, args): # bitwise_xor_expr (PIPE_OP bitwise_xor_expr)*
        return self._handle_binary_op(args)

    def bitwise_xor_expr(self, args): # bitwise_and_expr (CARET_OP bitwise_and_expr)*
        return self._handle_binary_op(args)

    def bitwise_and_expr(self, args): # shift_expr (AMPERSAND_OP shift_expr)*
        return self._handle_binary_op(args)

    def shift_expr(self, args): # additive_expr ((LSHIFT_OP | RSHIFT_OP) additive_expr)*
        return self._handle_binary_op(args)

    def additive_expr(self, args): # multiplicative_expr (ADD_OP_BIN multiplicative_expr)*
        return self._handle_binary_op(args)

    def multiplicative_expr(self, args): # unary_expr (MULT_OP_BIN unary_expr)*
        # This rule now includes AT_OP in MULT_OP_BIN. _handle_binary_op handles it correctly.
        return self._handle_binary_op(args)

    # Unary operators: unary_expr
    def unary_expr(self, args): # [UNARY_OP] power
        if len(args) == 1 and isinstance(args[0], Tree) and args[0].data == 'power':
             return self._convertir_nodo(args[0])
        elif len(args) == 2 and isinstance(args[0], Token) and args[0].type == 'UNARY_OP' and isinstance(args[1], Tree) and args[1].data == 'power':
             op_str = self._convertir_nodo(args[0])
             operand_str = self._convertir_nodo(args[1])
             space = " " if op_str == "not" else "" # Add space only for 'not'
             return f"{op_str}{space}{operand_str}"
        else:
             raise ValueError(f"Error interno: Estructura unary_expr inesperada. Recibido: {args}. Esperado [power] o [UNARY_OP, power]")

    # Power operator: power (right-associative handled by grammar/parser)
    def power(self, args): # access (DOUBLE_STAR unary_expr)* (Using DOUBLE_STAR terminal directly)
        # Based on the common grammar pattern for power with right-associativity (access (OP power)*)
        # but the provided grammar is (access (OP unary)*).
        # If the grammar is `power: access (DOUBLE_STAR power)*`, args for `a**b**c` would be `[access_a, token_**, tree_power_b_c]`.
        # If the grammar is `power: access (DOUBLE_STAR unary_expr)*`, args for `a**b**c` would be `[power_a_b, token_**, unary_c]` (left-associative).
        # We are using the provided grammar: `power: access (WS? DOUBLE_STAR WS? unary_expr)*`. This implies left-associativity by default in LALR.
        # _handle_binary_op processes this pattern correctly as left-associative.
        return self._handle_binary_op(args)

    # === ACCESS RULES (Attribute, Index, Call) ===
    def access(self, args): # primary (DOT_ACCESS | INDEX_ACCESS | CALL_SUFFIX)*
         if not args or not isinstance(args[0], Tree) or args[0].data != 'primary':
              raise ValueError(f"Error en access: Expected primary node as first arg. Recibido: {args}")

         result = self._convertir_nodo(args[0]) # Translate the primary expression.

         for suffix_node in args[1:]:
              if not isinstance(suffix_node, Tree) or suffix_node.data not in ['DOT_ACCESS', 'INDEX_ACCESS', 'CALL_SUFFIX']:
                   raise ValueError(f"Error interno: Nodo de sufijo de acceso inesperado. Esperado DOT_ACCESS, INDEX_ACCESS o CALL_SUFFIX. Recibido: {suffix_node}. Args: {args}")

              suffix_str = self._convertir_nodo(suffix_node) # Translate the suffix node.
              result = f"{result}{suffix_str}" # Append the suffix string.

         return result

    def DOT_ACCESS(self, args): # DOT IDENT
         if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'DOT' or not isinstance(args[1], Token) or args[1].type != 'IDENT':
              raise ValueError(f"Error en DOT_ACCESS: Estructura incorrecta. Esperado [DOT, IDENT]. Recibido: {args}")
         return f".{self._convertir_nodo(args[1])}"

    def INDEX_ACCESS(self, args): # LBRACKET slice_expr RBRACKET
        if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'LBRACKET' or not isinstance(args[1], Tree) or args[1].data != 'slice_expr' or not isinstance(args[2], Token) or args[2].type != 'RBRACKET':
            raise ValueError(f"Error en INDEX_ACCESS: Estructura incorrecta. Esperado [LBRACKET, slice_expr, RBRACKET]. Recibido: {args}")
        slice_expr_str = self._convertir_nodo(args[1])
        return f"[{slice_expr_str}]"

    def CALL_SUFFIX(self, args): # LPAR [argument_list] RPAR
        if not isinstance(args[0], Token) or args[0].type != 'LPAR' or not isinstance(args[-1], Token) or args[-1].type != 'RPAR':
             raise ValueError(f"Error en CALL_SUFFIX: Estructura inicial/final incorrecta (LPAR/RPAR). Recibido: {args}")

        arguments_str = ""
        if len(args) == 3:
             arg_list_node = args[1]
             if not isinstance(arg_list_node, Tree) or arg_list_node.data != 'argument_list':
                 raise ValueError(f"Error interno: expected 'argument_list' node between LPAR and RPAR in CALL_SUFFIX. Recibido: {arg_list_node}. Args: {args}")
             arguments_str = self._convertir_nodo(arg_list_node)

        elif len(args) != 2:
             raise ValueError(f"Error en CALL_SUFFIX: Número de argumentos inesperado ({len(args)}). Esperado 2 o 3.")

        return f"({arguments_str})"

    def argument_list(self, args): # (positional_args_list [COMMA star_arg] [COMMA keyword_args_list] [COMMA double_star_arg]) | ...
        translated_pos_args = []
        translated_star_args = []
        translated_keyword_args = []
        translated_double_star_args = []

        seen_star = False
        seen_keyword = False
        seen_double_star = False

        for arg_group_node in args:
            if isinstance(arg_group_node, Token) and arg_group_node.type in ['WS', 'COMA']:
                 continue

            if not isinstance(arg_group_node, Tree):
                raise TypeError(f"Error interno del transformer: Nodo inesperado en argument_list. Esperado un Tree de grupo de argumentos. Recibido: {arg_group_node}.")

            arg_type = arg_group_node.data

            if arg_type == 'positional_args_list':
                 if seen_star or seen_keyword or seen_double_star:
                      raise ValueError(f"Error de gramática: Argumento posicional aparece después de *args, argumentos por nombre, o **kwargs en la llamada.")
                 translated_pos_args.append(self._convertir_nodo(arg_group_node))

            elif arg_type == 'star_arg':
                 if seen_star: raise ValueError(f"Error de gramática: Múltiples *args en la llamada.")
                 if seen_double_star: raise ValueError(f"Error de gramática: *args aparece después de **kwargs.")
                 if seen_keyword: raise ValueError(f"Error de gramática: *args aparece después de un argumento por nombre en la llamada.")
                 seen_star = True
                 translated_star_args.append(self._convertir_nodo(arg_group_node))

            elif arg_type == 'keyword_args_list':
                 if seen_double_star:
                      raise ValueError(f"Error de gramática: Argumento por nombre aparece después de **kwargs en la llamada.")
                 seen_keyword = True
                 translated_keyword_args.append(self._convertir_nodo(arg_group_node))

            elif arg_type == 'double_star_arg':
                 if seen_double_star:
                      raise ValueError(f"Error de gramática: Múltiples **kwargs en la llamada.")
                 seen_double_star = True
                 translated_double_star_args.append(self._convertir_nodo(arg_group_node))

            else:
                 raise TypeError(f"Error interno del transformer: Tipo de grupo de argumentos desconocido en argument_list: {arg_type}. Nodo: {arg_group_node}")

        final_translated_parts = []

        if translated_pos_args:
            if len(translated_pos_args) > 1: raise ValueError(f"Error interno: Múltiples bloques de argumentos posicionales encontrados.")
            final_translated_parts.append(translated_pos_args[0])

        if translated_star_args:
             if len(translated_star_args) > 1: raise ValueError(f"Error interno: Múltiples argumentos *args encontrados.")
             final_translated_parts.append(translated_star_args[0])

        if translated_keyword_args:
             if len(translated_keyword_args) > 1: raise ValueError(f"Error interno: Múltiples bloques de argumentos por nombre encontrados.")
             final_translated_parts.append(translated_keyword_args[0])

        if translated_double_star_args:
             if len(translated_double_star_args) > 1: raise ValueError(f"Error interno: Múltiples argumentos **kwargs encontrados.")
             final_translated_parts.append(translated_double_star_args[0])

        return ", ".join(final_translated_parts)

    def positional_args_list(self, args): # expr (COMMA expr)*
        return ", ".join(self._convertir_nodo(arg) for arg in args)

    def keyword_args_list(self, args): # keyword_argument (COMMA keyword_argument)*
         return ", ".join(self._convertir_nodo(arg) for arg in args)

    def keyword_argument(self, args): # IDENT IGUAL expr
         if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'IDENT' or not isinstance(args[1], Token) or args[1].type != 'IGUAL' or not isinstance(args[2], Tree) or args[2].data != 'expr':
              raise ValueError(f"Error en keyword_argument: Estructura incorrecta. Esperado [IDENT, IGUAL, expr]. Recibido: {args}")
         name = self._convertir_nodo(args[0])
         value = self._convertir_nodo(args[2])
         return f"{name}={value}"

    def star_arg(self, args): # STAR expr
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'STAR' or not isinstance(args[1], Tree) or args[1].data != 'expr':
             raise ValueError(f"Error en star_arg: Estructura incorrecta. Esperado [STAR, expr]. Recibido: {args}")
        star_symbol_str = self._convertir_nodo(args[0]) # Should be "*"
        expr_str = self._convertir_nodo(args[1])
        return f"{star_symbol_str}{expr_str}"

    def double_star_arg(self, args): # DOUBLE_STAR expr
        if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'DOUBLE_STAR' or not isinstance(args[1], Tree) or args[1].data != 'expr':
             raise ValueError(f"Error en double_star_arg: Estructura incorrecta. Esperado [DOUBLE_STAR, expr]. Recibido: {args}")
        double_star_symbol_str = self._convertir_nodo(args[0]) # Should be "**"
        expr_str = self._convertir_nodo(args[1])
        return f"{double_star_symbol_str}{expr_str}"

    def slice_expr(self, args): # [expr] [COLON] [expr] [COLON] [expr]
        content_nodes = [arg for arg in args if not (isinstance(arg, Token) and arg.type == 'WS')]
        translated_parts_and_colons = []
        for node in content_nodes:
             translated_parts_and_colons.append(self._convertir_nodo(node))
        return "".join(translated_parts_and_colons)


    # === PRIMARY EXPRESSIONS ===
    # Includes new complex and imaginary literals.

    def primary(self, args):
        # primary: numero | cadena | MULTILINE_STRING | list_literal | BOOLEAN | dict_literal | tuple_literal | set_literal | new_instance | NONE_KW | IDENT | LPAR expr RPAR
        #       | list_comprehension | dict_comprehension | set_comprehension | generator_expression
        #       | complex_literal | imaginary_literal // Added complex and imaginary literals

        # Handle parenthesized expressions (LPAR expr RPAR)
        if len(args) == 3 and isinstance(args[0], Token) and args[0].type == 'LPAR' and isinstance(args[2], Token) and args[2].type == 'RPAR' and isinstance(args[1], Tree) and args[1].data == 'expr':
             inner_expr_str = self._convertir_nodo(args[1])
             return f"({inner_expr_str})"

        # Handle all other alternatives for primary (should be a single child node)
        if len(args) != 1:
             raise ValueError(f"Error en primary: Número de argumentos inesperado ({len(args)}). Esperado 1 o 3 (para paréntesis). Recibido: {args}")

        # Delegate the translation to the method for the single child node's rule/token type.
        # This will handle `numero`, `cadena`, `MULTILINE_STRING`, `BOOLEAN`, `NONE_KW`, `IDENT` (via _convertir_nodo's Token handling),
        # and the new `complex_literal`, `imaginary_literal` tokens as well, since _convertir_nodo returns their value.
        # It will also delegate for Tree nodes like `list_literal`, `dict_literal`, `new_instance`, `list_comprehension`, etc.
        return self._convertir_nodo(args[0])

    # Note: Methods for numero, cadena, MULTILINE_STRING, BOOLEAN, NONE_KW, IDENT
    # are implicitly handled by _convertir_nodo based on Token type.
    # Methods for complex_literal, imaginary_literal are also handled by _convertir_nodo
    # as they are terminals whose value is the desired Python string.

    def dict_literal(self, args): # LBRACE [key_value_list] RBRACE
         if not args: return "{}" # Empty dict {}

         if len(args) == 1 and isinstance(args[0], Tree) and args[0].data == 'key_value_list':
             items_list_node = args[0]
             items_str = self._convertir_nodo(items_list_node)
             return f"{{{items_str}}}"

         else:
             raise ValueError(f"Error en dict_literal: Estructura inesperada. Esperado [key_value_list?] o []. Recibido: {args}. Longitud: {len(args)}")

    def key_value_list(self, args): # key_value (COMMA key_value)*
        return ", ".join(self._convertir_nodo(arg) for arg in args)

    def key_value(self, args): # expr COLON expr
         if len(args) != 3 or not isinstance(args[0], Tree) or args[0].data != 'expr' or not isinstance(args[1], Token) or args[1].type != 'COLON' or not isinstance(args[2], Tree) or args[2].data != 'expr':
             raise ValueError(f"Error en key_value: Estructura incorrecta. Esperado [expr, COLON, expr]. Recibido: {args}")

         key_str = self._convertir_nodo(args[0])
         value_str = self._convertir_nodo(args[2])

         return f"{key_str}: {value_str}"

    def tuple_literal(self, args): # LPAR [ (expr (COMMA expr)*)? [COMMA] ] RPAR
        content_nodes = [arg for arg in args if not (isinstance(arg, Token) and arg.type == 'WS')]
        expr_nodes = [arg for arg in content_nodes if isinstance(arg, Tree) and arg.data == 'expr']
        has_trailing_comma_token = content_nodes and isinstance(content_nodes[-1], Token) and content_nodes[-1].type == 'COMA'

        if not expr_nodes and not has_trailing_comma_token:
             return "()"

        translated_elements = [self._convertir_nodo(node) for node in expr_nodes]
        elements_str = ", ".join(translated_elements)

        if len(translated_elements) == 1:
             if has_trailing_comma_token:
                 return f"({elements_str},)" # (expr,) tuple
             else:
                 return f"({elements_str})" # (expr) parenthesized expression

        elif len(translated_elements) > 1:
              return f"({elements_str}{',' if has_trailing_comma_token else ''})"

        raise ValueError(f"Error interno: Estructura de tuple_literal inesperada o inválida. Recibido {len(translated_elements)} expresiones y {has_trailing_comma_token} coma final. Args: {args}")


    def list_literal(self, args): # LBRACKET [ (expr (COMMA expr)*)? ] RBRACKET
        content_nodes = [arg for arg in args if not (isinstance(arg, Token) and arg.type == 'WS')]
        expr_nodes = [arg for arg in content_nodes if isinstance(arg, Tree) and arg.data == 'expr']

        translated_elements = [self._convertir_nodo(node) for node in expr_nodes]
        elements_str = ", ".join(translated_elements)

        return f"[{elements_str}]" # Handles [] for empty list

    def set_literal(self, args): # LBRACE expr (COMMA expr)* RBRACE
        # Args are the expr nodes directly. Requires at least one expr.
        if not args or not all(isinstance(arg, Tree) and arg.data == 'expr' for arg in args):
             raise ValueError(f"Error en set_literal: Estructura incorrecta. Esperado 1 o más nodos 'expr'. Recibido: {args}")

        expr_nodes = args # args IS the list of expr nodes
        translated_elements = [self._convertir_nodo(node) for node in expr_nodes]
        elements_str = ", ".join(translated_elements)

        return f"{{{elements_str}}}" # Handles {1}, {1, 2}.

    # === COMPREHENSIONS AND GENERATOR EXPRESSIONS ===
    def list_comprehension(self, args): # LBRACKET expr comprehension_for RBRACKET
         if len(args) != 2 or not isinstance(args[0], Tree) or args[0].data != 'expr' or not isinstance(args[1], Tree) or args[1].data != 'comprehension_for': raise ValueError(f"Error en list_comprehension: {args}. Esperado [expr, comprehension_for]")
         item_expr_str = self._convertir_nodo(args[0])
         comp_for_str = self._convertir_nodo(args[1])
         return f"[{item_expr_str} {comp_for_str}]"

    def dict_comprehension(self, args): # LBRACE key_value comprehension_for RBRACE
        if len(args) != 2 or not isinstance(args[0], Tree) or args[0].data != 'key_value' or not isinstance(args[1], Tree) or args[1].data != 'comprehension_for': raise ValueError(f"Error en dict_comprehension: {args}. Esperado [key_value, comprehension_for]")
        kv_str = self._convertir_nodo(args[0])
        comp_for_str = self._convertir_nodo(args[1])
        return f"{{{kv_str} {comp_for_str}}}"

    def set_comprehension(self, args): # LBRACE expr comprehension_for RBRACE
        if len(args) != 2 or not isinstance(args[0], Tree) or args[0].data != 'expr' or not isinstance(args[1], Tree) or args[1].data != 'comprehension_for': raise ValueError(f"Error en set_comprehension: {args}. Esperado [expr, comprehension_for]")
        item_expr_str = self._convertir_nodo(args[0])
        comp_for_str = self._convertir_nodo(args[1])
        return f"{{{item_expr_str} {comp_for_str}}}"

    def generator_expression(self, args): # LPAR expr comprehension_for RPAR
        if len(args) != 2 or not isinstance(args[0], Tree) or args[0].data != 'expr' or not isinstance(args[1], Tree) or args[1].data != 'comprehension_for': raise ValueError(f"Error en generator_expression: {args}. Esperado [expr, comprehension_for]")
        item_expr_str = self._convertir_nodo(args[0])
        comp_for_str = self._convertir_nodo(args[1])
        return f"({item_expr_str} {comp_for_str})"

    def comprehension_for(self, args): # PARA_KW IDENT EN_KW expr [comprehension_if]?
         if (len(args) < 4 or len(args) > 5 or
             not isinstance(args[0], Token) or args[0].type != 'PARA_KW' or
             not isinstance(args[1], Token) or args[1].type != 'IDENT' or
             not isinstance(args[2], Token) or args[2].type != 'EN_KW' or
             not isinstance(args[3], Tree) or args[3].data != 'expr'):
             raise ValueError(f"Error en comprehension_for: Estructura inicial incorrecta. Recibido: {args}. Esperado [PARA_KW, IDENT, EN_KW, expr, [comp_if?]]")

         ident_str = self._convertir_nodo(args[1])
         iterable_expr_str = self._convertir_nodo(args[3])
         if_clause_str = ""
         if len(args) == 5:
              if_node = args[4]
              if not isinstance(if_node, Tree) or if_node.data != 'comprehension_if': raise ValueError(f"Error interno: Expected comprehension_if node: {if_node}")
              if_clause_str = self._convertir_nodo(if_node)
              if if_clause_str: if_clause_str = f" {if_clause_str}"
         return f"for {ident_str} in {iterable_expr_str}{if_clause_str}"

    def comprehension_if(self, args): # SI_KW expr
         if len(args) != 2 or not isinstance(args[0], Token) or args[0].type != 'SI_KW' or not isinstance(args[1], Tree) or args[1].data != 'expr':
             raise ValueError(f"Error en comprehension_if: Estructura incorrecta. Esperado [SI_KW, expr]. Recibido: {args}")
         condition_str = self._convertir_nodo(args[1])
         return f"if {condition_str}"

    def lambda_expr(self, args): # LAMBDA_KW [parameter_list] COLON expr
        if not isinstance(args[0], Token) or args[0].type != 'LAMBDA_KW' or not isinstance(args[-2], Token) or args[-2].type != 'COLON' or not isinstance(args[-1], Tree) or args[-1].data != 'expr':
             raise ValueError(f"Error en lambda_expr: Estructura básica incorrecta. Esperado [LAMBDA_KW, ..., COLON, expr]. Recibido: {args}")

        expr_node = args[-1]

        param_list_node = None
        if len(args) == 4:
             potential_param_list = args[1]
             if not isinstance(potential_param_list, Tree) or potential_param_list.data != 'parameter_list':
                  raise ValueError(f"Error en lambda_expr: Con 4 argumentos, esperado parameter_list en posición [1]. Recibido: {potential_param_list}. Args: {args}")
             param_list_node = potential_param_list

        elif len(args) != 3:
             raise ValueError(f"Error en lambda_expr: Número de argumentos inesperado ({len(args)}). Esperado 3 o 4. Args: {args}")

        lambda_keyword_str = self._convertir_nodo(args[0])
        params_str = self._convertir_nodo(param_list_node) if param_list_node is not None else ""
        expr_str = self._convertir_nodo(expr_node)

        return f"{lambda_keyword_str} {params_str}: {expr_str}"

    def new_instance(self, args): # NEW_KW access CALL_SUFFIX
        if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'NEW_KW' or not isinstance(args[1], Tree) or args[1].data != 'access' or not isinstance(args[2], Tree) or args[2].data != 'CALL_SUFFIX':
             raise ValueError(f"Error en new_instance: Estructura incorrecta. Esperado [NEW_KW, access, CALL_SUFFIX]. Recibido: {args}")

        # NEW_KW is dropped in Python output.
        class_access_str = self._convertir_nodo(args[1])
        arguments_str = self._convertir_nodo(args[2])

        return f"{class_access_str}{arguments_str}"

    # === Other rule methods ===
    # graficar rule translation. Assumes matplotlib.pyplot is imported as plt in the preamble.
    def graficar(self, args): # GRAFICAR expr SEMICOLON
        if len(args) != 3 or not isinstance(args[0], Token) or args[0].type != 'GRAFICAR' or not isinstance(args[1], Tree) or args[1].data != 'expr' or not isinstance(args[2], Token) or args[2].type != 'SEMICOLON':
             raise ValueError(f"Error en graficar: Estructura incorrecta. Esperado [GRAFICAR, expr, SEMICOLON]. Recibido: {args}")

        plot_data_expr_str = self._convertir_nodo(args[1])

        # Returns a list of lines for the plotting calls.
        return [
            f"plt.plot({plot_data_expr_str})",
            "plt.show()"
        ]


    # The methods for terminals like AT_OP, AT_EQUAL, imaginary_literal, complex_literal,
    # COMP_OP, MEMBERSHIP_OP, IDENTITY_OP, ADD_OP_BIN, MULT_OP_BIN, UNARY_OP, AUG_ASSIGN_OP, DOT
    # are not explicitly needed as long as _convertir_nodo handles them by returning their `.value`,
    # which is sufficient for these tokens as their value is the correct Python representation.