
from flask import Flask, request, jsonify, send_from_directory, Response
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'datos_bingo.xml')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'PANEL_BINGO_75.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.json.get('numero')
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    balotas = root.find('balotas')

    # Marcar el número con ESTADO y ULTIMO
    for balota in balotas.findall('balota'):
        if balota.attrib['NUMERO'] == str(numero):
            balota.set('ESTADO', str(numero))
            balota.set('ULTIMO', str(numero))
        else:
            balota.set('ULTIMO', '')

    # Actualizar ULTIMO_NUMERO_GLOBAL
    ultimo_global = root.find('ULTIMO_NUMERO_GLOBAL')
    if ultimo_global is None:
        ultimo_global = ET.SubElement(root, 'ULTIMO_NUMERO_GLOBAL')
    ultimo_global.text = str(numero)

    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)
    return jsonify({'mensaje': 'Número guardado correctamente'})

@app.route('/resetear', methods=['POST'])
def resetear():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    balotas = root.find('balotas')

    for balota in balotas.findall('balota'):
        balota.set('ESTADO', '')
        balota.set('ULTIMO', '')

    # Vaciar el ULTIMO_NUMERO_GLOBAL
    ultimo_global = root.find('ULTIMO_NUMERO_GLOBAL')
    if ultimo_global is None:
        ultimo_global = ET.SubElement(root, 'ULTIMO_NUMERO_GLOBAL')
    ultimo_global.text = '0'

    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)
    return jsonify({'mensaje': 'Reinicio completado'})

@app.route('/xml')
def ver_xml():
    with open(XML_FILE, 'r', encoding='utf-8') as f:
        contenido = f.read()
    return Response(contenido, mimetype='application/xml')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
