from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'PANEL_BINGO_75.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.form.get('numero')

    tree = ET.parse('static/datos_bingo.xml')
    root = tree.getroot()
    
    balotas_container = root.find("balotas")
    if balotas_container is None:
        return "Error: <balotas> no encontrada", 500

    balotas = balotas_container.findall("balota")

    # Resetear el atributo ULTIMO de todas las balotas
    for balota in balotas:
        balota.set("ULTIMO", "")

    # Asignar el valor al número marcado
    for balota in balotas:
        if balota.get("NUMERO") == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
            break

    # Obtener o crear nodo global
    if len(balotas) > 0:
        balotas[0].set("ULTIMO_NUMERO_GLOBAL", numero)

    tree.write("static/datos_bingo.xml", encoding="utf-8", xml_declaration=True)
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    tree = ET.parse('static/datos_bingo.xml')
    root = tree.getroot()

    balotas_container = root.find("balotas")
    if balotas_container is None:
        return "Error: <balotas> no encontrada", 500

    balotas = balotas_container.findall("balota")

    for balota in balotas:
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write("static/datos_bingo.xml", encoding="utf-8", xml_declaration=True)
    return "Reset completo"
