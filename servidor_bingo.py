from flask import Flask, request, jsonify, send_from_directory
import os
import xml.etree.ElementTree as ET

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'datos_bingo.xml')

def leer_datos():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return tree, root

def escribir_datos(tree):
    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)

@app.route('/xml')
def serve_xml():
    return send_from_directory(app.static_folder, 'datos_bingo.xml')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = str(request.json.get('numero'))

    tree, root = leer_datos()
    balotas = root.find('balotas')

    # Resetear todos los atributos ULTIMO y ULTIMO_NUMERO_GLOBAL
    for balota in balotas.findall('balota'):
        balota.set('ULTIMO', '')
        balota.set('ULTIMO_NUMERO_GLOBAL', '')

    # Últimos 5 números
    ultimos = root.find('ultimos')
    if ultimos is None:
        ultimos = ET.SubElement(root, 'ultimos')
    historial = ultimos.findall('numero')
    historial.append(ET.Element('numero'))
    historial[-1].text = numero
    if len(historial) > 5:
        ultimos.remove(historial[0])

    for balota in balotas.findall('balota'):
        if balota.get('NUMERO') == numero:
            balota.set('ESTADO', numero)
            balota.set('ULTIMO', numero)
            balota.set('ULTIMO_NUMERO_GLOBAL', numero)
        else:
            balota.set('ULTIMO', '')

    escribir_datos(tree)
    return jsonify({'mensaje': 'Número actualizado'}), 200

@app.route('/reset', methods=['POST'])
def resetear():
    tree, root = leer_datos()
    balotas = root.find('balotas')

    for balota in balotas.findall('balota'):
        balota.set('ESTADO', '')
        balota.set('ULTIMO', '')
        balota.set('ULTIMO_NUMERO_GLOBAL', '')

    ultimos = root.find('ultimos')
    if ultimos is not None:
        root.remove(ultimos)

    escribir_datos(tree)
    return jsonify({'mensaje': 'XML reiniciado'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
