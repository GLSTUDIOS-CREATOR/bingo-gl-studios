
from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET

app = Flask(__name__, static_folder='static')

XML_PATH = 'static/datos_bingo.xml'

@app.route('/')
def index():
    return send_from_directory('static', 'PANEL_BINGO_75.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.form.get('numero')

    if not numero:
        return 'Número no proporcionado', 400

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    ultimos = root.find('ultimos')
    ultimo_numero_global = root.find('ultimo_numero_global')
    balotas = root.find('balotas')

    if balotas is None or ultimos is None or ultimo_numero_global is None:
        return 'Estructura del XML no válida', 500

    for balota in balotas.findall('balota'):
        num = balota.find('NUMERO')
        estado = balota.find('ESTADO')
        ultimo = balota.find('ULTIMO')

        if num is not None and estado is not None and ultimo is not None:
            if num.text == numero:
                estado.text = numero
                ultimo.text = numero
            else:
                ultimo.text = ""

    # Actualizar ULTIMO_NUMERO_GLOBAL (solo en la primera fila visible)
    for balota in balotas.findall('balota'):
        ultimo_global = balota.find('ULTIMO_NUMERO_GLOBAL')
        if ultimo_global is not None:
            ultimo_global.text = numero
            break

    # Actualizar los 5 últimos números
    prev = ultimos.text.strip().split() if ultimos.text else []
    prev = (prev + [numero])[-5:]
    ultimos.text = " ".join(prev)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return 'Guardado correctamente'

@app.route('/reset', methods=['POST'])
def reset():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    balotas = root.find('balotas')
    ultimos = root.find('ultimos')

    if balotas is None or ultimos is None:
        return 'Estructura del XML no válida', 500

    for balota in balotas.findall('balota'):
        if balota.find('ESTADO') is not None:
            balota.find('ESTADO').text = ""
        if balota.find('ULTIMO') is not None:
            balota.find('ULTIMO').text = ""
        if balota.find('ULTIMO_NUMERO_GLOBAL') is not None:
            balota.find('ULTIMO_NUMERO_GLOBAL').text = ""

    ultimos.text = ""
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return 'Reseteado correctamente'

@app.route('/xml')
def serve_xml():
    return send_from_directory('static', 'datos_bingo.xml')

if __name__ == '__main__':
    app.run(debug=True)
