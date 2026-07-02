#!/usr/bin/env python3
"""
convertir_a_csv.py
-------------------
Convierte de forma segura archivos .csv / .tsv / .txt de una carpeta de
entrada a un formato .csv estándar (UTF-8, delimitador ',') en una carpeta
de salida, SIN pérdida ni alteración de datos.

Por qué es "seguro":
- Lee y escribe fila a fila con el módulo csv (no con pandas), así que
  nunca se infieren tipos ni se redondean decimales (crítico con datos
  de expresión génica de alta precisión).
- Detecta el encoding real del archivo (utf-8, utf-8-sig, latin-1...) en
  vez de asumirlo, para no corromper caracteres.
- Detecta el delimitador real del contenido (no se fía solo de la
  extensión), porque un .txt puede venir con tabulador, ';' o espacios.
- Tras convertir, VALIDA que el nuevo .csv tiene exactamente el mismo
  número de filas y de columnas por fila que el original. Si algo no
  cuadra, el archivo se marca como FALLIDO y no se da por bueno.

Configuración de rutas:
    Las rutas NO van hardcodeadas ni por argumentos obligatorios: se leen de
    config.yaml (que no se sube a git, cada persona tiene el suyo con su
    propia ruta de Drive). Ver config.yaml.example para la plantilla.

Uso:
    # Conversión puntual (una pasada y termina)
    python convertir_a_csv.py

    # Modo vigilancia: se queda corriendo y convierte automáticamente
    # en cuanto aparece o cambia un archivo en la carpeta de entrada
    python convertir_a_csv.py --watch

    # Solo ver el estado (qué está convertido, qué falta), sin convertir nada
    python convertir_a_csv.py --status

    # Override manual de rutas sin tocar config.yaml
    python convertir_a_csv.py --input "G:\\Mi unidad\\OncoSeq\\raw" --output data/processed
"""

import argparse
import csv
import sys
import time
from pathlib import Path

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

CONFIG_PATH = Path(__file__).parent / "config.yaml"

# Aumentamos el límite de tamaño de campo por si alguna fila viene muy larga
csv.field_size_limit(sys.maxsize)

EXTENSIONES_VALIDAS = {".csv", ".tsv", ".txt"}
DELIMITADORES_CANDIDATOS = [",", "\t", ";", "|"]


def detectar_encoding(ruta: Path, muestra_bytes: int = 200_000) -> str:
    """Detecta el encoding del archivo leyendo una muestra de bytes."""
    with open(ruta, "rb") as f:
        raw = f.read(muestra_bytes)

    # BOM UTF-8 explícito
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    if HAS_CHARDET:
        resultado = chardet.detect(raw)
        encoding = resultado.get("encoding")
        confianza = resultado.get("confidence", 0)
        if encoding and confianza >= 0.6:
            return encoding

    # Fallback manual: probamos utf-8 estricto, si falla usamos latin-1
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"  # latin-1 nunca falla al decodificar


def detectar_delimitador(ruta: Path, encoding: str) -> str:
    """Detecta el delimitador real del archivo, con extensión como pista."""
    with open(ruta, "r", encoding=encoding, errors="replace", newline="") as f:
        muestra = f.read(65536)

    if not muestra.strip():
        raise ValueError("El archivo está vacío o no se pudo leer contenido.")

    # 1) Intentamos con el Sniffer de csv sobre varias líneas de muestra
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters="".join(DELIMITADORES_CANDIDATOS))
        return dialecto.delimiter
    except csv.Error:
        pass

    # 2) Fallback: contamos apariciones de cada delimitador candidato
    #    en la primera línea no vacía y nos quedamos con el más frecuente.
    primera_linea = next((l for l in muestra.splitlines() if l.strip()), "")
    conteos = {d: primera_linea.count(d) for d in DELIMITADORES_CANDIDATOS}
    mejor = max(conteos, key=conteos.get)

    if conteos[mejor] == 0:
        # Última opción: separación por espacios/tabs múltiples
        return "\t" if "\t" in primera_linea else " "

    return mejor


def contar_filas_y_columnas(ruta: Path, encoding: str, delimitador: str):
    """Devuelve (num_filas, [num_columnas_por_fila]) para validación."""
    filas = 0
    columnas_por_fila = []
    with open(ruta, "r", encoding=encoding, errors="replace", newline="") as f:
        lector = csv.reader(f, delimiter=delimitador)
        for fila in lector:
            filas += 1
            columnas_por_fila.append(len(fila))
    return filas, columnas_por_fila


def convertir_archivo(ruta_entrada: Path, ruta_salida: Path) -> dict:
    """Convierte un archivo a CSV estándar y valida el resultado."""
    resultado = {
        "archivo": ruta_entrada.name,
        "estado": "PENDIENTE",
        "detalle": "",
    }

    try:
        encoding = detectar_encoding(ruta_entrada)
        delimitador = detectar_delimitador(ruta_entrada, encoding)

        # Leemos y escribimos fila a fila, valor a valor, sin tocar nada.
        with open(ruta_entrada, "r", encoding=encoding, errors="replace", newline="") as f_in, \
             open(ruta_salida, "w", encoding="utf-8", newline="") as f_out:

            lector = csv.reader(f_in, delimiter=delimitador)
            escritor = csv.writer(f_out, delimiter=",", quoting=csv.QUOTE_MINIMAL)

            filas_leidas = 0
            for fila in lector:
                escritor.writerow(fila)
                filas_leidas += 1

        # --- Validación: releemos ambos archivos y comparamos ---
        filas_orig, cols_orig = contar_filas_y_columnas(ruta_entrada, encoding, delimitador)
        filas_nuevo, cols_nuevo = contar_filas_y_columnas(ruta_salida, "utf-8", ",")

        if filas_orig != filas_nuevo:
            resultado["estado"] = "FALLIDO"
            resultado["detalle"] = f"Nº de filas no coincide ({filas_orig} vs {filas_nuevo})"
            ruta_salida.unlink(missing_ok=True)
            return resultado

        if cols_orig != cols_nuevo:
            resultado["estado"] = "FALLIDO"
            resultado["detalle"] = "El nº de columnas por fila no coincide tras la conversión"
            ruta_salida.unlink(missing_ok=True)
            return resultado

        resultado["estado"] = "OK"
        resultado["detalle"] = (
            f"encoding={encoding}, delimitador original={repr(delimitador)}, "
            f"filas={filas_orig}, columnas={cols_orig[0] if cols_orig else 0}"
        )
        return resultado

    except Exception as e:
        resultado["estado"] = "FALLIDO"
        resultado["detalle"] = f"Error inesperado: {e}"
        return resultado


def cargar_config() -> dict:
    """Lee config.yaml (si existe) para obtener las rutas por defecto."""
    if HAS_YAML and CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            datos = yaml.safe_load(f) or {}
        return datos
    return {}


def procesar_carpeta(carpeta_entrada: Path, carpeta_salida: Path) -> None:
    """Convierte todos los archivos válidos de una carpeta. Se reutiliza
    tanto en la pasada única como en cada evento del modo --watch."""

    if not carpeta_entrada.exists():
        print(f"❌ La carpeta de entrada no existe: {carpeta_entrada}")
        return

    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivos = [
        p for p in sorted(carpeta_entrada.iterdir())
        if p.is_file() and p.suffix.lower() in EXTENSIONES_VALIDAS
    ]

    if not archivos:
        print(f"No se han encontrado archivos {EXTENSIONES_VALIDAS} en {carpeta_entrada}")
        return

    print(f"Encontrados {len(archivos)} archivo(s) en {carpeta_entrada}\n")

    resumen = []
    for archivo in archivos:
        nombre_salida = archivo.stem + ".csv"
        ruta_salida = carpeta_salida / nombre_salida

        # Si el .csv de salida ya existe y es más reciente que el original,
        # no hace falta reconvertir (evita trabajo repetido en modo watch).
        if ruta_salida.exists() and ruta_salida.stat().st_mtime >= archivo.stat().st_mtime:
            continue

        # Si ya es un .csv, comprobamos si ya está en formato estándar
        # (utf-8, delimitador ',') antes de decidir si hace falta convertir.
        if archivo.suffix.lower() == ".csv":
            try:
                encoding = detectar_encoding(archivo)
                delimitador = detectar_delimitador(archivo, encoding)
                if delimitador == "," and encoding.lower().replace("-", "") in ("utf8", "utf8sig", "ascii"):
                    print(f"⏭  {archivo.name}: ya está en formato CSV estándar, se copia tal cual.")
                    ruta_salida.write_bytes(archivo.read_bytes())
                    resumen.append({"archivo": archivo.name, "estado": "OK (sin cambios)", "detalle": "ya era CSV estándar"})
                    continue
            except Exception:
                pass  # si falla la detección, lo tratamos igualmente como conversión normal

        resultado = convertir_archivo(archivo, ruta_salida)
        resumen.append(resultado)

        icono = "✅" if resultado["estado"].startswith("OK") else "❌"
        print(f"{icono} {resultado['archivo']}: {resultado['estado']} — {resultado['detalle']}")

    if not resumen:
        print("Nada nuevo que convertir (todo ya estaba actualizado).")
        return

    ok = sum(1 for r in resumen if r["estado"].startswith("OK"))
    fallidos = sum(1 for r in resumen if r["estado"] == "FALLIDO")
    print(f"\nResumen: {ok} correcto(s), {fallidos} fallido(s), de {len(resumen)} archivo(s) procesado(s).")
    if fallidos:
        print("⚠️  Revisa los archivos marcados como FALLIDO antes de usarlos en el proyecto.")


def mostrar_estado(carpeta_entrada: Path, carpeta_salida: Path) -> None:
    """Imprime un cuadro con cada archivo de la carpeta de origen y si
    está pendiente de convertir, ya convertido y al día, o modificado
    después de la última conversión."""
    import datetime

    if not carpeta_entrada.exists():
        print(f"❌ La carpeta de entrada no existe: {carpeta_entrada}")
        return

    archivos = [
        p for p in sorted(carpeta_entrada.iterdir())
        if p.is_file() and p.suffix.lower() in EXTENSIONES_VALIDAS
    ]

    if not archivos:
        print(f"No se han encontrado archivos {EXTENSIONES_VALIDAS} en {carpeta_entrada}")
        return

    filas = []
    for archivo in archivos:
        ruta_salida = carpeta_salida / (archivo.stem + ".csv")
        mtime_origen = archivo.stat().st_mtime
        fecha = datetime.datetime.fromtimestamp(mtime_origen).strftime("%Y-%m-%d %H:%M")

        if not ruta_salida.exists():
            estado = "🆕 Sin convertir"
        elif ruta_salida.stat().st_mtime >= mtime_origen:
            estado = "✅ Convertido y al día"
        else:
            estado = "🔄 Modificado (pendiente)"

        filas.append((archivo.name, archivo.suffix.lower(), fecha, estado))

    # --- Anchos de columna dinámicos según el contenido ---
    col_archivo = max(len("Archivo"), max(len(f[0]) for f in filas))
    col_tipo = max(len("Tipo"), max(len(f[1]) for f in filas))
    col_fecha = max(len("Última modificación"), max(len(f[2]) for f in filas))
    col_estado = max(len("Estado"), max(len(f[3]) for f in filas))

    def linea_separadora(izq, medio, der):
        return izq + medio.join("─" * (c + 2) for c in (col_archivo, col_tipo, col_fecha, col_estado)) + der

    def fila_fmt(a, t, f, e):
        return f"│ {a.ljust(col_archivo)} │ {t.ljust(col_tipo)} │ {f.ljust(col_fecha)} │ {e.ljust(col_estado)} │"

    print(f"\nCarpeta de origen: {carpeta_entrada}\n")
    print(linea_separadora("┌", "┬", "┐"))
    print(fila_fmt("Archivo", "Tipo", "Última modificación", "Estado"))
    print(linea_separadora("├", "┼", "┤"))
    for a, t, f, e in filas:
        print(fila_fmt(a, t, f, e))
    print(linea_separadora("└", "┴", "┘"))

    pendientes = sum(1 for f in filas if "✅" not in f[3])
    print(f"\n{len(filas)} archivo(s) en total · {pendientes} pendiente(s) de conversión.")


def modo_vigilancia(carpeta_entrada: Path, carpeta_salida: Path, intervalo: int = 5) -> None:
    """Vigila la carpeta de entrada (p.ej. la de Drive) y reconvierte
    automáticamente en cuanto detecta un archivo nuevo o modificado.
    Usa polling simple (comprobar cada X segundos) en vez de watchdog
    porque las carpetas sincronizadas de Drive no siempre disparan
    eventos de sistema de archivos de forma fiable."""
    print(f"👀 Vigilando {carpeta_entrada} cada {intervalo}s. Ctrl+C para parar.\n")
    try:
        while True:
            procesar_carpeta(carpeta_entrada, carpeta_salida)
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\nVigilancia detenida.")


def main():
    config = cargar_config()

    parser = argparse.ArgumentParser(description="Convierte csv/tsv/txt a un .csv estándar de forma segura.")
    parser.add_argument("--input", default=config.get("carpeta_entrada"), help="Carpeta con los archivos originales (Drive)")
    parser.add_argument("--output", default=config.get("carpeta_salida", "data/processed"), help="Carpeta donde guardar los .csv resultantes")
    parser.add_argument("--watch", action="store_true", help="Deja el script corriendo y convierte automáticamente ante cualquier cambio")
    parser.add_argument("--status", action="store_true", help="Solo muestra un cuadro con el estado de cada archivo, sin convertir nada")
    parser.add_argument("--intervalo", type=int, default=config.get("intervalo_watch", 5), help="Segundos entre comprobaciones en modo --watch")
    args = parser.parse_args()

    if not args.input:
        print("❌ No se ha definido la carpeta de entrada.")
        print("   Crea un config.yaml (copia config.yaml.example) con 'carpeta_entrada: <ruta a tu Drive>'")
        print("   o pásala manualmente con --input")
        sys.exit(1)

    carpeta_entrada = Path(args.input)
    carpeta_salida = Path(args.output)

    if args.status:
        mostrar_estado(carpeta_entrada, carpeta_salida)
    elif args.watch:
        modo_vigilancia(carpeta_entrada, carpeta_salida, args.intervalo)
    else:
        procesar_carpeta(carpeta_entrada, carpeta_salida)


if __name__ == "__main__":
    main()