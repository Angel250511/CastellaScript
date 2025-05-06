# castella_backend.py

"""
Contiene funciones para generar ejecutables binarios a partir de código Python
(traducido desde Castella) usando PyInstaller y comprimirlos con UPX.
También incluye utilidades relacionadas con dependencias y limpieza.
"""

import os
import shutil # Para operaciones de archivos de alto nivel como copiar, mover, borrar árboles de directorios.
import subprocess # Para ejecutar comandos externos como PyInstaller y UPX.
import sys # Para acceder a información del sistema como el ejecutable de Python y la plataforma.
import re # Se mantuvo la importación ya que estaba en la función original, aunque podría no ser estrictamente necesaria para la limpieza final.

# Importar la función de traducción del módulo del parser.
# El backend necesita traducir el código Castella antes de empaquetarlo.
try:
    from .castella_parser import traducir_a_python
except ImportError as e:
    # Si falla la importación, reportar el error ya que este módulo depende del parser.
    print("\nError de Importación en castella_backend:")
    print("No se pudo importar la función 'traducir_a_python' desde 'castella_parser.py'.")
    print("Asegúrate de que 'castella_parser.py' exista en el mismo directorio.")
    print(f"Detalle: {e}")
    sys.exit(1) # Salir con un código de error.


from typing import Optional # Importar para la anotación de tipo de retorno Optional.

# === FUNCIONES DE UTILIDAD ===

def check_dependency(command: str, install_instructions: str, quiet=False) -> bool:
    """
    Verifica si un comando es accesible en el PATH del sistema.

    Esta función es utilizada para asegurar que herramientas como PyInstaller y UPX
    están disponibles antes de intentar ejecutarlas.

    Args:
        command: El nombre del comando a buscar (ej., "python", "pyinstaller", "upx").
        install_instructions: Una cadena que describe cómo instalar la herramienta,
                              mostrada si la herramienta no se encuentra.
        quiet: Si es True, suprime los mensajes de éxito o fallo.

    Returns:
        True si el comando es encontrado, False en caso contrario.
    """
    # shutil.which busca el comando en el PATH.
    if shutil.which(command) is None:
        if not quiet:
             # Imprimir un mensaje de error si el comando no se encuentra.
             print(f"\nError: La herramienta '{command}' no fue encontrada.")
             print(f"Por favor, asegúrate de que está instalada y accesible en tu PATH.")
             print(f"Instrucciones de instalación:", install_instructions)
        return False # La dependencia no está satisfecha.
    # if not quiet:
    #     # Mensaje opcional si se encuentra (silenciado por defecto).
    #     print(f"'{command}' encontrado.")
    return True # La dependencia está satisfecha.


def limpiar_archivos_temp(temp_py_file_path: str, pyinstaller_build_dir_name: str = "build"):
    """
    Limpia los archivos y directorios temporales generados por PyInstaller
    durante el proceso de construcción del binario (.py temp, .spec, build dir).

    Se ejecuta al inicio y al final del proceso de generación del binario.

    Args:
        temp_py_file_path: La ruta al archivo Python temporal que se creó.
                           A partir de esta ruta se derivan los nombres del .spec y el build dir.
        pyinstaller_build_dir_name: El nombre esperado del directorio de construcción de PyInstaller
                                    (por defecto es "build").
    """
    # Obtener la ruta absoluta del archivo temporal para derivar otras rutas de forma segura.
    abs_temp_py_file = os.path.abspath(temp_py_file_path)

    # El archivo .spec generado por PyInstaller suele estar en el mismo directorio que el script de entrada
    # y tiene el mismo nombre base con extensión .spec.
    abs_spec_file = os.path.splitext(abs_temp_py_file)[0] + ".spec"

    # El directorio de construcción de PyInstaller por defecto es "build" y se crea
    # en el mismo directorio que el archivo .spec y el script de entrada.
    abs_build_dir = os.path.join(os.path.dirname(abs_spec_file), pyinstaller_build_dir_name)

    try:
        # Intentar eliminar el archivo Python temporal.
        if os.path.exists(abs_temp_py_file) and os.path.isfile(abs_temp_py_file):
             os.remove(abs_temp_py_file)
             # print(f"Limpieza: Eliminado {os.path.basename(abs_temp_py_file)}") # Mensaje opcional

        # Intentar eliminar el archivo .spec generado por PyInstaller.
        if os.path.exists(abs_spec_file) and os.path.isfile(abs_spec_file):
             os.remove(abs_spec_file)
             # print(f"Limpieza: Eliminado {os.path.basename(abs_spec_file)}") # Mensaje opcional

        # Intentar eliminar el directorio de construcción de PyInstaller de forma recursiva.
        if os.path.exists(abs_build_dir) and os.path.isdir(abs_build_dir):
             # Verificación de seguridad: asegurar que no intentamos borrar el directorio actual
             # o un directorio padre accidentalmente.
             current_cwd = os.getcwd()
             relative_build_path = os.path.relpath(abs_build_dir, current_cwd)
             if relative_build_path != '.' and not relative_build_path.startswith('..'):
                 shutil.rmtree(abs_build_dir)
                 # print(f"Limpieza: Eliminado directorio {os.path.basename(abs_build_dir)}") # Mensaje opcional
             # else:
             #     print(f"Limpieza: Advertencia: El directorio de construcción '{pyinstaller_build_dir_name}' parece ser el directorio actual o padre. No se eliminará.") # Mensaje opcional

    except Exception as e:
        # Capturar cualquier error durante la limpieza e imprimir una advertencia.
        print(f"Advertencia al limpiar archivos temporales ({pyinstaller_build_dir_name}): {e}")

    # Nota: La limpieza del directorio 'dist' (donde va el ejecutable final)
    # se maneja por separado en generar_binario después de mover el archivo.


# === GENERADOR DE BINARIOS ===
def generar_binario(codigo_castella: str, nombre_binario_salida: str) -> Optional[str]:
    """
    Traduce código Castella a Python y genera un ejecutable binario autónomo
    utilizando PyInstaller.

    Orquesta los pasos de traducción, guardado temporal, ejecución de PyInstaller
    y manejo del archivo de salida.

    Args:
        codigo_castella: La cadena de texto con el código fuente en Castella.
        nombre_binario_salida: El nombre deseado para el archivo ejecutable final.
                               Puede incluir una ruta.

    Returns:
        La ruta absoluta al archivo binario generado exitosamente, o None si
        el proceso de generación falló en algún paso.
    """

    # 1. Traducir el código Castella a Python.
    # La función traducir_a_python maneja sus propios errores y los relanza.
    try:
        print("\n--- Paso 1: Traducción de Castella a Python ---")
        # Llama a la función del módulo castella_parser.
        codigo_python = traducir_a_python(codigo_castella)

        # Verificar si la traducción produjo código Python significativo.
        # Si la entrada Castella estaba vacía o solo con comentarios, traducir_a_python
        # podría retornar un string con un comentario. Esto es aceptable para PyInstaller.
        # Si retornara None o un string vacío inesperadamente, sería un problema.
        if codigo_python is None or not isinstance(codigo_python, str):
             print(f"Error interno: La traducción retornó un valor inesperado ({type(codigo_python)}) en lugar de una cadena de texto.")
             return None # Indica un fallo en la traducción.
        # Si el string es solo whitespace (aunque traducir_a_python debería retornar comentario),
        # PyInstaller con un archivo vacío podría fallar o generar un binario inútil.
        if not codigo_python.strip():
             print("La traducción resultó en un código Python vacío (o solo con espacios en blanco/comentarios).")
             print("Esto puede resultar en un ejecutable no funcional o un error de PyInstaller.")
             # Decidimos continuar, pero con una advertencia. Podríamos decidir abortar aquí.


    except Exception:
         # Si traducir_a_python lanza una excepción (sintaxis, transformer, etc.),
         # ya ha impreso los detalles. Solo necesitamos capturar aquí para detener
         # el proceso de generación del binario.
         print("La traducción falló. Abortando generación del binario.")
         return None # Indica un fallo.


    # 2. Guardar el código Python generado temporalmente.
    # PyInstaller necesita un archivo de script como entrada.
    # Usamos un nombre de archivo temporal fijo dentro del directorio actual.
    temp_py_file_name = "castella_temp_script.py"

    # Nombre del proyecto que PyInstaller usará para el .spec, build dir, y base del archivo de salida.
    # Lo derivamos del nombre deseado para el binario final.
    pyinstaller_project_name = os.path.splitext(os.path.basename(nombre_binario_salida))[0]
    # Asegurarse de que el nombre del proyecto no esté vacío si nombre_binario_salida era solo una extensión o path raro.
    if not pyinstaller_project_name:
         pyinstaller_project_name = "compiled_app" # Nombre de fallback

    # Nombres estándar de los directorios temporales de PyInstaller.
    pyinstaller_dist_dir_name = "dist"
    pyinstaller_build_dir_name = "build"

    # Limpiar archivos temporales y directorios de compilaciones previas antes de empezar.
    print("\n--- Limpiando archivos temporales de PyInstaller (fase inicial) ---")
    limpiar_archivos_temp(temp_py_file_name, pyinstaller_build_dir_name)

    # Intentar limpiar también el directorio 'dist' previo si parece estar obsoleto
    # (ej., no contiene el ejecutable esperado del último intento).
    prev_dist_abs_path = os.path.abspath(pyinstaller_dist_dir_name)
    prev_expected_exe_name_in_dist = pyinstaller_project_name
    # PyInstaller añade .exe al nombre del archivo en Windows si es onefile en el directorio dist.
    if sys.platform.startswith('win'):
        prev_expected_exe_name_in_dist += '.exe'
    prev_expected_exe_abs_path = os.path.join(prev_dist_abs_path, prev_expected_exe_name_in_dist)

    if os.path.exists(prev_dist_abs_path) and os.path.isdir(prev_dist_abs_path):
         # Solo limpiar si el ejecutable esperado NO existe en el directorio 'dist'.
         if not os.path.exists(prev_expected_exe_abs_path):
              try:
                  current_cwd = os.getcwd()
                  # Segunda verificación de seguridad: no borrar directorios sensibles.
                  relative_dist_path = os.path.relpath(prev_dist_abs_path, current_cwd)
                  if relative_dist_path != '.' and not relative_dist_path.startswith('..'):
                       print(f"(Limpiando antiguo directorio '{pyinstaller_dist_dir_name}')")
                       shutil.rmtree(prev_dist_abs_path)
              except Exception as e:
                  print(f"Advertencia al intentar limpiar el directorio '{pyinstaller_dist_dir_name}': {e}")


    try:
        print("\n--- Paso 2: Guardar código Python temporal ---")
        # Escribir el código Python traducido al archivo temporal.
        # Es CRUCIAL especificar la codificación a 'utf-8' para evitar problemas.
        with open(temp_py_file_name, "w", encoding="utf-8") as archivo:
            archivo.write(codigo_python)
        print(f"Código Python guardado temporalmente en '{temp_py_file_name}'")

        # 3. Generar el ejecutable usando PyInstaller.
        print("\n--- Paso 3: Generar ejecutable con PyInstaller (esto puede tardar varios minutos) ---")

        # Asegurarse de que el ejecutable de Python esté disponible para ejecutar PyInstaller.
        python_executable = sys.executable
        # check_dependency imprime mensajes si falla, usamos quiet=True porque la verificación principal
        # ya se hizo en castella_compiler y reportó al usuario.
        if not check_dependency(python_executable, "El intérprete de Python es necesario para ejecutar PyInstaller.", quiet=True):
             # Aunque ya se verificó Python antes, esta es una verificación adicional de que sys.executable funciona.
             print(f"Error: El ejecutable de Python '{python_executable}' no se encuentra o no es ejecutable.")
             return None # No se puede continuar sin Python.

        # Construir el comando para ejecutar PyInstaller.
        # -m PyInstaller: Ejecuta PyInstaller como un módulo del intérprete actual.
        # --onefile: Empaqueta todo en un solo archivo ejecutable.
        # --clean: Limpia la caché y los directorios temporales de PyInstaller antes de la construcción.
        # --name <nombre>: Define el nombre base del archivo de salida y otros directorios temporales.
        # --distpath .: Especifica el directorio de salida para el binario final. "." significa el directorio actual.
        # <script_entrada>: El script Python a empaquetar (nuestro archivo temporal).
        command = [
            python_executable,
            "-m", "PyInstaller",
            "--onefile",
            "--clean",
            "--name", pyinstaller_project_name,
            "--distpath", ".", # Salida directa al directorio actual.
            temp_py_file_name
        ]

        print(f"Ejecutando comando: {' '.join(command)}")

        # Ejecutar el comando de PyInstaller como un subproceso.
        # cwd=".": Ejecutar el comando en el directorio actual donde guardamos el archivo temporal.
        # capture_output=True: Capturar stdout y stderr del subproceso.
        # text=True: Decodificar stdout/stderr como texto (útil para imprimir mensajes).
        # check=True: Lanza subprocess.CalledProcessError si el subproceso retorna un código de salida no-cero (indicando error).
        process = subprocess.run(
            command,
            cwd=".",
            capture_output=True,
            text=True,
            check=True
        )

        # Si el proceso fue exitoso (no lanzó CalledProcessError), imprimimos la salida.
        print("PyInstaller STDOUT:\n", process.stdout)
        if process.stderr: # Imprimir stderr solo si contiene algo.
             print("PyInstaller STDERR:\n", process.stderr)
        print("PyInstaller completado exitosamente.")

        # 4. Localizar el ejecutable generado y moverlo/renombrarlo si es necesario.
        # Con --onefile y --distpath ., PyInstaller deja el ejecutable directamente
        # en el directorio actual con el nombre especificado por --name (más la extensión del sistema).
        generated_exe_name_with_ext = pyinstaller_project_name
        if sys.platform.startswith('win'):
            generated_exe_name_with_ext += '.exe' # Añadir .exe en Windows.

        # Ruta donde PyInstaller debería haber dejado el archivo.
        source_exe_path_in_cwd = os.path.join(".", generated_exe_name_with_ext)
        # La ruta final deseada por el usuario.
        final_target_path = nombre_binario_salida

        # Convertir a rutas absolutas para operaciones de archivo más robustas.
        abs_source_path = os.path.abspath(source_exe_path_in_cwd)
        abs_final_target_path = os.path.abspath(final_target_path)

        # Verificar si el ejecutable generado realmente existe.
        if os.path.exists(abs_source_path) and os.path.isfile(abs_source_path):
             # Si la ruta de origen (lo que generó PyInstaller) es diferente de la ruta final deseada, mover/renombrar.
             if abs_source_path != abs_final_target_path:
                 print(f"\nRenombrando/moviendo '{os.path.basename(abs_source_path)}' a '{final_target_path}'")
                 # Si el archivo de destino ya existe, intentamos borrarlo primero.
                 if os.path.exists(abs_final_target_path) and os.path.isfile(abs_final_target_path):
                      # print(f"Advertencia: El archivo de destino '{final_target_path}' ya existe y será sobrescrito.") # Mensaje informativo
                      try: os.remove(abs_final_target_path)
                      except Exception as e:
                          print(f"Error al intentar eliminar el archivo de destino '{final_target_path}' antes de mover: {e}.")
                          # Si no podemos eliminar el archivo existente, reportamos y fallamos.
                          return None

                 try:
                    # Usamos shutil.move que maneja renombrar si están en el mismo sistema de archivos
                    # o copiar+borrar si están en diferentes sistemas de archivos.
                    shutil.move(abs_source_path, abs_final_target_path)
                    print(f"Ejecutable generado y renombrado/movido a: '{final_target_path}'")
                 except Exception as e:
                     # Capturar errores durante la operación de mover.
                     print(f"Error al intentar renombrar/mover '{os.path.basename(abs_source_path)}' a '{final_target_path}': {e}")
                     return None # Indica fallo en el movimiento.
             else:
                  # Si la ruta de origen y destino son las mismas, el archivo ya está donde queremos.
                  print(f"\nEjecutable generado en: '{final_target_path}'")

             # Retornar la ruta absoluta del binario generado exitosamente.
             return abs_final_target_path

        else:
            # Si el ejecutable no se encontró donde esperábamos, algo falló en PyInstaller
            # a pesar de no lanzar un error de proceso, o la lógica de ruta es incorrecta.
            print(f"Error: No se encontró el ejecutable esperado '{source_exe_path_in_cwd}' en el directorio actual después de la construcción de PyInstaller.")
            print("Verifique la salida de PyInstaller arriba para posibles errores en la fase de empaquetado o enlace.")
            return None # Indica fallo.

    # --- Manejo de Errores Específicos de Subproceso PyInstaller ---
    except FileNotFoundError:
         # Este error ocurre si el comando `python` o `pyinstaller` no se encuentra en el PATH.
         print(f"\nError: No se encontró el comando para ejecutar PyInstaller ('{python_executable} -m PyInstaller').")
         print("Asegúrate de que Python está en tu PATH y PyInstaller está instalado (`pip install pyinstaller`).")
         return None

    except subprocess.CalledProcessError as e:
        # Este error ocurre si PyInstaller se ejecutó pero retornó un código de salida de error.
        print(f"\nError al ejecutar PyInstaller:")
        print(f"  Comando: {' '.join(e.cmd)}")
        print(f"  Directorio de trabajo: {e.cwd}")
        print(f"  Código de salida: {e.returncode}")
        # Imprimir la salida capturada para ayudar a diagnosticar el problema de PyInstaller.
        if e.stdout: print(f"  STDOUT:\n{e.stdout}")
        if e.stderr: print(f"  STDERR:\n{e.stderr}")
        print("La generación del ejecutable con PyInstaller falló.")
        return None

    except Exception as e:
        # Capturar cualquier otra excepción inesperada durante la generación del binario
        # (ej. errores al escribir el archivo temporal, errores de permisos, etc.).
        print(f"\nOcurrió un error inesperado durante la generación del binario:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Detalle del error: {e}")
        import traceback # Importar traceback aquí si no se hizo globalmente
        traceback.print_exc()
        return None

    finally:
        # Asegurarse de que los archivos y directorios temporales de PyInstaller se limpien
        # incluso si ocurrió un error después de crearlos.
        # Nota: El argumento --clean de PyInstaller también ayuda, pero esto es una red de seguridad.
        print("\n--- Limpiando archivos temporales de PyInstaller (fase final) ---")
        # Llamar a la función de limpieza con el nombre del archivo temporal usado.
        limpiar_archivos_temp(temp_py_file_name, pyinstaller_build_dir_name)
        print("-----------------------------------------------------------------")


def comprimir_binario(nombre_binario_path: str):
    """
    Comprime un archivo binario existente usando la herramienta UPX.

    Args:
        nombre_binario_path: La ruta al archivo binario que se desea comprimir.
    """
    # Verificar si el archivo binario existe en la ruta proporcionada.
    if not os.path.exists(nombre_binario_path) or not os.path.isfile(nombre_binario_path):
        print(f"\nAdvertencia: El archivo binario '{os.path.basename(nombre_binario_path)}' no fue encontrado o no es un archivo para comprimir con UPX.")
        return # No se puede comprimir si el archivo no existe.

    # Verificar si la herramienta UPX está disponible en el sistema.
    # Usamos quiet=True porque la verificación principal ya se hizo en castella_compiler.
    if not check_dependency("upx", "Descárgalo e instálalo desde https://upx.github.io/.", quiet=True):
         print("UPX no encontrado o no accesible en el PATH. Saltando compresión.")
         return # No se puede comprimir si UPX no está disponible.

    try:
        print(f"\n--- Comprimiendo '{os.path.basename(nombre_binario_path)}' con UPX ---")

        # Construir el comando para ejecutar UPX.
        # El uso básico es 'upx [opciones] archivo'. La opción por defecto suele ser suficiente.
        command = ["upx", nombre_binario_path]

        print(f"Ejecutando comando: {' '.join(command)}")

        # Ejecutar el comando de UPX como un subproceso.
        # Similar a PyInstaller, capturamos la salida y verificamos el código de salida.
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        # Imprimir la salida de UPX. UPX a menudo reporta estadísticas de compresión por stderr.
        if process.stdout: print("UPX STDOUT:\n", process.stdout)
        if process.stderr: print("UPX STDERR:\n", process.stderr) # UPX a menudo usa STDERR para info/warnings
        print(f"Compresión completada: '{os.path.basename(nombre_binario_path)}'")

    # --- Manejo de Errores Específicos de Subproceso UPX ---
    except FileNotFoundError:
        # Este error debe ser capturado por check_dependency antes, pero es una red de seguridad.
        print(f"\nError: No se encontró el comando 'upx'.")
        print("Asegúrate de que UPX está instalado y en tu PATH.")

    except subprocess.CalledProcessError as e:
        # Este error ocurre si UPX se ejecutó pero retornó un código de salida de error.
        print(f"\nError al ejecutar UPX:")
        print(f"  Comando: {' '.join(e.cmd)}")
        # Imprimir la salida capturada para ayudar a diagnosticar el problema de UPX.
        if e.stdout: print(f"  STDOUT:\n{e.stdout}")
        if e.stderr: print(f"  STDERR:\n{e.stderr}")
        print(f"  Código de salida: {e.returncode}")
        print("La compresión con UPX falló.")

    except Exception as e:
        # Capturar cualquier otra excepción inesperada durante la compresión.
        print(f"\nOcurrió un error inesperado durante la compresión:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Detalle del error: {e}")
        import traceback # Importar traceback aquí si no se hizo globalmente
        traceback.print_exc()

# No se incluye `if __name__ == "__main__":` en este archivo, ya que es un módulo
# diseñado para ser importado. La lógica principal de ejecución está en `castella_compiler.py`.