from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_from_directory, send_file
import os
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
from flask_login import LoginManager, login_required, current_user
import xml.etree.ElementTree as ET
import re
import json

# Blueprints de usuarios
from usuarios import bp_usuarios   # Asegúrate que tu archivo usuarios.py tenga 'bp_usuarios' definido correctamente

# OTRAS IMPORTACIONES DE BLUEPRINTS SI LAS TIENES
app = Flask(__name__)




#IMPORT PANDAS


import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARCHIVO_NUMEROS_MARCADOS = os.path.join(DATA_DIR, "numeros_marcados.txt")


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
        for letra in ['b','i','n','g','o']:
            for i in range(1,6):
                clave = f"{letra}{i}"
                # .get devuelve None si falta la clave -> tratamos como 0
                val = boleto.get(clave, 0)
                val = int(val) if pd.notna(val) and str(val).isdigit() else 0
                carton.append(val)
    except Exception as e:
        # cualquier error, devolvemos False
        app.logger.error(f"ERROR al leer boleto {boleto.get('numero','?')}: {e}")
        return False

    # comprueba que todos los números marcados estén en carton
    for num in carton:
        if num != 0 and num not in numeros_marcados:
            return False
    return True




def buscar_ganadores_carton_lleno(archivos_cartones, numeros_marcados):
    ganadores = []
    for archivo in archivos_cartones:
        ext = os.path.splitext(archivo)[1].lower()
        try:
            if ext in ('.xlsx', '.xls'):
                # Lee un fichero Excel
                df = pd.read_excel(archivo, engine='openpyxl')
            elif ext == '.csv':
                # Lee un CSV
                df = pd.read_csv(archivo)
            elif ext == '.xml':
                # Lee un XML
                df = pd.read_xml(archivo)
            else:
                app.logger.warning(f"Formato no soportado, salto: {archivo}")
                continue

        except Exception as e:
            app.logger.error(f"No pude leer {archivo}: {e}")
            continue

        for _, boleto in df.iterrows():
            # Access seguro de la columna 'numero'
            numero = boleto.get('numero') or boleto.get('Número') or ''
            if not numero:
                app.logger.error(f"Falta columna 'numero' en {archivo}")
                continue

            # Comprueba ganador usando tu función segura
            if es_carton_lleno(boleto, numeros_marcados):
                ganadores.append({
                    "archivo": archivo,
                    "numero": numero
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



#generar sorteos y cargar sorteos este bloque es importante


@app.route('/generar_sorteo')
def generar_sorteo():
    # Aquí simulo los datos que necesitas; en tu sistema deberías leerlos de tu base de datos o archivos:
    sorteo = {
        "fecha": "2025-06-27",
        "identificador": "AC-123",
        "numero": 1,
        "boletos_total": 1500,
        "boletos_vendidos": 1200,
        "boletos_devueltos": 300,
        "figuras_jugadas": [
            {"nombre": "LETRA L", "premio": 500},
            {"nombre": "HUESO", "premio": 800}
        ],
        "vendedores": [
            {"nombre": "Juan Pérez", "planillas": 5, "vendidos": 150, "devueltos": 30, "ganancia_vendedor": 45, "ganancia_empresa": 105},
            {"nombre": "María López", "planillas": 4, "vendidos": 120, "devueltos": 20, "ganancia_vendedor": 36, "ganancia_empresa": 84}
        ],
        "caja": {
            "total_recaudado": 1200,
            "ganancia_empresa": 800,
            "ganancia_vendedores": 400
        },
        "ultima_balota": 37,
        "balotas_marcadas": [5, 12, 18, 21, 37],
        "figuras_ganadoras": [
            {"figura": "LETRA L", "tabla": "A23", "premio": 500}
        ],
        "estado": "abierto"  # o "cerrado" según el estado del día
    }

    return render_template('generar_sorteo.html', sorteo=sorteo)

# Activar sorteo
@app.route('/activar_sorteo/<int:id>')
def activar_sorteo(id):
    sorteos = cargar_sorteos()
    for sorteo in sorteos:
        if sorteo['id'] == id:
            sorteo['estado'] = 'Activo'
    guardar_sorteos(sorteos)
    flash("Sorteo activado correctamente.", "info")
    return redirect(url_for('generar_sorteo'))

# Procesar día (cerrar sorteo)
@app.route('/procesar_sorteo/<int:id>')
def procesar_sorteo(id):
    sorteos = cargar_sorteos()
    for sorteo in sorteos:
        if sorteo['id'] == id:
            sorteo['estado'] = 'Procesado'
    guardar_sorteos(sorteos)
    flash("Día procesado, el sorteo ha sido cerrado.", "warning")
    return redirect(url_for('generar_sorteo'))

# Eliminar sorteo
@app.route('/eliminar_sorteo/<int:id>')
def eliminar_sorteo(id):
    sorteos = cargar_sorteos()
    sorteos = [s for s in sorteos if s['id'] != id]
    guardar_sorteos(sorteos)
    flash("Sorteo eliminado correctamente.", "danger")
    return redirect(url_for('generar_sorteo'))


@app.route('/ver_sorteo/<int:id>')
def ver_sorteo(id):
    sorteos = cargar_sorteos()
    sorteo = next((s for s in sorteos if s['id'] == id), None)
    if not sorteo:
        flash("Sorteo no encontrado.", "danger")
        return redirect(url_for('generar_sorteo'))
    return render_template('ver_sorteo.html', sorteo=sorteo)


# Utilidades para manejar sorteos como archivo JSON
SORTEOS_FILE = 'sorteos.json'

def cargar_sorteos():
    if not os.path.exists(SORTEOS_FILE):
        return []
    with open(SORTEOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_sorteos(sorteos):
    with open(SORTEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorteos, f, indent=2, ensure_ascii=False)




#codigo del tablero 


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








def verificar_ganador_figura():
    import xml.etree.ElementTree as ET

    XML_BALOTAS = os.path.join(DATA_DIR, "datos_bingo.xml")
    RUTA_FIGURAS_DIA = os.path.join(DATA_DIR, "figuras_del_dia.xml")
    ARCHIVOS_CARTONES = [
        os.path.join(DATA_DIR, "Srs_ib1.csv"),
        os.path.join(DATA_DIR, "Srs_ib2.csv"),
        os.path.join(DATA_DIR, "Srs_ib3.csv"),
        os.path.join(DATA_DIR, "Srs_Manilla.csv"),
    ]

    # 1. Lee números marcados
    tree = ET.parse(XML_BALOTAS)
    root = tree.getroot()
    balotas = root.find('balotas')
    numeros_marcados = set(
        int(b.get('estado')) for b in balotas.findall('balota')
        if b.get('estado') and b.get('estado').isdigit()
    )

    # 2. Lee figuras del día
    tree_fig = ET.parse(RUTA_FIGURAS_DIA)
    root_fig = tree_fig.getroot()
    figuras = []
    for f in root_fig.findall("figura"):
        nombre = f.attrib.get("nombre")
        valor = int(f.attrib.get("valor", 0))
        colores = f.find("cuadro").text.split(",")
        posiciones = [i for i, c in enumerate(colores) if c.strip().upper() == "#FF0000"]
        figuras.append({
            "nombre": nombre,
            "valor": valor,
            "posiciones": posiciones,
            "colores": colores
        })

    # 3. Recorre cada cartón
    for archivo in ARCHIVOS_CARTONES:
        if not os.path.exists(archivo):
            continue
        df = pd.read_csv(archivo)
        df.columns = [col.strip().lower() for col in df.columns]
        for idx, boleto in df.iterrows():
            carton = []
            try:
                carton += [int(boleto[f'b{i}']) for i in range(1, 6)]
                carton += [int(boleto[f'i{i}']) for i in range(1, 6)]
                carton += [int(boleto[f'n{i}']) for i in range(1, 6)]
                carton += [int(boleto[f'g{i}']) for i in range(1, 6)]
                carton += [int(boleto[f'o{i}']) for i in range(1, 6)]
            except Exception as e:
                continue

            for figura in figuras:
                if not figura["posiciones"]:
                    continue
                numeros_figura = [carton[i] for i in figura["posiciones"] if carton[i] != 0]
                if all(num in numeros_marcados for num in numeros_figura):
                    return {
                        "success": True,
                        "ganador": {
                            "boleto": str(boleto['numero']),
                            "figura": figura["nombre"],
                            "valor": figura["valor"],
                            "casillas_boleto": carton,
                            "posiciones_figura": figura["posiciones"],
                            "numeros": numeros_figura,
                        }
                    }
    return {"success": True, "ganador": None}




@app.route('/verificar_ganador_figura', methods=['POST'])
def api_verificar_ganador_figura():
    resultado = verificar_ganador_figura()
    return jsonify(resultado)




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
# ── CALIBRACIÓN GLOBAL ────────────────────────────────────────────
# Ajusta estos valores (pt) hasta que tu PDF cuadre con la impresora:
CALIB_X =  10    # positivo → desplaza todo hacia la derecha
CALIB_Y = -20    # negativo → desplaza todo hacia arriba


# ── CONSTANTES DE DISEÑO ─────────────────────────────────────────
COLUMNAS      = 2      # boletos por fila
FILAS         = 4      # filas de boletos por página
MARGEN_H      = 14     # margen general (izq/dcha hoja)
ESPACIO_H     = 35     # espacio horizontal entre celdas
ESPACIO_V     = 35     # espacio vertical entre celdas

GRID_SCALE    = 0.9    # compacidad del bloque 5×5 (0.0–1.0)
CELL_ROT      = -90    # rotación de la rejilla de números
GRID_OFFSET_X = +60    # desplazamiento horizontal global de la rejilla
GRID_OFFSET_Y = -10    # desplazamiento vertical global de la rejilla

SIZE_NUM      = 20     # tamaño fuente de los números de la rejilla
SIZE_ID       = 10     # tamaño fuente del ID del boleto (destacado)
INFO_FSIZE    = 9     # tamaño de fuente de la línea de info
SIZE_INFO     = INFO_FSIZE
INFO_ROT      = -90    # rotación de la línea de info
INFO_DX       = -140   # desplazamiento X global de la info
INFO_DY       = +80    # desplazamiento Y global de la info

REINT_W       = 45     # ancho del icono de reintegro
REINT_H       = 45     # alto del icono de reintegro
REINT_ROT     = -90    # rotación del icono de reintegro
REINT_DX      = -REINT_W + 170  # desplazamiento X global del reintegro
REINT_DY      = +140            # desplazamiento Y global del reintegro

# ── Offsets específicos por boleto (0-based) ──
per_cell_offsets = {
    0: {"grid_x": -95, "grid_y": -80, "info_x": 116.8, "info_y": 113, "rein_x": 60, "rein_y":  -265},
    1: {"grid_x":-95, "grid_y": -70, "info_x":  120, "info_y": 113, "rein_x": 70,  "rein_y": -265},
    2: {"grid_x": -95, "grid_y": -80, "info_x": 116.8, "info_y": 113, "rein_x": 60, "rein_y":  -265},
    3: {"grid_x": -95, "grid_y": -70, "info_x": 120, "info_y": 113, "rein_x": 70, "rein_y":  -265},
    4: {"grid_x": -95, "grid_y": -80, "info_x": 116.8, "info_y": 113, "rein_x": 60, "rein_y":  -265},
    5: {"grid_x": -95, "grid_y": -70, "info_x": 120, "info_y": 113, "rein_x": 70, "rein_y":  -265},
    6: {"grid_x": -95, "grid_y": -80, "info_x": 116.8, "info_y": 113, "rein_x": 60, "rein_y":  -265},
    7: {"grid_x": -95, "grid_y": -70, "info_x": 120, "info_y": 113, "rein_x": 70, "rein_y":  -265},
}


# ── MAPEADO DE SERIES ──
SERIE_MAP = {
    "Srs_ib1.xlsx": "V",
    "Srs_ib2.xlsx": "+",
    "Srs_ib3.xlsx": "&",
    "Srs_Manila.xlsx": "M"
}

@app.route('/impresion', methods=['GET', 'POST'])
def impresion():
    files = sorted(f for f in os.listdir(DATA_DIR) if f.lower().endswith('.xlsx'))
    series = [(f, SERIE_MAP.get(f, f)) for f in files]

    reintegros = sorted(f for f in os.listdir(REINTEGROS_DIR) if f.lower().endswith('.png'))
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
            incluir_aleatorio = (request.form.get('incluir_aleatorio', '1') == '1')

            path = os.path.join(DATA_DIR, nombre)
            df = pd.read_excel(path, dtype=str).fillna('')
            ids = df[df.columns[0]].astype(str).tolist()
            if start and start in ids:
                ids = ids[ids.index(start):]
            if end and end in ids:
                ids = ids[:ids.index(end) + 1]
            boletos = df[df[df.columns[0]].astype(str).isin(ids)]

            pdf_buf = generar_pdf_boletos_excel(
                ids, boletos, valor, telefono, nombre,
                reintegro_especial, cant_reintegro_especial,
                reintegros, incluir_aleatorio, fecha_sorteo
            )

            sorteos = cargar_sorteos()
            activo = next((s for s in sorteos if s['estado'] == 'Activo'), None)
            if activo:
                activo['boletos_impresos'] = {
                    "serie": nombre,
                    "inicio": ids[0],
                    "fin": ids[-1],
                    "cantidad": len(ids),
                    "fecha": fecha_sorteo
                }
                guardar_sorteos(sorteos)

            return send_file(pdf_buf, download_name='boletos_bingo.pdf', as_attachment=True)

        elif form_type == "planilla":
            archivo = request.form['serie_archivo_planilla']
            inicio = int(request.form['planilla_inicio'])
            fin = int(request.form['planilla_fin'])
            fecha_planilla = request.form['fecha_planilla']

            path = os.path.join(DATA_DIR, archivo)
            if not os.path.exists(path):
                raise FileNotFoundError(f"El archivo {path} no existe. Verifica tus archivos.")

            if archivo.lower().endswith('.csv'):
                df = pd.read_csv(path, dtype=str).fillna('')
            else:
                df = pd.read_excel(path, dtype=str).fillna('')

            ids = df[df.columns[0]].astype(str).tolist()[inicio-1:fin]

            BOLETOS_X_PLANILLA = 40
            merger = PdfMerger()
            for i in range(0, len(ids), BOLETOS_X_PLANILLA):
                bloque_ids = ids[i:i + BOLETOS_X_PLANILLA]
                bloque_ini = inicio + i
                bloque_fin = min(bloque_ini + BOLETOS_X_PLANILLA - 1, fin)
                num_planilla = (i // BOLETOS_X_PLANILLA) + 1

                planilla_buf = generar_pdf_planilla(
                    bloque_ids, archivo, 'SIN_NOMBRE',
                    fecha_planilla, bloque_ini, bloque_fin,
                    SERIE_MAP, num_planilla
                )
                merger.append(planilla_buf)

            out = BytesIO()
            merger.write(out)
            out.seek(0)

            sorteos = cargar_sorteos()
            activo = next((s for s in sorteos if s['estado'] == 'Activo'), None)
            if activo:
                if 'planillas' not in activo:
                    activo['planillas'] = []
                activo['planillas'].append({
                    "vendedor": "SIN_NOMBRE",
                    "archivo": archivo,
                    "inicio": inicio,
                    "fin": fin,
                    "planillas": (fin - inicio + 1) // 30
                })
                guardar_sorteos(sorteos)

            return send_file(out, download_name='planilla_vendedor.pdf', as_attachment=True)

    return render_template(
        'impresion_boletos_excel.html',
        series=series,
        reintegros=reintegros,
        fecha_hoy=fecha_hoy
    )
                 

POSICIONES_FILE = os.path.join(DATA_DIR, "posiciones_boletos.json")

@app.route('/editor_boletos', methods=['GET', 'POST'])
def editor_boletos():
    if request.method == 'POST':
        # Recibir JSON del front-end y guardar en archivo
        posiciones = request.get_json()
        with open(POSICIONES_FILE, 'w', encoding='utf-8') as f:
            json.dump(posiciones, f, indent=2)
        return jsonify({"success": True, "msg": "Posiciones guardadas correctamente."})
    return render_template('editor_boletos.html')    






def generar_pdf_boletos_excel(
    ids, registros, valor, telefono,
    nombre, reintegro_especial,
    cant_especial, reintegros,
    incluir_aleatorio, fecha_sorteo
):
    buf = BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    ancho_pg, alto_pg = A4

    # convertir DataFrame a lista de dicts si hace falta
    if hasattr(registros, "to_dict"):
        registros = registros.to_dict("records")
    elif registros and isinstance(registros[0], str):
        registros = [{} for _ in registros]

    N = len(registros)
    esp_idx = random.sample(range(N), min(N, cant_especial)) if reintegro_especial else []
    ale_idx = [i for i in range(N) if i not in esp_idx] if incluir_aleatorio else []

    # dimensiones de cada boleto
    ancho_bol = (ancho_pg - 2*MARGEN_H - ESPACIO_H*(COLUMNAS-1)) / COLUMNAS
    alto_bol  = (alto_pg  - 2*MARGEN_H - ESPACIO_V*(FILAS   -1)) / FILAS
    size_celda = min(ancho_bol, alto_bol) * GRID_SCALE / 5

    # iterar páginas
    for start in range(0, N, COLUMNAS*FILAS):
        # re-aplico calibración al inicio de CADA página
        c.saveState()
        c.translate(CALIB_X, CALIB_Y)

        chunk = registros[start:start + COLUMNAS*FILAS]
        for i, row in enumerate(chunk):
            pos = start + i
            col = i % COLUMNAS
            fil = i // COLUMNAS

            x0 = MARGEN_H + col*(ancho_bol + ESPACIO_H)
            y0 = alto_pg - MARGEN_H - fil*(alto_bol + ESPACIO_V)
            cx, cy = x0 + ancho_bol/2, y0 - alto_bol/2

            offs = per_cell_offsets.get(i, {})

            # 1) rejilla 5×5 + QR
            bb_w, bb_h = size_celda*5, size_celda*5
            bx0 = cx - bb_w/2 + GRID_OFFSET_X + offs.get("grid_x", 0)
            by0 = cy + bb_h/2 + GRID_OFFSET_Y + offs.get("grid_y", 0)

            c.saveState()
            c.translate(cx, cy)
            c.rotate(CELL_ROT)
            c.translate(-cx, -cy)
            c.setFont("Helvetica-Bold", SIZE_NUM)
            for r in range(5):
                for j, letra in enumerate("bingo"):
                    x = bx0 + j*size_celda
                    y = by0 - r*size_celda
                    if letra=="n" and r==2:
                        qr = qrcode.make(f"{ids[pos]}|{fecha_sorteo}")
                        qr_buf = BytesIO()
                        qr.save(qr_buf, "PNG")
                        qr_buf.seek(0)
                        c.drawImage(
                            ImageReader(qr_buf),
                            x+1, y+1,
                            size_celda-2, size_celda-2
                        )
                    else:
                        v = str(row.get(f"{letra}{r+1}", "-"))
                        c.drawCentredString(
                            x + size_celda/2,
                            y + size_celda*0.28,
                            v
                        )
            c.restoreState()

            # 2) línea de info rotada
            x_info = x0 + INFO_DX + offs.get("info_x", 0)
            y_info = y0 - size_celda*5 + INFO_DY + offs.get("info_y", 0)

            c.saveState()
            c.translate(x_info, y_info)
            c.rotate(INFO_ROT)

            boleto_text = f"{ids[pos]}{SERIE_MAP.get(nombre, nombre)}"
            c.setFont("Helvetica-Bold", SIZE_ID)
            c.drawString(0, 0, boleto_text)

            resto = f"  | {fecha_sorteo} | ${valor} | {telefono}"
            c.setFont("Helvetica", SIZE_INFO)
            dx = c.stringWidth(boleto_text, "Helvetica-Bold", SIZE_ID) + 5
            c.drawString(dx, 0, resto)
            c.restoreState()

            # 3) icono de reintegro rotado
            ix = x0 + REINT_DX + offs.get("rein_x", 0)
            iy = y0 + REINT_DY + offs.get("rein_y", 0)

            if pos in esp_idx and reintegro_especial:
                img_name = reintegro_especial
            elif pos in ale_idx and reintegros:
                others = [r for r in reintegros if r != reintegro_especial]
                img_name = random.choice(others) if others else None
            else:
                img_name = None

            if img_name:
                ruta = os.path.join(REINTEGROS_DIR, img_name)
                c.saveState()
                c.translate(ix + REINT_W/2, iy + REINT_H/2)
                c.rotate(REINT_ROT)
                c.translate(-ix - REINT_W/2, -iy - REINT_H/2)
                c.drawImage(ruta, ix, iy, REINT_W, REINT_H, mask="auto")
                c.restoreState()

        c.restoreState()
        c.showPage()

    c.save()
    buf.seek(0)
    return buf


















def generar_pdf_planilla(ids, serie_archivo, vendedor, fecha, inicio, fin, serie_map, num_planilla=None):
    from io import BytesIO
    from datetime import datetime
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    import os, qrcode

    # — Formatear fecha en español —
    dt = datetime.strptime(fecha, "%Y-%m-%d")
    dias   = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    meses  = {
        1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",
        5:"Mayo",6:"Junio",7:"Julio",8:"Agosto",
        9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
    }
    formatted_date = f"{dias[dt.weekday()]}, {dt.day} de {meses[dt.month]} del {dt.year}"
    fecha_limpia   = dt.strftime("%Y%m%d")
    serie_letra    = serie_map.get(serie_archivo, "")

    # — Rangos —
    left_desde  = inicio
    left_hasta  = min(inicio + 19, fin)
    right_desde = inicio + 20
    right_hasta = min(inicio + 39, fin)
    full_desde  = inicio
    full_hasta  = min(inicio + 39, fin)

    # — Generadores de cadena QR —
    def qr_cadena(tipo, desde, hasta, serie):
        return f"SORTEO{fecha_limpia}{tipo}A{desde}A{hasta}{serie}"

    # — Preparar canvas —
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    ancho, alto = landscape(A4)

    # — Márgenes y constantes —
    M_LEFT, M_RIGHT, M_BOTTOM = 20, 20, 20
    GUTTER, HEADER_H, QR_SIZE = 20, 60, 40

    # — Área útil para tablas —
    HALF_W  = (ancho - M_LEFT - M_RIGHT - GUTTER) / 2
    TOP_Y   = alto - HEADER_H - 5
    BOT_Y   = M_BOTTOM
    AVAIL_H = TOP_Y - BOT_Y

    # — Filas y altura dinámica —
    NUM_ROWS = 21
    ROW_H    = AVAIL_H / NUM_ROWS

    # — Posiciones X y ancho de tabla —
    X_L, X_R = M_LEFT, M_LEFT + HALF_W + GUTTER
    TABLE_W  = HALF_W - 20
    PAD      = 10

    # — Recursos y fuentes —
    LOGO_PATH = os.path.join("static","golpe_suerte_logo.png")
    FB, FR    = "Helvetica-Bold", "Helvetica"

    # — Índices de planilla según rango —
    left_index  = (left_desde - 1) // 20 + 1
    right_index = (right_desde - 1) // 20 + 1

    # — Función: dibuja header en x0 con QR de su rango —
    def draw_header(x0, sheet_num, tipo, desde, hasta):
        # fondo gris
        c.setFillColorRGB(0.9,0.9,0.9)
        c.rect(x0, alto - HEADER_H, HALF_W, HEADER_H, fill=1, stroke=0)
        c.setFillColor(colors.black)

        # logo grande manteniendo proporción
        img = ImageReader(LOGO_PATH)
        ow, oh = img.getSize()
        dh = HEADER_H - 4
        dw = dh * ow / oh
        c.drawImage(img,
                    x0 + 8,
                    alto - HEADER_H + 2,
                    width=dw, height=dh,
                    mask="auto")

        # recuadros de fecha
        box_w = HALF_W * 0.45
        box_h = 20
        bx = x0 + (HALF_W - box_w) / 2
        by = alto - HEADER_H + 8
        c.setLineWidth(1.5)
        c.setFillColor(colors.white)
        c.roundRect(bx, by + box_h + 4, box_w, box_h, 4, stroke=1, fill=1)  # vacío arriba
        c.roundRect(bx, by,               box_w, box_h, 4, stroke=1, fill=1)  # fecha
        c.setFillColor(colors.black)
        c.setFont(FB, 10)
        c.drawCentredString(bx + box_w/2, by + box_h/2 - 4, formatted_date)

        # QR de rango para esta mitad
        data_qr = qr_cadena(tipo, desde, hasta, serie_letra)
        buf = BytesIO(); qrcode.make(data_qr).save(buf,format="PNG"); buf.seek(0)
        qx = x0 + HALF_W - QR_SIZE - 8
        qy = alto - HEADER_H + 8
        c.drawImage(ImageReader(buf), qx, qy, QR_SIZE, QR_SIZE)

        # recuadro del número a la izquierda del QR
        pn_w, pn_h = 36, 28
        px = qx - pn_w - 6
        py = qy + (QR_SIZE - pn_h)/2
        c.setFillColor(colors.white)
        c.setLineWidth(1.5)
        c.roundRect(px, py, pn_w, pn_h, 4, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont(FB, 18)
        c.drawCentredString(px + pn_w/2, py + pn_h/2 - 5, str(sheet_num))

    # — Dibujar headers izquierdo y derecho con sus propios QR —
    draw_header(X_L, left_index,  "L1", left_desde,  left_hasta)
    draw_header(X_R, right_index, "L2", right_desde, right_hasta)

    # — Línea divisoria central —
    c.setLineWidth(2)
    c.line(X_R, TOP_Y, X_R, BOT_Y)

    # — QR central de rango completo (40 boletos) —
    data_full = qr_cadena("RG", full_desde, full_hasta, serie_letra)
    buf2 = BytesIO(); qrcode.make(data_full).save(buf2,format="PNG"); buf2.seek(0)
    mid_y = BOT_Y + (AVAIL_H/2) - (QR_SIZE/2)
    c.drawImage(ImageReader(buf2),
                ancho/2 - QR_SIZE/2,
                mid_y,
                QR_SIZE, QR_SIZE)

    # — Construir siempre 21 filas por tabla —
    left_data = [["Boleto / Nombres Apellidos",""]]
    for i in range(20):
        n = inicio + i
        left_data.append([str(n) if n <= fin else "", ""])
    right_data = [["Boleto / Nombres Apellidos",""]]
    for i in range(20):
        n = inicio + 20 + i
        right_data.append([str(n) if n <= fin else "", ""])

    # — Recuadro en encabezado de tabla —
    header_y = TOP_Y - ROW_H
    c.setLineWidth(1.5)
    c.roundRect(X_L + PAD, header_y, TABLE_W, ROW_H, 4, stroke=1, fill=0)
    c.roundRect(X_R + PAD, header_y, TABLE_W, ROW_H, 4, stroke=1, fill=0)

    # — Estilo de tabla —
    from reportlab.platypus import Table
    style = TableStyle([
        ("SPAN",        (0,0),(1,0)),
        ("FONT",        (0,0),(1,0), FB, 10),
        ("ALIGN",       (0,0),(1,0),"CENTER"),
        ("FONT",        (0,1),(0,-1), FB, 12),
        ("FONT",        (1,1),(1,-1), FR, 8),
        ("VALIGN",      (0,0),(-1,-1),"MIDDLE"),
        ("INNERGRID",   (0,0),(-1,-1),1,colors.black),
        ("BOX",         (0,0),(-1,-1),2,colors.black),
        ("LEFTPADDING", (0,0),(-1,-1),3),
        ("RIGHTPADDING",(0,0),(-1,-1),3),
    ])

    # — Renderizar tablas —
    tblL = Table(left_data,  colWidths=[40, TABLE_W-40], rowHeights=[ROW_H]*NUM_ROWS)
    tblL.setStyle(style); tblL.wrapOn(c,0,0); tblL.drawOn(c, X_L+PAD, BOT_Y)
    tblR = Table(right_data, colWidths=[40, TABLE_W-40], rowHeights=[ROW_H]*NUM_ROWS)
    tblR.setStyle(style); tblR.wrapOn(c,0,0); tblR.drawOn(c, X_R+PAD, BOT_Y)

    c.save()
    buffer.seek(0)
    return buffer




#fin de asignar planillas





VENDEDORES_XML = os.path.join(DATA_DIR, "vendedores.xml")

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

def guardar_vendedores(lista_vendedores):
    root = ET.Element("vendedores")
    for vend in lista_vendedores:
        ET.SubElement(root, "vendedor", id=str(vend["id"]), nombre=vend["nombre"], alias=vend["alias"])
    tree = ET.ElementTree(root)
    tree.write(VENDEDORES_XML, encoding="utf-8", xml_declaration=True)


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

@app.route('/prueba')
def prueba():
    print("Entró a la ruta /prueba")
    return "¡PRUEBA OK!"



if __name__ == '__main__':
    app.run(debug=True, port=5000)

