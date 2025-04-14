
from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'datos_bingo.xml')

def cargar_xml():
    tree = ET.parse(XML_FILE)
    return tree, tree.getroot()

def guardar_xml(tree):
    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)

@app.route('/')
def inicio():
    return send_from_directory(app.static_folder, 'PANEL_BINGO_75.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = str(request.json.get('numero'))

    tree, root = cargar_xml()

    # Lista para guardar últimos 5 números
    ultimos_nodos = root.find('ultimos')
    ultimo_global = ultimos_nodos.find('ULTIMO_NUMERO_GLOBAL')
    ultimos5 = ultimos_nodos.find('ULTIMOS_5_NUMEROS')

    balotas = root.find('balotas')

    for balota in balotas.findall('balota'):
        if balota.attrib['NUMERO'] == numero:
            balota.set('ESTADO', numero)
            balota.set('ULTIMO', numero)
        else:
            balota.set('ULTIMO', '')

    # Actualizar último número global
    ultimo_global.text = numero

    # Actualizar últimos 5 números
    historial = ultimos5.text.split(',') if ultimos5.text else []
    if numero not in historial:
        historial.append(numero)
        if len(historial) > 5:
            historial.pop(0)
    ultimos5.text = ','.join(historial)

    guardar_xml(tree)
    return jsonify({'ok': True})

@app.route('/resetear', methods=['POST'])
def resetear():
    tree, root = cargar_xml()
    balotas = root.find('balotas')

    for balota in balotas.findall('balota'):
        balota.set('ESTADO', '')
        balota.set('ULTIMO', '')

    ultimos = root.find('ultimos')
    ultimos.find('ULTIMO_NUMERO_GLOBAL').text = "0"
    ultimos.find('ULTIMOS_5_NUMEROS').text = ""

    guardar_xml(tree)
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
