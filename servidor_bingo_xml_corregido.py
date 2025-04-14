from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'datos_bingo.xml')

def leer_datos():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return tree, root

def escribir_datos(tree):
    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.json.get('numero')
    if not numero:
        return jsonify({'error': 'Número no proporcionado'}), 400

    tree, root = leer_datos()
    balotas = root.find('balotas')
    ultimos_nodos = root.find('ultimos')

    if ultimos_nodos is None:
        ultimos_nodos = ET.SubElement(root, 'ultimos')
        ET.SubElement(ultimos_nodos, 'ULTIMO_NUMERO_GLOBAL').text = ""
        ET.SubElement(ultimos_nodos, 'ULTIMOS_5_NUMEROS').text = ""

    # Actualizar balotas
    for balota in balotas.findall('balota'):
        if balota.attrib['NUMERO'] == numero:
            balota.set('ESTADO', numero)
            balota.set('ULTIMO', numero)
        else:
            balota.set('ULTIMO', "")

    # Actualizar último número global
    ultimo_global = ultimos_nodos.find('ULTIMO_NUMERO_GLOBAL')
    ultimo_global.text = numero

    # Actualizar últimos 5
    ultimos_5 = ultimos_nodos.find('ULTIMOS_5_NUMEROS')
    actuales = ultimos_5.text.split() if ultimos_5.text else []
    if numero not in actuales:
        actuales.insert(0, numero)
    ultimos_5.text = ' '.join(actuales[:5])

    escribir_datos(tree)
    return jsonify({'success': True}), 200

@app.route('/resetear', methods=['POST'])
def resetear():
    tree, root = leer_datos()
    balotas = root.find('balotas')
    ultimos_nodos = root.find('ultimos')

    for balota in balotas.findall('balota'):
        balota.set('ESTADO', '')
        balota.set('ULTIMO', '')

    if ultimos_nodos is None:
        ultimos_nodos = ET.SubElement(root, 'ultimos')
        ET.SubElement(ultimos_nodos, 'ULTIMO_NUMERO_GLOBAL').text = ""
        ET.SubElement(ultimos_nodos, 'ULTIMOS_5_NUMEROS').text = ""
    else:
        ultimos_nodos.find('ULTIMO_NUMERO_GLOBAL').text = ""
        ultimos_nodos.find('ULTIMOS_5_NUMEROS').text = ""

    escribir_datos(tree)
    return jsonify({'reset': True}), 200

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')
