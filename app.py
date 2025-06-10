from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_from_directory, send_file
from flask import send_from_directory
import os
import glob
import pandas as pd
from datetime import date, datetime
import random
import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PyPDF2 import PdfMerger
import xml.etree.ElementTree as ET
import re
import json
from datetime import date

# Blueprints de usuarios
from usuarios import bp_usuarios   # Asegúrate que tu archivo usuarios.py tenga 'bp_usuarios' definido correctamente

# OTRAS IMPORTACIONES DE BLUEPRINTS SI LAS TIENES
app = Flask(__name__)


import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARCHIVO_NUMEROS_MARCADOS = os.path.join(DATA_DIR, "numeros_marcados.txt")
ASIGNACIONES_DIR = os.path.join(BASE_DIR, "asignaciones")

ARCHIVOS_CARTONES = [
    os.path.join(DATA_DIR, "Srs_ib1.csv"),
    os.path.join(DATA_DIR, "Srs_ib2.csv"),
    os.path.join(DATA_DIR, "Srs_ib3.csv"),
    os.path.join(DATA_DIR, "Srs_Manilla.csv"),
    # agrega más si tienes más archivos
]

def cargar_numeros_marcados():
    if not os.path.exists(ARCHIVO_NUMEROS_MARCADOS):
        return []
    with open(ARCHIVO_NUMEROS_MARCADOS, "r") as f:
        return [int(x) for x in f.read().split(",") if x.strip()]


# ==== BINGO Y GANADOR ====

def es_carton_lleno(boleto, numeros_marcados):
    try:
        carton = []
        carton += [int(boleto[f'b{i}']) if pd.notna(boleto[f'b{i}']) and str(boleto[f'b{i}']).isdigit() else 0 for i in range(1, 6)]
        carton += [int(boleto[f'i{i}']) if pd.notna(boleto[f'i{i}']) and str(boleto[f'i{i}']).isdigit() else 0 for i in range(1, 6)]
        carton += [int(boleto[f'n{i}']) if pd.notna(boleto[f'n{i}']) and str(boleto[f'n{i}']).isdigit() else 0 for i in range(1, 6)]
        carton += [int(boleto[f'g{i}']) if pd.notna(boleto[f'g{i}']) and str(boleto[f'g{i}']).isdigit() else 0 for i in range(1, 6)]
        carton += [int(boleto[f'o{i}']) if pd.notna(boleto[f'o{i}']) and str(boleto[f'o{i}']).isdigit() else 0 for i in range(1, 6)]
    except KeyError as e:
        print(f"ERROR KeyError en boleto {boleto.get('numero','?')}: columna faltante: {e}")
        return False
    # El centro del cartón (N3) suele ser 0 (libre), no es necesario marcarlo
    for num in carton:
        if num != 0 and num not in numeros_marcados:
            return False
    return True



def buscar_ganadores_carton_lleno(archivos_csv, numeros_marcados):
    ganadores = []
    for archivo in archivos_csv:
        if not os.path.exists(archivo):
            continue
        df = pd.read_csv(archivo)
        df.columns = [col.strip().lower() for col in df.columns]  # Normaliza siempre
        for idx, boleto in df.iterrows():
            if es_carton_lleno(boleto, numeros_marcados):
                nombre_archivo = os.path.basename(archivo)
                ganadores.append({
                    "archivo": nombre_archivo,
                    "numero": boleto['numero'],
                    "carton": [int(boleto[f'b{i}']) for i in range(1, 6)] +
                              [int(boleto[f'i{i}']) for i in range(1, 6)] +
                              [int(boleto[f'n{i}']) for i in range(1, 6)] +
                              [int(boleto[f'g{i}']) for i in range(1, 6)] +
                              [int(boleto[f'o{i}']) for i in range(1, 6)]
                })
    return ganadores


# EJECUTA PARA PROBAR:
if __name__ == '__main__':
    numeros_marcados = cargar_numeros_marcados()
    ganadores = buscar_ganadores_carton_lleno(ARCHIVOS_CARTONES, numeros_marcados)
    if ganadores:
        print("¡Boletos ganadores (cartón lleno):")
        for archivo, numero in ganadores:
            print(f"- Archivo: {archivo}, Boleto: {numero}")
    else:
        print("Aún no hay ganadores.")





    
def guardar_numeros_marcados(numeros):
    with open(ARCHIVO_NUMEROS_MARCADOS, "w") as f:
        f.write(",".join(map(str, numeros)))

def marcar_numero_bingo(numero):
    numeros = cargar_numeros_marcados()
    if int(numero) not in numeros:
        numeros.append(int(numero))
        guardar_numeros_marcados(numeros)
        return True
    return False


def resetear_numeros_marcados():
    with open(ARCHIVO_NUMEROS_MARCADOS, "w") as f:
        f.write("")
    return []

from flask import jsonify

@app.route('/api/ganadores_carton_lleno')
def api_ganadores_carton_lleno():
    numeros_marcados = cargar_numeros_marcados()
    ganadores = buscar_ganadores_carton_lleno(ARCHIVOS_CARTONES, numeros_marcados)
    return jsonify({"ganadores": ganadores})


@app.route('/api/historial_numeros')
def api_historial_numeros():
    numeros = cargar_numeros_marcados()
    return jsonify({"numeros": numeros})





@app.route('/resetear_numeros_marcados', methods=['POST'])
def resetear_numeros_marcados_route():
    resetear_numeros_marcados()
    return jsonify({"success": True, "mensaje": "Historial de números marcados reseteado."})





app.secret_key = 'clave-secreta-segura'

# Claves independientes por sección
CLAVES_SECCIONES = {
    "dashboard": "PlandeDios10",
    "vendedores": "PlandeDios10",
    "impresion": "PlandeDios10",
    "asignar_planillas": "PlandeDios10"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RUTA_FIGURAS_CREADAS = os.path.join(DATA_DIR, "figuras_creadas.xml")
RUTA_FIGURAS_DIA = os.path.join(DATA_DIR, "figuras_del_dia.xml")
XML_PATH = os.path.join(DATA_DIR, 'datos_bingo.xml')
CONFIG_FILE = os.path.join(DATA_DIR, "config_srs.json")



# === FUNCIONES XML ===

def cargar_figuras_guardadas():
    figuras = []
    if not os.path.exists(RUTA_FIGURAS_CREADAS):
        return figuras
    tree = ET.parse(RUTA_FIGURAS_CREADAS)
    root = tree.getroot()
    for figura in root.findall("figura"):
        nombre = figura.attrib.get("nombre", "")
        matriz = []
        for cuadro in figura.findall("cuadro"):
            colores_fila = cuadro.text.split(",")
            matriz.extend(colores_fila)
        figuras.append({"nombre": nombre, "colores": matriz})
    return figuras

def cargar_figuras_del_dia():
    figuras = []
    if not os.path.exists(RUTA_FIGURAS_DIA):
        return figuras
    tree = ET.parse(RUTA_FIGURAS_DIA)
    root = tree.getroot()
    for fig in root.findall("figura"):
        nombre = fig.get("nombre")
        valor = fig.get("valor", "")
        estado = fig.get("estado", "")
        colores = []
        for cuadro in fig.findall("cuadro"):
            colores.extend(cuadro.text.split(","))
        figuras.append({
            "nombre": nombre,
            "valor": valor,
            "estado": estado,
            "colores": colores
        })
    return figuras

# === SEGURIDAD DE SECCIONES ===

def requiere_clave(seccion):
    clave_correcta = CLAVES_SECCIONES.get(seccion)
    clave_guardada = session.get(f'clave_{seccion}')
    return clave_guardada == clave_correcta

@app.route('/clave/<seccion>', methods=['GET', 'POST'])
def pedir_clave(seccion):
    if seccion not in CLAVES_SECCIONES:
        return "Sección inválida", 404
    error = ""
    if request.method == "POST":
        clave = request.form.get("clave")
        if clave == CLAVES_SECCIONES[seccion]:
            session[f'clave_{seccion}'] = clave
            return redirect(url_for(seccion))
        else:
            error = "Clave incorrecta"
    return render_template("clave.html", seccion=seccion, error=error)

# === RUTAS DEL SISTEMA ===

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario == 'GLSTUDIOS' and clave == 'LiamLara..2912':
            session['usuario'] = usuario
            return redirect(url_for('tablero'))
        else:
            return render_template('login.html', error="Usuario o clave incorrectos")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/tablero')
def tablero():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    figuras_bingo = cargar_figuras_guardadas()
    figuras_dia = cargar_figuras_del_dia()
    return render_template(
        'tablero.html',
        figuras_bingo=figuras_bingo,
        figuras_dia=figuras_dia
    )






def obtener_archivos_srs():
    """Devuelve lista de archivos XML tipo Srs_*.xml en /data."""
    archivos = []
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith('.xml') and fname.lower().startswith('srs_'):
            archivos.append(fname)
    archivos.sort()
    return archivos


# ================= PANEL DE FIGURAS =================
@app.route('/panel_figuras')
def panel_figuras():
    archivos_srs = obtener_archivos_srs()
    figuras_bingo = cargar_figuras_guardadas()
    figuras_dia = cargar_figuras_del_dia()
    def figura_imagen(figura):
        estado = figura.get('estado', 'normal')
        if estado == "se_fue":
            return "se fue.png"
        elif estado == "se_quedo":
            return "se quedo.png"
        else:
            return f"{figura['nombre']}.png"
    return render_template(
        'figuras_dia_visual.html',
        archivos_srs=archivos_srs,
        figuras_bingo=figuras_bingo,
        figuras_dia=figuras_dia,
        figura_imagen=figura_imagen
    )




@app.route('/guardar_configuracion_srs', methods=['POST'])
def guardar_configuracion_srs():
    data = request.get_json()
    archivo = data.get('archivo')
    desde = int(data.get('desde'))
    hasta = int(data.get('hasta'))
    if not archivo or desde < 1 or hasta < desde:
        return jsonify(success=False, error="Datos incorrectos")
    config = {
        "archivo": archivo,
        "desde": desde,
        "hasta": hasta
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return jsonify(success=True)








@app.route("/guardar_figura_dia", methods=["POST"])
def guardar_figura_dia():
    import shutil
    data = request.get_json()
    nombre = data.get('nombre')
    valor = data.get('valor')
    colores = data.get('colores')

    if not nombre or not valor or not colores:
        return jsonify({"success": False, "error": "Datos incompletos"})

    print("RUTA_FIGURAS_DIA:", RUTA_FIGURAS_DIA)

    # Cargar o crear XML
    if os.path.exists(RUTA_FIGURAS_DIA):
        try:
            tree = ET.parse(RUTA_FIGURAS_DIA)
            root = tree.getroot()
        except Exception as e:
            # Corrige si el archivo está vacío/corrupto
            root = ET.Element("figuras")
            tree = ET.ElementTree(root)
    else:
        root = ET.Element("figuras")
        tree = ET.ElementTree(root)

    # Evita duplicados
    for f in root.findall("figura"):
        if f.attrib.get("nombre") == nombre:
            return jsonify({"success": False, "error": "Figura ya está en el día"})

    figura_el = ET.SubElement(root, "figura", nombre=nombre, valor=valor, estado="normal")
    ET.SubElement(figura_el, "cuadro").text = ','.join(colores)

    # Guarda backup antes de escribir
    if os.path.exists(RUTA_FIGURAS_DIA):
        shutil.copy(RUTA_FIGURAS_DIA, RUTA_FIGURAS_DIA + ".bak")

    tree.write(RUTA_FIGURAS_DIA, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})


@app.route("/api/figuras_dia")
def api_figuras_dia():
    if not os.path.exists(RUTA_FIGURAS_DIA):
        return jsonify([])
    tree = ET.parse(RUTA_FIGURAS_DIA)
    root = tree.getroot()
    figuras = []
    for figura in root.findall("figura"):
        figuras.append({
            "nombre": figura.attrib.get("nombre"),
            "valor": figura.attrib.get("valor"),
            "estado": figura.attrib.get("estado"),
            "colores": figura.find("cuadro").text if figura.find("cuadro") is not None else ""
        })
    return jsonify(figuras)




@app.route("/eliminar_figura_dia", methods=["POST"])
def eliminar_figura_dia():
    nombre = request.get_json().get('nombre')
    

    if not os.path.exists(RUTA_FIGURAS_DIA):
        return jsonify({"success": False, "error": "No existe archivo de figuras del día"})

    try:
        tree = ET.parse(RUTA_FIGURAS_DIA)
        root = tree.getroot()
        eliminada = False
        for f in root.findall("figura"):
            if f.attrib.get("nombre") == nombre:
                root.remove(f)
                eliminada = True
                break
        if eliminada:
            tree.write(RUTA_FIGURAS_DIA, encoding="utf-8", xml_declaration=True)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Figura no encontrada"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



@app.route('/reset_figuras_dia', methods=['POST'])
def reset_figuras_dia():
    root = ET.Element("figuras")  # <--- ¡Así, NO <figuras_del_dia>!
    tree = ET.ElementTree(root)
    tree.write(RUTA_FIGURAS_DIA, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})


@app.route('/cambiar_estado_figura', methods=['POST'])
def cambiar_estado_figura():
    data = request.get_json()
    nombre = data.get('nombre')
    estado = data.get('estado')

    if not nombre or not estado:
        return jsonify({'success': False, 'error': 'Datos incompletos'})

    if not os.path.exists(RUTA_FIGURAS_DIA):
        return jsonify({'success': False, 'error': 'No existe el archivo de figuras del día'})

    tree = ET.parse(RUTA_FIGURAS_DIA)
    root = tree.getroot()
    encontrada = False

    for fig in root.findall("figura"):
        if fig.get("nombre") == nombre:
            fig.set("estado", estado)
            encontrada = True
            break

    if encontrada:
        tree.write(RUTA_FIGURAS_DIA, encoding="utf-8", xml_declaration=True)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Figura no encontrada'})


@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)





@app.route('/marcar_balota', methods=['POST'])
def marcar_balota():
    import xml.etree.ElementTree as ET
    import os
    from flask import request, jsonify

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    XML_PATH = os.path.join(DATA_DIR, "datos_bingo.xml")
    RUTA_FIGURAS_DIA = os.path.join(DATA_DIR, "figuras_del_dia.xml")
    CONFIG_FILE = os.path.join(DATA_DIR, "config_srs.json")

    try:
        numero = str(request.json.get('numero'))
        marcar_numero_bingo(numero)  # <-- AGREGA ESTA LÍNEA

        # ========== Marcar balota en datos_bingo.xml ==========
        if not os.path.exists(XML_PATH):
            return jsonify({"error": "No existe el archivo XML del bingo"}), 500
        tree = ET.parse(XML_PATH)
        root = tree.getroot()
        balotas = root.find('balotas')
        for balota in balotas.findall('balota'):
            if balota.get('numero') == numero:
                balota.set('estado', numero if balota.get('estado') != numero else '')
        # Actualizaciones estándar
        for balota in balotas.findall('balota'):
            balota.set('ultimo', '')
        for balota in balotas.findall('balota'):
            if balota.get('numero') == "1":
                balota.set('ultimo', numero)
        # Últimos 5 y totales
        ultimos5 = root.find('ultimos5')
        if ultimos5 is None:
            ultimos5 = ET.SubElement(root, 'ultimos5')
        ultimos = ultimos5.text.split(',') if ultimos5.text else []
        if numero in ultimos:
            ultimos.remove(numero)
        ultimos.insert(0, numero)
        ultimos = ultimos[:5]
        ultimos5.text = ','.join(ultimos)
        total = len([b for b in balotas.findall('balota') if b.get('estado')])
        totalMarcadas = root.find('totalMarcadas')
        if totalMarcadas is None:
            totalMarcadas = ET.SubElement(root, 'totalMarcadas')
        totalMarcadas.text = str(total)
        ultimoMarcado = root.find('ultimoMarcado')
        if ultimoMarcado is None:
            ultimoMarcado = ET.SubElement(root, 'ultimoMarcado')
        ultimoMarcado.text = numero
        tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
        balotas_marcadas = set(
            b.get('numero') for b in balotas.findall('balota') if b.get('estado')
        )

        # ========== Leer figuras del día ==========
        def leer_figuras_del_dia(path=RUTA_FIGURAS_DIA):
            figuras = []
            if not os.path.exists(path):
                return figuras
            tree_fig = ET.parse(path)
            root_fig = tree_fig.getroot()
            for f in root_fig.findall("figura"):
                nombre = f.attrib.get("nombre")
                valor = int(f.attrib.get("valor", 0))
                estado = f.attrib.get("estado")
                colores = f.find("cuadro").text.split(",")
                posiciones = [i for i, c in enumerate(colores) if c.strip().upper() == "#FF0000"]
                figuras.append({
                    "nombre": nombre,
                    "valor": valor,
                    "estado": estado,
                    "posiciones": posiciones
                })
            return figuras

        # ========== Leer el rango de boletos a jugar ==========
        import json
        if not os.path.exists(CONFIG_FILE):
            return jsonify({"success": True, "ganador": None})
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        archivo_boletos = os.path.join(DATA_DIR, config["archivo"])
        desde = int(config["desde"])
        hasta = int(config["hasta"])

        if not os.path.exists(archivo_boletos):
            return jsonify({"success": True, "ganador": None})
        tree_boletos = ET.parse(archivo_boletos)
        root_boletos = tree_boletos.getroot()
        boletos = root_boletos.findall("boleto")

        # ========== Buscar ganador ==========
        figuras_dia = leer_figuras_del_dia()
        ganador = None

        for idx, boleto in enumerate(boletos, start=1):
            if idx < desde or idx > hasta:
                continue
            id_boleto = boleto.get("codigo") or boleto.get("id") or str(idx)
            casillas = [casilla.text.strip() for casilla in boleto.findall("casilla")]
            for figura in figuras_dia:
                if not figura["posiciones"]:
                    continue
                numeros_figura = [casillas[i] for i in figura["posiciones"] if i < len(casillas)]
                if all(num in balotas_marcadas for num in numeros_figura):
                    ganador = {
                        "boleto": id_boleto,
                        "figura": figura["nombre"],
                        "valor": figura["valor"],
                        "casillas_boleto": casillas,
                        "posiciones_figura": figura["posiciones"],
                        "numeros": numeros_figura,
                        "ultimo_numero": numero
                    }
                    break
            if ganador:
                break

        return jsonify({
            "success": True,
            "ganador": ganador,
            "balotas_marcadas": list(balotas_marcadas)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500








def leer_figura_pattern_color(ruta_figura_xml):
    """
    Lee la figura activa (formato XML de tu sistema) y devuelve una lista de posiciones (índices 0 a 24)
    donde el color sea '#FF0000' (activo). ¡Así no te dará errores de índice!
    """
    import xml.etree.ElementTree as ET
    tree = ET.parse(ruta_figura_xml)
    root = tree.getroot()
    figura = root.find('figura')
    if figura is None:
        return []
    cuadro = figura.find('cuadro')
    if cuadro is None or not cuadro.text:
        return []
    colores = [c.strip().upper() for c in cuadro.text.split(",")]
    # Devuelve índices de las casillas activas en la figura (por color rojo)
    return [i for i, color in enumerate(colores) if color == "#FF0000"]

def cargar_cartones_csv(ruta_csv):
    """
    Lee el CSV real de cartones y devuelve lista de diccionarios con todos los números en orden BINGO (25).
    """
    df = pd.read_csv(ruta_csv, dtype=str)
    df.columns = [col.lower().strip() for col in df.columns]
    cartones = []
    for idx, row in df.iterrows():
        numeros = []
        for pref in ['b', 'i', 'n', 'g', 'o']:
            for i in range(1, 6):
                key = f'{pref}{i}'
                val = row.get(key)
                if pd.isna(val) or val == '' or val is None:
                    numeros.append(None)
                else:
                    numeros.append(int(val))
        carton = {
            'numero': row.get('numero', idx+1),
            'numeros': numeros
        }
        cartones.append(carton)
    return cartones

def es_carton_ganador_color(carton, balotas_marcadas, posiciones_figura):
    """
    Devuelve True si el cartón es ganador para la figura (por posiciones activas y números marcados).
    Anula la casilla central N3 (índice 12).
    """
    for idx in posiciones_figura:
        if idx == 12:  # Ignora centro
            continue
        num = carton['numeros'][idx]
        if num is None or int(num) not in balotas_marcadas:
            return False
    return True

def buscar_ganador_csv_color(ruta_csv, ruta_figura_xml, balotas_marcadas):
    posiciones_figura = leer_figura_pattern_color(ruta_figura_xml)
    cartones = cargar_cartones_csv(ruta_csv)
    for carton in cartones:
        if es_carton_ganador_color(carton, balotas_marcadas, posiciones_figura):
            return carton
    return None

# ENDPOINT para mostrar el ganador en tu panel
@app.route('/verificar_ganador')
def verificar_ganador():
    with open('data/numeros_marcados.txt') as f:
        balotas = [int(x) for x in f.read().strip().split(',') if x.strip().isdigit()]
    ruta_csv = 'data/Srs_ib1.csv'  # o el archivo que esté activo (ajusta si el usuario elige otro)
    ruta_figura = 'data/figuras_del_dia.xml'
    ganador = buscar_ganador_csv_color(ruta_csv, ruta_figura, balotas)
    if ganador:
        return render_template('mostrar_ganador.html', carton=ganador)
    else:
        return "No hay ganador aún."






















@app.route('/reset_juego', methods=['POST'])
def reset_juego():
    try:
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        for balota in root.find('balotas').findall('balota'):
            balota.set('estado', '')
            balota.set('ultimo', '')

        ultimos5 = root.find('ultimos5')
        if ultimos5 is not None:
            ultimos5.text = ''

        totalMarcadas = root.find('totalMarcadas')
        if totalMarcadas is not None:
            totalMarcadas.text = '0'

        ultimoMarcado = root.find('ultimoMarcado')
        if ultimoMarcado is not None:
            ultimoMarcado.text = ''

        tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
        return jsonify({"success": True})
    except Exception as e:
        print("\U0001f4a5 ERROR RESET:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/activar_stinger', methods=['POST'])
def activar_stinger():
    try:
        numero = str(request.json.get('numero'))
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        stinger = root.find('stinger')
        if stinger is None:
            stinger = ET.SubElement(root, 'stinger')

        stinger.text = numero

        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
        return jsonify({"success": True})
    except Exception as e:
        print("\U0001f4a5 ERROR STINGER:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/crear_figura')
def crear_figura():
    return render_template('crear_figura.html')

@app.route('/guardar_figura', methods=['POST'])
def guardar_figura():
    data = request.get_json()
    nombre = data.get('nombre')
    matriz = data.get('matriz')

    if not nombre or not matriz:
        return {'error': 'Datos incompletos'}, 400

    xml_path = os.path.join("data", "figuras_creadas.xml")

    if not os.path.exists(xml_path):
        root = ET.Element("figuras")
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    figura_el = ET.SubElement(root, "figura", nombre=nombre)
    for i, fila in enumerate(matriz):
        ET.SubElement(figura_el, "cuadro", fila=str(i+1)).text = ",".join(fila)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    return {"success": True}

# ==== Dashboard y otras funciones protegidas por clave ====

@app.route('/dashboard')
def dashboard():
    if not requiere_clave("dashboard"):
        return redirect(url_for('pedir_clave', seccion="dashboard"))

    # Datos de ejemplo para que el dashboard siempre abra
    total_recaudado = "0.00"
    boletos_vendidos = "0"
    boletos_devueltos = "0"
    efectivo_caja = "0.00"
    gastos_mes = "0.00"
    ganancia_vendedor = "0.00"
    ganancia_empresa = "0.00"

    return render_template(
        'index.html',
        total_recaudado=total_recaudado,
        boletos_vendidos=boletos_vendidos,
        boletos_devueltos=boletos_devueltos,
        efectivo_caja=efectivo_caja,
        gastos_mes=gastos_mes,
        ganancia_vendedor=ganancia_vendedor,
        ganancia_empresa=ganancia_empresa
    )



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REINTEGROS_DIR = os.path.join(DATA_DIR, "REINTEGROS")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# -- Configuración visual
MARGEN_IZQ   = 20
MARGEN_SUP   = 45
ESPACIO_X    = 36
ESPACIO_Y    = 46
COLUMNAS     = 2
FILAS        = 4
SIZE_NUM     = 21
SIZE_INFO    = 12
SIZE_VALOR   = 15
REINTEGRO_W  = 60
REINTEGRO_H  = 60

# --- Agrega este bloque al inicio de tu archivo, cerca de tus otras constantes ---
SERIE_MAP = {
    "Srs_ib1.xlsx": "V",
    "Srs_ib2.xlsx": "+",
    "Srs_ib3.xlsx": "&",
    "Srs_Manila.xlsx": "M"
}

@app.route('/impresion', methods=['GET', 'POST'])
def impresion():
    series = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(('.xlsx', '.csv'))]
    reintegros = [f for f in os.listdir(REINTEGROS_DIR) if f.lower().endswith('.png')]
    fecha_hoy = date.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == "boletos":
            nombre = request.form['serie_archivo']
            start = request.form.get('serie_inicio', '')
            end = request.form.get('serie_fin', '')
            valor = request.form['valor']
            telefono = request.form['telefono']
            fecha_sorteo = request.form.get('fecha_sorteo', fecha_hoy)
            reintegro_especial = request.form.get('reintegro_especial', '')
            cant_reintegro_especial = int(request.form.get('cant_reintegro_especial', 0))
            incluir_aleatorio = request.form.get('incluir_aleatorio', '1') == '1'

            path = os.path.join(DATA_DIR, nombre)
            print(f"Intentando cargar archivo: {path}")
            if not os.path.exists(path):
                return render_template("error.html", mensaje=f"Archivo no encontrado en {path}")

            try:
                df = pd.read_excel(path, dtype=str).fillna('')
                if df.empty:
                    raise ValueError("Archivo cargado vacío.")
            except Exception as e:
                return render_template("error.html", mensaje=f"Error al cargar Excel: {e}")

            ids = df[df.columns[0]].astype(str).tolist()

            if start and start in ids:
                ids = ids[ids.index(start):]
            if end and end in ids:
                ids = ids[:ids.index(end) + 1]

            boletos = df[df[df.columns[0]].astype(str).isin(ids)]

            pdf_buf = generar_pdf_boletos_excel(
                ids, boletos, valor, telefono, nombre, reintegro_especial,
                cant_reintegro_especial, reintegros, incluir_aleatorio, fecha_sorteo
            )

            return send_file(pdf_buf, download_name='boletos_bingo.pdf', as_attachment=True)

        elif form_type == "planilla":
            archivo = request.form['serie_archivo_planilla']
            inicio = int(request.form['planilla_inicio'])
            fin = int(request.form['planilla_fin'])
            nombre_vendedor = request.form['nombre_vendedor']
            fecha_planilla = request.form['fecha_planilla']
            path = os.path.join(DATA_DIR, archivo)
            if archivo.lower().endswith('.csv'):
                df = pd.read_csv(path, dtype=str).fillna('')
            else:
                df = pd.read_excel(path, dtype=str).fillna('')

            ids = df[df.columns[0]].astype(str).tolist()
            ids = ids[inicio-1:fin]
            BOLETOS_X_PLANILLA = 40
            total = len(ids)
            merger = PdfMerger()
            for i in range(0, total, BOLETOS_X_PLANILLA):
                bloque_ids = ids[i:i+BOLETOS_X_PLANILLA]
                bloque_inicio = inicio + i
                bloque_fin = min(bloque_inicio + BOLETOS_X_PLANILLA - 1, fin)
                num_planilla = (i // BOLETOS_X_PLANILLA) + 1  # <-- NÚMERO DE PLANILLA
                planilla_buf = generar_pdf_planilla(
                    bloque_ids, archivo, nombre_vendedor, fecha_planilla, bloque_inicio, bloque_fin, SERIE_MAP, num_planilla
                )
                merger.append(planilla_buf)
            output_buffer = BytesIO()
            merger.write(output_buffer)
            output_buffer.seek(0)
            return send_file(output_buffer, download_name='planilla_vendedor.pdf', as_attachment=True)

    return render_template(
        'impresion_boletos_excel.html',
        series=series, reintegros=reintegros, fecha_hoy=fecha_hoy
    )





def generar_pdf_boletos_excel(
    ids, boletos, valor, telefono, nombre,
    reintegro_especial, cant_especial, reintegros, incluir_aleatorio, fecha_sorteo
):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4
    ancho_boleto = (ancho - 2 * MARGEN_IZQ - ESPACIO_X) / COLUMNAS
    alto_boleto = (alto - 2 * MARGEN_SUP - ESPACIO_Y * (FILAS - 1)) / FILAS
    size_celda = min(ancho_boleto, alto_boleto) / 5.2

    # -- Calcular reintegros
    N = len(boletos)
    indices_especial = random.sample(range(N), min(N, cant_especial)) if (reintegro_especial and reintegro_especial != '') else []
    indices_aleatorio = []
    if incluir_aleatorio:
        disponibles = [i for i in range(N) if i not in indices_especial]
        indices_aleatorio = disponibles

    if hasattr(boletos, 'to_dict'):
        boletos = boletos.to_dict(orient='records')

    for idx in range(0, N, FILAS * COLUMNAS):
        page_boletos = boletos[idx:idx + FILAS * COLUMNAS]
        for i, row in enumerate(page_boletos):
            pos_global = idx + i
            col = i % COLUMNAS
            fila = i // COLUMNAS
            x = MARGEN_IZQ + col * (ancho_boleto + ESPACIO_X)
            y = alto - MARGEN_SUP - fila * (alto_boleto + ESPACIO_Y)

            # --- TABLA Y NÚMEROS ---
            c.setLineWidth(1.6)
            for f in range(5):
                for j, letra in enumerate('bingo'):
                    cx = x + j * size_celda
                    cy = y - f * size_celda
                    c.setFont('Helvetica-Bold', SIZE_NUM)
                    valor_celda = str(row.get(f"{letra}{f+1}", "-"))
                    if letra == 'n' and f == 2:
                        # === QR GRANDE Y FORMATO LIMPIO ===
                        serie_letra = SERIE_MAP.get(nombre, nombre)[0]  # Solo la letra/serie (V, +, &, M...)
                        qr_data = (
                            f"SORTEO{fecha_sorteo.replace('-','')}B{ids[pos_global]}{serie_letra}"
                        )
                        qr_img = qrcode.make(qr_data)
                        qr_buffer = BytesIO()
                        qr_img.save(qr_buffer, format='PNG')
                        qr_buffer.seek(0)
                        # TAMAÑO QR GRANDE
                        size_qr = size_celda * 1.3  # ¡Hazlo bien grande!
                        offset = (size_qr - size_celda) / 2
                        c.drawImage(
                            ImageReader(qr_buffer),
                            cx - offset, cy - offset,
                            size_qr, size_qr
                        )
                    else:
                        c.setFillColorRGB(0, 0, 0)
                        c.drawCentredString(cx + size_celda/2, cy + size_celda*0.28, valor_celda)
            # --- INFORMACIÓN ---
            serie_letra = SERIE_MAP.get(nombre, nombre)[0]
            serie_texto = f"{ids[pos_global]}{serie_letra} | {fecha_sorteo}"
            valor_texto = f": ${valor}"
            tel_texto = f"Tel: {telefono}"
            info_y = y - size_celda*5.17

            c.setFont('Helvetica-Bold', SIZE_INFO)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x, info_y, serie_texto)
            c.setFont('Helvetica-Bold', SIZE_VALOR)
            c.drawCentredString(x + ancho_boleto/2, info_y, valor_texto)
            c.setFont('Helvetica-Bold', SIZE_INFO)
            c.drawRightString(x + ancho_boleto, info_y, tel_texto)

            # --- REINTEGRO ---
            if pos_global in indices_especial and reintegro_especial and reintegro_especial != "":
                ruta_reintegro = os.path.join(REINTEGROS_DIR, reintegro_especial)
                if os.path.exists(ruta_reintegro):
                    img = ImageReader(ruta_reintegro)
                    img_x = x + ancho_boleto - REINTEGRO_W - 10
                    img_y = y - size_celda*2.2
                    c.drawImage(img, img_x, img_y, width=REINTEGRO_W, height=REINTEGRO_H, mask='auto')
            elif pos_global in indices_aleatorio and len(reintegros) > 0:
                otros = [r for r in reintegros if r != reintegro_especial]
                if otros:
                    elegido = random.choice(otros)
                    ruta_aleatorio = os.path.join(REINTEGROS_DIR, elegido)
                    if os.path.exists(ruta_aleatorio):
                        img = ImageReader(ruta_aleatorio)
                        img_x = x + ancho_boleto - REINTEGRO_W - 10
                        img_y = y - size_celda*2.2
                        c.drawImage(img, img_x, img_y, width=REINTEGRO_W, height=REINTEGRO_H, mask='auto')
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer






# AGREGA ESTA FUNCIÓN AL FINAL DE TU ARCHIVO (antes del if __name__ == '__main__':)
def generar_pdf_planilla(ids, serie_archivo, vendedor, fecha, inicio, fin, serie_map, num_planilla):
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import ImageReader
    import os
    import qrcode

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    ancho, alto = landscape(A4)

    LOGO_PATH = os.path.join("static", "golpe_suerte_logo.png")
    font_bold = 'Helvetica-Bold'
    font_reg = 'Helvetica'

    # Configuración de márgenes y separaciones
    margen_izq = 40
    margen_sup = 100
    espacio_x_col = 400    # separación horizontal entre columnas
    espacio_y = 23         # separación vertical entre líneas

    # Posiciones QR
    x_qr_left = ancho // 4 + 150
    y_qr_left = alto - 90
    x_qr_right = ancho * 2 // 2 - 80
    y_qr_right = alto - 90
    x_central_qr = ancho // 2 - 35
    y_central_qr = 65

    # --- Logo ---
    c.drawImage(LOGO_PATH, 40, alto - 60, width=100, height=50, mask='auto')

    # --- Vendedor y Fecha centrados ---
    c.setFont(font_bold, 15)
    c.drawString(ancho//2 - 275, alto - 50, f"VENDEDOR: {vendedor}")
    c.setFont(font_bold, 12)
    c.drawString(ancho//2 - 275, alto - 70, f"FECHA:    {fecha}")

    # --- NÚMERO GRANDE de la planilla ---
    c.setFont(font_bold, 42)
    c.drawString(18, alto - 70, str(num_planilla))  # <-- Número de la planilla

    # ======== QRs SOLO LETRAS Y NÚMEROS (Separador "A") ========
    serie_letra = serie_map.get(serie_archivo, "")
    fecha_limpia = fecha.replace("-", "")  # Ej: 2025-06-13 -> 20250613

    # Función para generar el string QR sin símbolos
    def qr_string(tipo, desde, hasta, serie):
        return f"SORTEO{fecha_limpia}{tipo}A{desde}A{hasta}{serie}"

    # QR central (rango completo)
    qr_text_central = qr_string("RG", inicio, fin, serie_letra)
    qr_central = qrcode.make(qr_text_central)
    qr_central_buf = BytesIO()
    qr_central.save(qr_central_buf, format='PNG')
    qr_central_buf.seek(0)
    c.drawImage(ImageReader(qr_central_buf), x_central_qr, y_central_qr, 52, 52)

    # QR arriba izquierdo (LADO1, boletos 1-20)
    lado1_ini = inicio
    lado1_fin = min(inicio + 19, fin)
    qr_text_lado1 = qr_string("L1", lado1_ini, lado1_fin, serie_letra)
    qr1 = qrcode.make(qr_text_lado1)
    qr_buf1 = BytesIO()
    qr1.save(qr_buf1, format='PNG')
    qr_buf1.seek(0)
    c.drawImage(ImageReader(qr_buf1), x_qr_left, y_qr_left, 52, 52)

    # QR arriba derecho (LADO2, boletos 21-40)
    lado2_ini = min(inicio + 20, fin)
    lado2_fin = min(inicio + 39, fin)
    qr_text_lado2 = qr_string("L2", lado2_ini, lado2_fin, serie_letra)
    qr2 = qrcode.make(qr_text_lado2)
    qr_buf2 = BytesIO()
    qr2.save(qr_buf2, format='PNG')
    qr_buf2.seek(0)
    c.drawImage(ImageReader(qr_buf2), x_qr_right, y_qr_right, 52, 52)

    # --- Líneas y numeración global ---
    c.setFont(font_bold, 17)
    for i in range(20):
        y = alto - margen_sup - i * espacio_y

        # Izquierda (líneas 1-20 de la planilla)
        num_izq = inicio + i
        if num_izq <= fin:
            c.drawString(margen_izq, y, str(num_izq))
            c.line(margen_izq+38, y+5, margen_izq+338, y+5)

        # Derecha (líneas 21-40 de la planilla)
        num_der = inicio + i + 20
        if num_der <= fin:
            c.drawString(margen_izq+espacio_x_col, y, str(num_der))
            c.line(margen_izq+espacio_x_col+38, y+5, margen_izq+espacio_x_col+338, y+5)

    c.save()
    buffer.seek(0)
    return buffer







DATA_DIR = "data"
ASIGNACIONES_DIR = "asignaciones"
COBROS_DIR = "cobros"
VENDEDORES_XML = os.path.join(DATA_DIR, "vendedores.xml")

# 1. UTILIDAD: CARGAR VENDEDORES DESDE /data/vendedores.xml
def cargar_vendedores():
    if not os.path.exists(VENDEDORES_XML):
        return []
    tree = ET.parse(VENDEDORES_XML)
    root = tree.getroot()
    vendedores = []
    for vend in root.findall("vendedor"):
        vendedores.append({
            "id": vend.get("id"),
            "nombre": vend.get("nombre"),
            "alias": vend.get("alias")
        })
    return vendedores

# 2. GUARDAR VENDEDORES NUEVOS O EDITADOS
def guardar_vendedores(lista_vendedores):
    root = ET.Element("vendedores")
    for vend in lista_vendedores:
        ET.SubElement(root, "vendedor", id=str(vend["id"]), nombre=vend["nombre"], alias=vend["alias"])
    tree = ET.ElementTree(root)
    tree.write(VENDEDORES_XML, encoding="utf-8", xml_declaration=True)

# 3. PANEL PARA ASIGNAR PLANILLAS

@app.route('/asignar_planillas')
def asignar_planillas():
    vendedores = cargar_vendedores()
    fecha_hoy = date.today().isoformat()  # Ejemplo: '2025-06-03'
    return render_template('asignar_planillas.html', vendedores=vendedores, fecha_hoy=fecha_hoy)


# 4. API PARA AGREGAR PLANILLAS A UN VENDEDOR (NO SOBREESCRIBE, SOLO AGREGA)
@app.route('/api/agregar_planillas', methods=['POST'])
def api_agregar_planillas():
    data = request.get_json()
    fecha = data.get('fecha')
    nombre = data.get('nombre')
    alias = data.get('alias')
    planillas = data.get('planillas', [])

    if not fecha or not nombre or not alias or not planillas:
        return jsonify({"success": False, "error": "Datos incompletos"}), 400

    os.makedirs(ASIGNACIONES_DIR, exist_ok=True)
    xml_path = os.path.join(ASIGNACIONES_DIR, f"{fecha}.xml")
    # Si existe, actualiza; si no, crea nuevo
    if os.path.exists(xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
    else:
        root = ET.Element("asignaciones", fecha=fecha)
        tree = ET.ElementTree(root)

    # Buscar vendedor en XML
    vendedor_xml = None
    for v in root.findall("vendedor"):
        if v.get("nombre") == nombre:
            vendedor_xml = v
            break
    if vendedor_xml is None:
        vendedor_xml = ET.SubElement(root, "vendedor", nombre=nombre, alias=alias)

    # No duplicar planillas
    planillas_existentes = set([p.get("codigo") for p in vendedor_xml.findall("planilla")])
    for codigo in planillas:
        if codigo not in planillas_existentes:
            ET.SubElement(vendedor_xml, "planilla", codigo=codigo)
            planillas_existentes.add(codigo)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

# 5. SERVIR ASIGNACIÓN POR FECHA
@app.route('/asignaciones/<fecha>.xml')
def servir_asignacion_xml(fecha):
    archivo = f"{fecha}.xml"
    return send_from_directory(ASIGNACIONES_DIR, archivo)

    

# 6. API PARA CARGAR ASIGNACIONES DESDE XML (devuelve para la fecha las planillas por vendedor)
@app.route('/api/asignaciones_fecha')
def api_asignaciones_fecha():
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify([])
    xml_path = os.path.join(ASIGNACIONES_DIR, f"{fecha}.xml")
    if not os.path.exists(xml_path):
        return jsonify([])
    tree = ET.parse(xml_path)
    root = tree.getroot()
    resultado = []
    for v in root.findall("vendedor"):
        nombre = v.get("nombre")
        alias = v.get("alias", "")
        planillas = [p.get("codigo") for p in v.findall("planilla")]
        resultado.append({
            "nombre": nombre,
            "alias": alias,
            "planillas": planillas,
        })
    return jsonify(resultado)

# 7. CRUD BÁSICO DE VENDEDORES
@app.route('/vendedores', methods=['GET'])
def panel_vendedores():
    vendedores = cargar_vendedores()
    return render_template("panel_vendedores.html", vendedores=vendedores)

@app.route('/api/vendedores', methods=['POST'])
def api_agregar_vendedor():
    data = request.get_json()
    nombre = data.get("nombre", "").strip()
    alias = data.get("alias", "").strip()
    if not nombre or not alias:
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    vendedores = cargar_vendedores()
    new_id = max([int(v["id"]) for v in vendedores], default=0) + 1
    vendedores.append({"id": new_id, "nombre": nombre, "alias": alias})
    guardar_vendedores(vendedores)
    return jsonify({"success": True})

@app.route('/api/vendedores/<int:id>', methods=['PUT'])
def api_editar_vendedor(id):
    data = request.get_json()
    nombre = data.get("nombre", "").strip()
    alias = data.get("alias", "").strip()
    vendedores = cargar_vendedores()
    actualizado = False
    for v in vendedores:
        if int(v["id"]) == id:
            v["nombre"] = nombre
            v["alias"] = alias
            actualizado = True
    if actualizado:
        guardar_vendedores(vendedores)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No encontrado"}), 404

@app.route('/api/vendedores/<int:id>', methods=['DELETE'])
def api_eliminar_vendedor(id):
    vendedores = cargar_vendedores()
    vendedores = [v for v in vendedores if int(v["id"]) != id]
    guardar_vendedores(vendedores)
    return jsonify({"success": True})

@app.route('/api/agregar_planillas_masivo', methods=['POST'])
def agregar_planillas_masivo():
    data = request.json
    vendedor = data["vendedor"]
    fecha = data["fecha"]
    codigos = [c.strip() for c in data["codigos"] if c.strip()]
    # Lógica para obtener todas las planillas ya asignadas
    todas_asignadas = get_all_planillas_asignadas()  # <--- deberías implementarla
    planillas_vendedor = get_planillas_de_vendedor(vendedor, fecha)  # <--- deberías implementarla

    asignadas = []
    repetidas = []
    for cod in codigos:
        if cod in todas_asignadas:
            repetidas.append(cod)
        else:
            asignadas.append(cod)
            # Lógica para guardar la planilla (agregaPlanillaVendedor...)
            agregaPlanillaVendedor(vendedor, fecha, cod)
    # Actualiza el XML, CSV o BD según tu sistema

    return jsonify({
        "asignadas": asignadas,
        "repetidas": repetidas
    })


# 8. DASHBOARD CONTABILIDAD
def cargar_asignacion_planillas(fecha):
    xml_path = os.path.join(ASIGNACIONES_DIR, f"{fecha}.xml")
    if not os.path.exists(xml_path):
        return []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    resultado = []
    for v in root.findall("vendedor"):
        nombre = v.get("nombre")
        alias = v.get("alias", "")
        planillas = [p.get("codigo") for p in v.findall("planilla")]
        resultado.append({
            "nombre": nombre,
            "alias": alias,
            "planillas": planillas,
        })
    return resultado

@app.route('/dashboard_contabilidad')
def dashboard_contabilidad():
    fecha_hoy = date.today().isoformat()
    vendedores = cargar_asignacion_planillas(fecha_hoy)
    return render_template('dashboard_contabilidad.html', vendedores=vendedores, fecha_hoy=fecha_hoy)

# 9. DESASIGNAR PLANILLA DE UN VENDEDOR (ELIMINAR PLANILLA)
@app.route('/api/desasignar_planilla', methods=['POST'])
def api_desasignar_planilla():
    data = request.get_json()
    fecha = data.get('fecha')
    nombre = data.get('nombre')
    planilla = data.get('planilla')

    if not fecha or not nombre or not planilla:
        return jsonify({"success": False, "error": "Datos incompletos"}), 400

    xml_path = os.path.join(ASIGNACIONES_DIR, f"{fecha}.xml")
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": "No existe el archivo de asignaciones"}), 404

    tree = ET.parse(xml_path)
    root = tree.getroot()
    encontrado = False

    for v in root.findall("vendedor"):
        if v.get("nombre") == nombre:
            for p in v.findall("planilla"):
                if p.get("codigo") == planilla:
                    v.remove(p)
                    encontrado = True
                    break

    if not encontrado:
        return jsonify({"success": False, "error": "Planilla no encontrada"}), 404

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})



import os
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify

COBROS_DIR = "cobros"
os.makedirs(COBROS_DIR, exist_ok=True)

COBROS_DIR = "cobros"
os.makedirs(COBROS_DIR, exist_ok=True)

# Guardar cobros del día
@app.route("/api/guardar_cobro", methods=["POST"])
def api_guardar_cobro():
    data = request.json
    fecha = data["fecha"]
    nombre = data["nombre"]
    boletosDevueltosLista = data["boletosDevueltosLista"]
    archivo = os.path.join(COBROS_DIR, f"{fecha}.xml")
    if os.path.exists(archivo):
        tree = ET.parse(archivo)
        root = tree.getroot()
    else:
        root = ET.Element("cobros", fecha=fecha)
        tree = ET.ElementTree(root)
    v = None
    for vend in root.findall("vendedor"):
        if vend.get("nombre") == nombre:
            v = vend
            break
    if v is None:
        v = ET.SubElement(root, "vendedor", nombre=nombre, planillas="1")
    v.set("estado", "Pagado")
    # borra boletos anteriores
    for b in v.findall("boleto"):
        v.remove(b)
    for cod in boletosDevueltosLista:
        ET.SubElement(v, "boleto").text = cod
    tree.write(archivo, encoding="utf-8", xml_declaration=True)
    return jsonify({"ok": True})
# Leer cobros del día
@app.route("/api/cobros_fecha")
def api_cobros_fecha():
    fecha = request.args.get("fecha")
    archivo = os.path.join(COBROS_DIR, f"{fecha}.xml")
    vendedores = []
    if os.path.exists(archivo):
        tree = ET.parse(archivo)
        root = tree.getroot()
        for v in root.findall("vendedor"):
            vendedores.append({
                "nombre": v.get("nombre"),
                "planillas": int(v.get("planillas", "1")),
                "boletosDevueltosLista": [b.text for b in v.findall("boleto")],
                "estado": v.get("estado", "Pendiente")
            })
    else:
        # aquí deberías cargar los vendedores asignados desde planillas si no existe el cobro
        pass
    return jsonify(vendedores)

@app.route('/api/planillas_vendedor')
def api_planillas_vendedor():
    fecha = request.args.get("fecha")
    nombre = request.args.get("nombre")
    xml_path = os.path.join("data", "asignaciones", f"{fecha}.xml")
    if not (fecha and nombre and os.path.exists(xml_path)):
        return jsonify([])
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for v in root.findall("vendedor"):
        if v.get("nombre") == nombre:
            planillas = [p.get("codigo") for p in v.findall("planilla")]
            return jsonify(planillas)
    return jsonify([])

@app.route("/api/eliminar_cobro", methods=["POST"])
def api_eliminar_cobro():
    data = request.json
    fecha = data["fecha"]
    nombre = data["nombre"]
    archivo = os.path.join(COBROS_DIR, f"{fecha}.xml")
    if os.path.exists(archivo):
        tree = ET.parse(archivo)
        root = tree.getroot()
        for v in root.findall("vendedor"):
            if v.get("nombre") == nombre:
                v.set("estado", "Pendiente")
                for b in v.findall("boleto"):
                    v.remove(b)
    tree.write(archivo, encoding="utf-8", xml_declaration=True)
    return jsonify({"ok": True})

    
from flask import Blueprint, render_template, request, redirect, url_for, flash


# === RUTAS DE ARCHIVOS Y CARPETAS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'static', 'data')
FACTURAS_DIR = os.path.join(BASE_DIR, 'static', 'facturas')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FACTURAS_DIR, exist_ok=True)

BONIFICACIONES_XML = os.path.join(DATA_DIR, 'bonificaciones.xml')
GASTOS_XML = os.path.join(DATA_DIR, 'gastos.xml')
EMPLEADOS_XML = os.path.join(DATA_DIR, 'empleados.xml')
VENTAS_XML = os.path.join(DATA_DIR, 'ventas.xml')  # Simulación archivo ventas

# === FUNCIONES DE BONIFICACIONES ===
def leer_bonificaciones():
    if not os.path.exists(BONIFICACIONES_XML):
        root = ET.Element('bonificaciones')
        ET.ElementTree(root).write(BONIFICACIONES_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(BONIFICACIONES_XML)
    root = tree.getroot()
    bonificaciones = []
    for b in root.findall('bonificacion'):
        bonificaciones.append({
            'fecha': b.get('fecha'),
            'vendedor': b.get('vendedor'),
            'motivo': b.get('motivo'),
            'monto': float(b.get('monto', '0')),
            'observacion': b.get('observacion', '')
        })
    return bonificaciones

def guardar_bonificacion(fecha, vendedor, motivo, monto, observacion):
    if not os.path.exists(BONIFICACIONES_XML):
        root = ET.Element('bonificaciones')
        ET.ElementTree(root).write(BONIFICACIONES_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(BONIFICACIONES_XML)
    root = tree.getroot()
    nueva = ET.SubElement(root, 'bonificacion')
    nueva.set('fecha', fecha)
    nueva.set('vendedor', vendedor)
    nueva.set('motivo', motivo)
    nueva.set('monto', str(monto))
    nueva.set('observacion', observacion)
    tree.write(BONIFICACIONES_XML, encoding='utf-8', xml_declaration=True)

@app.route('/bonificaciones', methods=['GET', 'POST'])
def panel_bonificaciones():
    if request.method == 'POST':
        fecha = request.form.get('fecha', date.today().isoformat())
        vendedor = request.form['vendedor']
        motivo = request.form['motivo']
        monto = request.form['monto']
        observacion = request.form.get('observacion', '')
        guardar_bonificacion(fecha, vendedor, motivo, monto, observacion)
        flash('Bonificación registrada exitosamente.', 'success')
        return redirect(url_for('panel_bonificaciones'))
    bonificaciones = leer_bonificaciones()
    return render_template('bonificaciones_panel.html', bonificaciones=bonificaciones)

# === FUNCIONES DE GASTOS ===
def leer_gastos():
    if not os.path.exists(GASTOS_XML):
        root = ET.Element('gastos')
        ET.ElementTree(root).write(GASTOS_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(GASTOS_XML)
    root = tree.getroot()
    gastos = []
    for g in root.findall('gasto'):
        gastos.append({
            'fecha': g.get('fecha'),
            'concepto': g.get('concepto'),
            'monto': float(g.get('monto', '0')),
            'factura': g.get('factura', ''),
            'observacion': g.get('observacion', '')
        })
    return gastos

def guardar_gasto(fecha, concepto, monto, factura, observacion):
    if not os.path.exists(GASTOS_XML):
        root = ET.Element('gastos')
        ET.ElementTree(root).write(GASTOS_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(GASTOS_XML)
    root = tree.getroot()
    nuevo = ET.SubElement(root, 'gasto')
    nuevo.set('fecha', fecha)
    nuevo.set('concepto', concepto)
    nuevo.set('monto', str(monto))
    nuevo.set('factura', factura)
    nuevo.set('observacion', observacion)
    tree.write(GASTOS_XML, encoding='utf-8', xml_declaration=True)

@app.route('/gastos', methods=['GET', 'POST'])
def panel_gastos():
    if request.method == 'POST':
        fecha = request.form.get('fecha', date.today().isoformat())
        concepto = request.form['concepto']
        monto = request.form['monto']
        observacion = request.form.get('observacion', '')
        factura_file = request.files.get('factura')
        nombre_factura = ""
        if factura_file and factura_file.filename:
            nombre_factura = secure_filename(factura_file.filename)
            factura_file.save(os.path.join(FACTURAS_DIR, nombre_factura))
        guardar_gasto(fecha, concepto, monto, nombre_factura, observacion)
        flash('Gasto registrado exitosamente.', 'success')
        return redirect(url_for('panel_gastos'))
    gastos = leer_gastos()
    return render_template('gastos_panel.html', gastos=gastos)

# === FUNCIONES DE EMPLEADOS/SUELDOS ===
def leer_empleados():
    if not os.path.exists(EMPLEADOS_XML):
        root = ET.Element('empleados')
        ET.ElementTree(root).write(EMPLEADOS_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(EMPLEADOS_XML)
    root = tree.getroot()
    empleados = []
    for e in root.findall('empleado'):
        empleados.append({
            'nombre': e.get('nombre'),
            'sueldo': float(e.get('sueldo', '0')),
            'pagos': e.get('pagos', '')  # lista separada por coma
        })
    return empleados

def guardar_empleado(nombre, sueldo):
    if not os.path.exists(EMPLEADOS_XML):
        root = ET.Element('empleados')
        ET.ElementTree(root).write(EMPLEADOS_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(EMPLEADOS_XML)
    root = tree.getroot()
    nuevo = ET.SubElement(root, 'empleado')
    nuevo.set('nombre', nombre)
    nuevo.set('sueldo', str(sueldo))
    nuevo.set('pagos', '')
    tree.write(EMPLEADOS_XML, encoding='utf-8', xml_declaration=True)

def registrar_pago_empleado(nombre, fecha_pago):
    tree = ET.parse(EMPLEADOS_XML)
    root = tree.getroot()
    for e in root.findall('empleado'):
        if e.get('nombre') == nombre:
            pagos = e.get('pagos', '')
            lista = pagos.split(',') if pagos else []
            lista.append(fecha_pago)
            e.set('pagos', ','.join(lista))
    tree.write(EMPLEADOS_XML, encoding='utf-8', xml_declaration=True)

@app.route('/empleados', methods=['GET', 'POST'])
def panel_empleados():
    if request.method == 'POST':
        nombre = request.form['nombre']
        sueldo = request.form['sueldo']
        guardar_empleado(nombre, sueldo)
        flash('Empleado agregado exitosamente.', 'success')
        return redirect(url_for('panel_empleados'))
    empleados = leer_empleados()
    return render_template('empleados_panel.html', empleados=empleados)

@app.route('/empleados/pagar', methods=['POST'])
def pagar_empleado():
    nombre = request.form['nombre']
    fecha_pago = request.form.get('fecha_pago', date.today().isoformat())
    registrar_pago_empleado(nombre, fecha_pago)
    flash('Pago registrado.', 'success')
    return redirect(url_for('panel_empleados'))

# === FUNCIONES DE VENTAS (SIMULADAS, ADÁPTALO A TU SISTEMA) ===
def leer_ventas():
    if not os.path.exists(VENTAS_XML):
        root = ET.Element('ventas')
        ET.ElementTree(root).write(VENTAS_XML, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(VENTAS_XML)
    root = tree.getroot()
    ventas = []
    for v in root.findall('venta'):
        ventas.append({
            'fecha': v.get('fecha'),
            'vendedor': v.get('vendedor'),
            'total': float(v.get('total', '0'))
        })
    return ventas

def total_recaudado():
    ventas = leer_ventas()
    return sum(v['total'] for v in ventas)

# === DASHBOARD PRINCIPAL ===


if __name__ == '__main__':
    app.run(debug=True, port=5000)

