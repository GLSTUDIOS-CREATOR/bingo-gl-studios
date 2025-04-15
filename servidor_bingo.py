from flask import Flask, request, jsonify, send_from_directory
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)
XML_FILE = os.path.join(app.root_path, 'static', 'datos_bingo.xml')

@app.route('/')
def index():
    return send_from_directory('static', 'PANEL_BINGO_75.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.json.get("numero")
    if not numero:
        return jsonify({"error": "Número no proporcionado"}), 400

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    # Actualizar ULTIMO_NUMERO_GLOBAL en la primera fila
    primera_fila = root.find('balota')
    if primera_fila is not None:
        ultimo_global = primera_fila.find('ULTIMO_NUMERO_GLOBAL')
        if ultimo_global is not None:
            ultimo_global.text = str(numero)

    # Actualizar ESTADO y ULTIMO en la balota marcada
    for balota in root.findall('balota')[1:]:  # omitir la primera fila
        num = balota.find('NUMERO').text
        if num == str(numero):
            balota.find('ESTADO').text = str(numero)
            balota.find('ULTIMO').text = str(numero)
        else:
            balota.find('ULTIMO').text = ""

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True}), 200

@app.route('/reset', methods=['POST'])
def reset():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    # Limpiar ULTIMO_NUMERO_GLOBAL
    primera_fila = root.find('balota')
    if primera_fila is not None:
        ultimo_global = primera_fila.find('ULTIMO_NUMERO_GLOBAL')
        if ultimo_global is not None:
            ultimo_global.text = ""

    # Limpiar ESTADO y ULTIMO de cada balota
    for balota in root.findall('balota')[1:]:  # omitir la primera fila
        balota.find('ESTADO').text = ""
        balota.find('ULTIMO').text = ""

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"reset": True}), 200

@app.route('/xml')
def xml():
    return send_from_directory('static', 'datos_bingo.xml')
