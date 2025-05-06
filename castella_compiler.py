# castella_compiler.py

"""
Compilador de Castella a ejecutable binario.
Este es el script principal que gestiona la línea de comandos,
lee el archivo de entrada y orquesta el proceso de traducción y empaquetado.
"""

import sys # Para acceder a los argumentos de línea de comandos y salir del programa.
import os  # Para operar con rutas de archivos y directorios (ej. os.path.splitext, os.path.basename, os.getcwd).
import shutil # Importar para operaciones como os.path.isfile o shutil.which (aunque check_dependency lo usa internamente).

# Importar las funciones clave y utilidades de nuestros módulos de backend y parser.
# Usamos importaciones relativas ya que se espera que estos archivos estén juntos en un paquete.
try:
    # Importar la función principal para generar el binario y la función para comprimir.
    from .castella_backend import generar_binario, comprimir_binario, check_dependency
    # Importar traducir_a_python (aunque generar_binario la llama internamente,
    # mantener la importación podría ser útil si se añade una opción solo de traducción).
    from .castella_parser import traducir_a_python # Importada aquí para verificación de dependencia 'lark' también.
except ImportError as e:
    # Si falla la importación de cualquier módulo nuestro, el programa no puede continuar.
    print("\nError de Importación:")
    print("No se pudieron importar los módulos internos del compilador (backend, parser).")
    print("Asegúrate de que 'castella_backend.py', 'castella_parser.py' y 'castella_transformer.py'")
    print("existan en el mismo directorio que 'castella_compiler.py'")
    print("y que estás ejecutando el compilador desde el directorio contenedor o como un paquete.")
    print(f"Detalle: {e}")
    sys.exit(1) # Salir con un código de error para indicar un fallo grave.

# No necesitamos importar lark, numpy, matplotlib, etc., directamente aquí,
# ya que los usamos a través de las funciones importadas de los otros módulos,
# y sus dependencias se verifican en los módulos correspondientes o en check_dependency.


def main():
    """
    Función principal del compilador Castella.

    Gestiona la entrada del usuario (línea de comandos o prompts),
    verifica las dependencias, lee el archivo fuente, llama a la
    generación del binario y a la compresión opcional, y reporta el resultado.
    """
    print("=== COMPILADOR CASTELLA ===")

    print("\n--- Verificando dependencias esenciales ---")

    # Verificar dependencias clave que necesita el proceso completo:
    # 1. La librería Lark (Python package) - necesaria para el parser.
    # 2. La herramienta PyInstaller (comando externo) - necesaria para generar el binario.
    # 3. La herramienta UPX (comando externo) - opcional, necesaria para comprimir.

    # Verificación de Lark (importable como paquete Python).
    try:
        import lark
        lark_ok = True
        print(f"'lark' encontrado (versión {lark.__version__}).")
    except ImportError:
        lark_ok = False
        print("\nError: La librería 'lark' no fue encontrada.")
        print("Por favor, instálala con: pip install lark")

    # Verificación de PyInstaller (como comando en el PATH).
    # check_dependency imprime mensajes si falla. Usamos quiet=False para que el usuario vea el resultado.
    pyinstaller_ok = check_dependency("pyinstaller", "Instálalo con: pip install pyinstaller", quiet=False)

    # Verificación de UPX (como comando en el PATH). Es opcional.
    # No salimos si falla, solo informamos. Usamos quiet=True para un mensaje más conciso aquí.
    upx_available = check_dependency("upx", "Descárgalo e instálalo desde https://upx.github.io/.", quiet=True)
    if upx_available:
        print("'upx' encontrado.")
    else:
        print("'upx' no encontrado. La compresión de binarios no estará disponible.")


    print("------------------------------------------")

    # Si PyInstaller o Lark no están disponibles, no podemos continuar.
    if not pyinstaller_ok or not lark_ok:
         print("\nNo se pudieron resolver todas las dependencias necesarias (Lark y/o PyInstaller).")
         print("Por favor, instálalas y asegúrate de que estén accesibles en tu entorno/PATH.")
         sys.exit(1) # Salir con un código de error.

    # --- Procesamiento de argumentos de línea de comandos ---
    # Los argumentos esperados son:
    # sys.argv[1]: Ruta al archivo Castella de entrada.
    # sys.argv[2]: Nombre deseado para el archivo binario de salida (opcional).
    # sys.argv[3]: Opción de compresión ("s" o "n") (opcional).

    input_file_arg = None
    output_name_arg = None
    compress_arg_str = None # Usamos un nombre claro para la cadena del argumento.

    # Leer los argumentos si están presentes.
    if len(sys.argv) > 1:
        input_file_arg = sys.argv[1]
    if len(sys.argv) > 2:
        output_name_arg = sys.argv[2]
    if len(sys.argv) > 3:
        compress_arg_str = sys.argv[3].lower() # Leer el tercer argumento y convertir a minúsculas.

    # --- Obtener la ruta del archivo de entrada Castella ---
    archivo_castella_path = input_file_arg
    if not archivo_castella_path:
         # Si no se proporcionó la ruta como argumento, solicitarla al usuario.
         archivo_castella_path = input("Introduce la ruta al archivo Castella (.castella): ").strip()
         if not archivo_castella_path:
              print("Error: No se especificó una ruta para el archivo Castella de entrada.")
              sys.exit(1) # Salir si el usuario no proporciona la ruta.

    # Asegurarse de que la ruta termine en ".castella" si no se especificó la extensión.
    if not archivo_castella_path.lower().endswith(".castella"):
        archivo_castella_path += ".castella"

    # Verificar si el archivo de entrada existe y es un archivo.
    # Usamos os.path.isfile para verificar que existe y no es un directorio.
    if not os.path.isfile(archivo_castella_path):
        print(f"Error: El archivo de entrada '{archivo_castella_path}' no existe o no es un archivo válido.")
        print(f"Directorio actual de ejecución: '{os.getcwd()}'") # Mostrar el directorio actual para contexto.
        sys.exit(1) # Salir si el archivo no se encuentra.


    # --- Obtener el nombre deseado para el binario de salida ---
    nombre_binario_salida = output_name_arg
    if not nombre_binario_salida:
         # Si no se proporcionó el nombre de salida como argumento, solicitarlo al usuario.
         # Ofrecer un nombre por defecto basado en el nombre del archivo de entrada.
         base_name = os.path.splitext(os.path.basename(archivo_castella_path))[0]
         default_name = base_name
         # Añadir la extensión .exe por defecto en Windows para mayor usabilidad.
         if sys.platform.startswith('win'):
             default_name += '.exe'
         nombre_binario_salida = input(f"Introduce el nombre deseado para el ejecutable generado (Enter para '{default_name}'): ").strip()
         # Si el usuario no ingresa nada, usar el nombre por defecto.
         if not nombre_binario_salida:
              print(f"Usando nombre por defecto: '{default_name}'")
              nombre_binario_salida = default_name
         # Si el usuario ingresó un nombre en Windows pero sin .exe, añadirlo.
         elif sys.platform.startswith('win') and not nombre_binario_salida.lower().endswith('.exe'):
             nombre_binario_salida += '.exe'

    # --- Leer el código fuente de Castella ---
    codigo_castella = ""
    try:
        print(f"\n--- Leyendo archivo '{archivo_castella_path}' ---")
        # Abrir el archivo con codificación UTF-8 para asegurar que se lean correctamente
        # caracteres especiales, comentarios multilínea, etc.
        with open(archivo_castella_path, "r", encoding="utf-8") as f:
            codigo_castella = f.read()
        print("--- Archivo leído exitosamente ---")
    except FileNotFoundError:
         # Este caso debería haber sido capturado por os.path.isfile, pero es una red de seguridad.
         print(f"Error: El archivo '{archivo_castella_path}' no existe (FileNotFoundError inesperado).")
         sys.exit(1)
    except Exception as e:
        # Capturar cualquier otro error durante la lectura del archivo (permisos, problemas de codificación, etc.).
        print(f"Error al leer el archivo '{archivo_castella_path}': {e}")
        # Imprimir traceback para ayudar a depurar problemas de lectura.
        # import traceback; traceback.print_exc() # Ya importado globalmente si se necesita
        sys.exit(1) # Salir con un código de error.


    # --- Generar el ejecutable binario ---
    print("\n--- Iniciando proceso de generación de binario ---")
    # Llamar a la función principal del backend. Esta función se encarga de todo:
    # traducir (llamando al parser), guardar temporalmente, ejecutar PyInstaller.
    # Retorna la ruta al binario generado (o None si falló).
    nombre_binario_generado_path = generar_binario(codigo_castella, nombre_binario_salida)
    print("--- Finalizado proceso de generación de binario ---")

    # --- Compresión Opcional con UPX ---
    # Solo intentar la compresión si la generación del binario fue exitosa.
    if nombre_binario_generado_path:
         # Ya verificamos si UPX está disponible al inicio.
         if upx_available:
              # Determinar si se solicita la compresión (desde el argumento o interacción).
              comprimir_solicitado = False
              if compress_arg_str is not None:
                   # La opción de compresión se especificó en la línea de comandos.
                   if compress_arg_str in ("s", "si"):
                        comprimir_solicitado = True
                   elif compress_arg_str not in ("n", "no"):
                        # Advertir si el argumento de compresión no es válido.
                        print(f"\nOpción de compresión '{compress_arg_str}' no válida. Use 's' o 'n'. Saltando compresión.")
              else:
                   # La opción no se especificó en línea de comandos, preguntar al usuario.
                   comprimir_input = input(f"\n¿Deseas comprimir el binario '{os.path.basename(nombre_binario_generado_path)}' con UPX? (s/n): ").strip().lower()
                   if comprimir_input in ("s", "sí", "si"):
                        comprimir_solicitado = True

              # Si la compresión fue solicitada Y UPX está disponible, ejecutar la compresión.
              if comprimir_solicitado:
                  print("\n--- Iniciando proceso de compresión con UPX ---")
                  comprimir_binario(nombre_binario_generado_path) # Llamar a la función del backend.
                  print("--- Finalizado proceso de compresión con UPX ---")

         else:
             # UPX no está disponible. Si el usuario intentó solicitarlo por argumento, reportar como error.
             print("\nUPX no encontrado. La compresión de binarios no está disponible.")
             if compress_arg_str is not None and compress_arg_str in ("s", "si"):
                 # El usuario pidió explícitamente compresión pero no fue posible. Salir con error.
                 print("La compresión fue solicitada en línea de comandos pero UPX no está disponible en el PATH.")
                 sys.exit(1)


    print("\n=== Proceso completado. ===")

    # Salir del script principal.
    # sys.exit(0) indica éxito. sys.exit(1) indica fallo.
    if nombre_binario_generado_path:
         sys.exit(0) # Éxito: El binario se generó (y posiblemente comprimió).
    else:
         # Si generar_binario retornó None, significa que falló.
         print("La generación del binario falló durante el proceso.")
         sys.exit(1) # Fallo.


# Bloque de entrada principal.
# Esto asegura que la función main() se ejecute solo cuando el script se llama directamente.
if __name__ == "__main__":
    main()