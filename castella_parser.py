# castella_parser.py

"""
Configura el parser de Lark con la gramática y el transformer,
y proporciona la función principal para traducir código Castella a Python.
Maneja los errores de parsing y transformación de manera detallada.
"""

# Importar las clases necesarias de Lark
from lark import Lark, UnexpectedInput, Transformer, Tree, Token # Import Tree and Token for type checking in error handling

# Importar la definición de la gramática y la clase Transformer de nuestros módulos locales
# Usamos importaciones relativas (.module) porque estos archivos están en el mismo paquete/directorio.
try:
    from .castella_grammar import GRAMATICA
    from .castella_transformer import CastellaTransformer
except ImportError as e:
    # Si falla la importación, significa que los archivos no están bien estructurados como paquete
    # o faltan los otros módulos.
    print("\nError de Importación:")
    print("No se pudieron importar los módulos de gramática o transformer.")
    print("Asegúrate de que 'castella_grammar.py' y 'castella_transformer.py' existan en el mismo directorio")
    print("que 'castella_parser.py' y que los estás ejecutando desde el directorio contenedor o como un paquete.")
    print(f"Detalle: {e}")
    sys.exit(1)


import sys
import traceback # Importar para imprimir el traceback de errores

# === CONFIGURACIÓN DEL PARSER ===
# El parser de Lark se crea aquí cuando este módulo es importado.
# Esto valida la sintaxis de la GRAMATICA y construye el motor de parsing.
try:
    print("\nIntentando crear el parser de Lark a partir de la gramática definida...")
    # Instanciamos el transformer y lo pasamos al parser.
    # parser="lalr" indica que usamos el algoritmo LALR (Look-Ahead LR),
    # que es eficiente y adecuado para gramáticas tipo programación.
    # start="start" especifica la regla de inicio en la gramática.
    # transformer=CastellaTransformer() crea una instancia del transformer.
    parser = Lark(GRAMATICA, start="start", parser="lalr", transformer=CastellaTransformer())
    print("Parser de Lark creado exitosamente. La sintaxis de la gramática es válida para Lark.")

# --- Manejo de Errores Durante la Creación del Parser ---
except Exception as e:
    # Si ocurre una excepción aquí, significa que la definición de la gramática (la cadena GRAMATICA)
    # contiene errores sintácticos que Lark no puede procesar.
    print("\nError CRÍTICO al inicializar el parser:")
    print("Esto usualmente significa un error en la sintaxis de la definición de la gramática (la cadena GRAMATICA).")
    print(f"Tipo de error de Lark: {type(e).__name__}") # Imprimir el tipo específico de excepción de Lark.
    print(f"Detalle del error: {e}") # Imprimir el mensaje de error detallado.

    # Imprimir el traceback para ayudar a la depuración (muestra la pila de llamadas).
    traceback.print_exc()

    # Salir del programa con un código de error, ya que no se puede continuar sin un parser válido.
    sys.exit(1)


# === FUNCIÓN DE TRADUCCIÓN ===

def traducir_a_python(codigo_castella: str) -> str:
    """
    Traduce una cadena de código Castella a una cadena de código Python.

    Utiliza el parser de Lark configurado globalmente para analizar el código
    y el transformer asociado para convertir el árbol de sintaxis a código Python.

    Args:
        codigo_castella: La cadena que contiene el código fuente en Castella.

    Returns:
        Una cadena que contiene el código Python traducido.
        Retorna un string de comentario si la entrada está vacía.

    Raises:
        UnexpectedInput: Si hay un error de sintaxis en el código Castella de entrada.
                         Se imprime información detallada antes de relanzar.
        NotImplementedError: Si el transformer no tiene un método para una regla gramatical.
                           Se imprime el mensaje antes de relanzar.
        ValueError: Si el transformer detecta un error estructural o semántico durante la traducción.
                    Se imprime el mensaje antes de relanzar.
        TypeError: Si el transformer encuentra un tipo de nodo inesperado o un problema interno
                   relacionado con tipos de datos.
                   Se imprime el mensaje antes de relanzar.
        Exception: Para cualquier otro error inesperado durante el proceso de parseo/transformación.
                   Se imprime el error y el traceback antes de relanzar.
    """
    # Manejar el caso de entrada vacía o solo con espacios en blanco.
    if not codigo_castella or not codigo_castella.strip():
        # Si no hay código para traducir, retornamos una cadena de comentario simple.
        print("El código de entrada está vacío o solo contiene espacios en blanco. Generando archivo Python vacío con comentario.")
        return "# Código Castella vacío o solo con espacios en blanco." # Retornar un string de comentario válido en Python.

    print("\n--- Analizando y traduciendo código Castella a Python ---")

    try:
        # Llamar al método parse del parser de Lark.
        # Esto dispara todo el proceso de parsing y transformación.
        codigo_python_result = parser.parse(codigo_castella)

        print("--- Código Python generado ---")

        # El método `start` del transformer DEBE retornar una cadena (el código Python completo).
        # Validar el tipo de retorno.
        if not isinstance(codigo_python_result, str):
             # Si el transformer retornó algo inesperado (no None, porque None ya se maneja en el transformer si no hay contenido),
             # es un error lógico en el transformer. Intentamos convertir a string y reportamos.
             print(f"Error interno del Transformer: El método 'start' retornó un tipo inesperado.")
             print(f"Tipo de retorno: {type(codigo_python_result)}. Se esperaba 'str'.")
             # En este caso, en lugar de intentar convertir y potencialmente generar código incorrecto,
             # es más seguro lanzar un TypeError, ya que indica un problema fundamental en el transformer.
             raise TypeError(f"Transformer start method returned unexpected type: {type(codigo_python_result)}")

        # Si el resultado es una cadena, la usamos directamente.
        codigo_python_output = codigo_python_result

        # Formateo final del código Python: eliminar líneas vacías al final
        # y asegurarse de que haya exactamente una línea vacía al final (convención Python).
        python_lines = codigo_python_output.splitlines()
        while python_lines and not python_lines[-1].strip():
            python_lines.pop() # Eliminar líneas vacías finales existentes.
        python_lines.append('') # Añadir una sola línea vacía al final.
        codigo_python_final = "\n".join(python_lines)


        # Imprimir el código Python generado (para depuración y verificación).
        print(codigo_python_final)
        print("------------------------------")

        # Retornar la cadena final del código Python traducido.
        return codigo_python_final

    # --- Manejo de Errores Durante el Proceso de Parseo y Transformación ---

    except UnexpectedInput as e:
        # Lark lanza UnexpectedInput para errores de sintaxis en el código fuente de Castella.
        print(f"\nError de Sintaxis en el código Castella:")
        print(f"  Línea {e.line}, columna {e.column}")
        # Asegurarnos de que e.token sea accesible y útil
        token_info = f"'{e.token}' (tipo: {e.token.type})" if isinstance(e.token, Token) else f"Token inesperado: {e.token!r}"
        print(f"  {token_info}")
        # Mostrar qué tokens esperaba Lark en ese punto.
        # Ordenar `e.expected` para una salida consistente.
        print(f"  Se esperaba uno de: {', '.join(sorted(str(exp) for exp in e.expected))}")
        # Mostrar el contexto del código fuente alrededor del error.
        try:
            context = e.get_context(codigo_castella, span=50) # Mostrar 50 caracteres alrededor del error.
            print(f"  Contexto del error:\n---\n{context}\n---")
        except Exception as ctx_e:
             # Si obtener el contexto falla, lo reportamos pero no impedimos mostrar el resto del error.
             print(f"  Advertencia: No se pudo obtener el contexto del error. Detalle: {ctx_e}")


        # Imprimir el traceback para información adicional de depuración.
        traceback.print_exc()

        # Relanzar la excepción para que el código que llamó sepa que falló la traducción.
        raise

    except NotImplementedError as e:
        # Error lanzado por el transformer (`_convertir_nodo`) si falta un método.
        print(f"\nError del Transformer: Implementación faltante para una característica del lenguaje.")
        print(e) # El mensaje de error ya indica la regla faltante.

        traceback.print_exc()
        raise

    except ValueError as e:
        # Error lanzado por los métodos del transformer para validación estructural o lógica.
        print(f"\nError en el código Castella (Validación Estructural o Lógica durante la traducción):")
        print(e) # El mensaje de error detalla el problema.

        traceback.print_exc()
        raise

    except TypeError as e:
        # Error lanzado por el transformer por tipos inesperados o inconsistencias internas.
        print(f"\nError interno del Transformer (Tipos de datos inesperados o inconsistencia):")
        print(e)

        traceback.print_exc()
        raise

    except Exception as e:
        # Atrapar cualquier otra excepción inesperada que pueda ocurrir durante el parseo o transformación.
        print(f"\nOcurrió un error inesperado durante la traducción:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Detalle del error: {e}")

        traceback.print_exc()
        raise

# No se incluye `if __name__ == "__main__":` en este archivo, ya que es un módulo
# diseñado para ser importado. La lógica principal de ejecución está en `castella_compiler.py`.