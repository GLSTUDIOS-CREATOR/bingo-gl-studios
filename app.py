from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_from_directory
from flask import Flask, render_template, request, send_file
import os
import pandas as pd  # <--- ¡No olvides tener instalada la librería!
import random
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.secret_key = 'clave-secreta-segura'

# Claves independientes por sección
CLAVES_SECCIONES = {
    "dashboard": "PlandeDios10",
    "vendedores": "PlandeDios10",
    "impresion": "PlandeDios10",
    "asignar_planillas": "PlandeDios10"
}

RUTA_FIGURAS_CREADAS = os.path.join("data", "figuras_creadas.xml")
RUTA_FIGURAS_DIA = os.path.join("data", "figuras_del_dia.xml")
XML_PATH = os.path.join('data', 'datos_bingo.xml')


@app.route('/impresion_boletos', methods=['GET', 'POST'])
def impresion_boletos():
    if request.method == 'POST':
        cantidad = int(request.form['cantidad'])
        pdf_stream = generar_pdf_boletos(cantidad)
        return send_file(pdf_stream, as_attachment=True, download_name='boletos_bingo.pdf', mimetype='application/pdf')
    return render_template('impresion_boletos.html')


def generar_tabla_bingo():
    # Crea una tabla bingo 5x5 aleatoria (puedes personalizar con tus CSV)
    import random
    columnas = {
        'B': random.sample(range(1, 16), 5),
        'I': random.sample(range(16, 31), 5),
        'N': random.sample(range(31, 46), 5),
        'G': random.sample(range(46, 61), 5),
        'O': random.sample(range(61, 76), 5)
    }
    # El centro (N3) suele ser el espacio de QR o FREE
    columnas['N'][2] = 'QR'
    tabla = [[columnas[letra][fila] for letra in 'BINGO'] for fila in range(5)]
    return tabla

def generar_pdf_boletos(cantidad):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    for i in range(cantidad):
        tabla = generar_tabla_bingo()
        qr_data = f"Boleto-{i+1}"
        qr_img = qrcode.make(qr_data)
        qr_path = f"temp_qr_{i}.png"
        qr_img.save(qr_path)
        # Dibuja tabla (puedes mejorarlo visualmente)
        y = 700
        for fila in tabla:
            c.drawString(100, y, ' | '.join(str(n) for n in fila))
            y -= 20
        # Dibuja el QR en la posición del centro N3 visualmente
        c.drawImage(qr_path, 260, 650, width=60, height=60)
        os.remove(qr_path)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer



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

@app.route('/panel_figuras')
def panel_figuras():
    figuras_bingo = cargar_figuras_guardadas()
    figuras_dia = cargar_figuras_del_dia()
    return render_template('figuras_dia_visual.html',
                           figuras_bingo=figuras_bingo,
                           figuras_dia=figuras_dia)

@app.route("/guardar_figura_dia", methods=["POST"])
def guardar_figura_dia():
    data = request.get_json()
    nombre = data.get('nombre')
    valor = data.get('valor')
    colores = data.get('colores')

    if not nombre or not valor or not colores:
        return jsonify({"success": False, "error": "Datos incompletos"})

    # Cargar o crear XML
    if os.path.exists(RUTA_FIGURAS_DIA):
        tree = ET.parse(RUTA_FIGURAS_DIA)
        root = tree.getroot()
    else:
        root = ET.Element("figuras")
        tree = ET.ElementTree(root)

    # Evita duplicados
    for f in root.findall("figura"):
        if f.attrib.get("nombre") == nombre:
            return jsonify({"success": False, "error": "Figura ya está en el día"})

    figura_el = ET.SubElement(root, "figura", nombre=nombre, valor=valor, estado="normal")
    ET.SubElement(figura_el, "cuadro").text = ','.join(colores)

    tree.write(RUTA_FIGURAS_DIA, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

@app.route('/reset_figuras_dia', methods=['POST'])
def reset_figuras_dia():
    root = ET.Element("figuras_del_dia")
    tree = ET.ElementTree(root)
    tree.write(RUTA_FIGURAS_DIA, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)

@app.route('/marcar_balota', methods=['POST'])
def marcar_balota():
    try:
        numero = str(request.json.get('numero'))
        if not numero:
            return jsonify({"error": "Número no recibido"}), 400

        tree = ET.parse(XML_PATH)
        root = tree.getroot()
        balotas = root.find('balotas')

        for balota in balotas.findall('balota'):
            if balota.get('numero') == numero:
                balota.set('estado', numero if balota.get('estado') != numero else '')

        for balota in balotas.findall('balota'):
            balota.set('ultimo', '')
        for balota in balotas.findall('balota'):
            if balota.get('numero') == "1":
                balota.set('ultimo', numero)

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
        return jsonify({"success": True})
    except Exception as e:
        print("\U0001f4a5 ERROR MARCAR_BALOTA:", e)
        return jsonify({"error": str(e)}), 500

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



@app.route('/impresion', methods=['GET', 'POST'])
def impresion():
    # Listar los nombres de los archivos .xlsx/.csv en /data
    series_dir = 'data'
    series = [f for f in os.listdir(series_dir) if f.endswith('.xlsx') or f.endswith('.csv')]
    if request.method == 'POST':
        valor = request.form['valor']
        telefono = request.form['telefono']
        serie = request.form['serie']
        desde = int(request.form['desde'])
        hasta = int(request.form['hasta'])

        # Leer archivo Excel/CSV
        excel_path = os.path.join(series_dir, serie)
        if serie.endswith('.xlsx'):
            df = pd.read_excel(excel_path)
        else:
            df = pd.read_csv(excel_path)

        # Filtrar solo los boletos del rango solicitado
        boletos = df.iloc[desde-1:hasta]

        # Generar el PDF y retornar
        pdf_stream = generar_pdf_desde_boletos(boletos, valor, telefono, serie)
        return send_file(pdf_stream, as_attachment=True, download_name='boletos_bingo.pdf', mimetype='application/pdf')
    return render_template('impresion_boletos.html', series=series)


def generar_pdf_desde_boletos(boletos, valor, telefono, serie):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    for i, row in boletos.iterrows():
        # Supón que tu DataFrame tiene columnas: B1, B2, B3, B4, B5, I1, ..., O5
        tabla = []
        for letra in 'BINGO':
            fila = [str(row[f'{letra}{n}']) for n in range(1,6)]
            tabla.append(fila)
        # Transponer para que quede 5x5
        tabla = list(map(list, zip(*tabla)))

        # Dibuja tabla (esto lo puedes hacer visualmente bonito)
        y = 700
        for fila in tabla:
            c.drawString(100, y, ' | '.join(str(n) for n in fila))
            y -= 20

        # Agrega datos
        c.drawString(100, 620, f"Valor: ${valor}")
        c.drawString(200, 620, f"Tel: {telefono}")
        c.drawString(350, 620, f"Serie: {serie}")

        # Genera QR único por boleto
        qr_data = f"{serie}-{i+1}"
        qr_img = qrcode.make(qr_data)
        qr_path = f"temp_qr_{i}.png"
        qr_img.save(qr_path)
        c.drawImage(qr_path, 450, 650, width=60, height=60)
        os.remove(qr_path)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


@app.route("/vendedores")
def vendedores():
    if not requiere_clave("vendedores"):
        return redirect(url_for('pedir_clave', seccion="vendedores"))
    return render_template("vendedores.html")

@app.route("/asignar_planillas")
def asignar_planillas():
    if not requiere_clave("asignar_planillas"):
        return redirect(url_for('pedir_clave', seccion="asignar_planillas"))
    return "<h2>Página de Asignación de Planillas (en construcción)</h2>"

@app.route('/eliminar_figura_dia', methods=['POST'])
def eliminar_figura_dia():
    data = request.get_json()
    nombre = data.get('nombre')
    if not nombre:
        return jsonify({"success": False, "error": "Nombre no recibido"})

    if not os.path.exists(RUTA_FIGURAS_DIA):
        return jsonify({"success": False, "error": "Archivo no encontrado"})

    tree = ET.parse(RUTA_FIGURAS_DIA)
    root = tree.getroot()
    eliminado = False

    # Busca por nombre y elimina la figura
    for fig in root.findall("figura"):
        if fig.get("nombre") == nombre:
            root.remove(fig)
            eliminado = True
            break

    tree.write(RUTA_FIGURAS_DIA, encoding='utf-8', xml_declaration=True)
    return jsonify({"success": eliminado})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

