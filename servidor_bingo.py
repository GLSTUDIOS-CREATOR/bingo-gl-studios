from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'datos_bingo.xml')

@app.route('/')
def inicio():
    return send_from_directory(app.static_folder, 'PANEL_BINGO_75.html')

def leer_datos():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return tree, root

def escribir_datos(tree):
    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.json.get('numero')
    if numero is None:
        return jsonify({'error': 'Número no proporcionado'}), 400

    tree, root = leer_datos()

    ultimos = root.find('ultimos')
    if ultimos is None:
        ultimos = ET.SubElement(root, 'ultimos')

    ultimo_global = root.find('ultimo_global')
    if ultimo_global is None:
        ultimo_global = ET.SubElement(root, 'ultimo_global')

    balotas = root.find('balotas')
    for balota in balotas.findall('balota'):
        if balota.get('NUMERO') == str(numero):
            balota.set('ESTADO', str(numero))
            balota.set('ULTIMO', str(numero))
        else:
            balota.set('ULTIMO', '')

    # Actualizar últimos 5 números
    ultimos_numeros = [elem.text for elem in ultimos.findall('numero')]
    ultimos_numeros = [n for n in ultimos_numeros if n and n != str(numero)]
    ultimos_numeros = ([str(numero)] + ultimos_numeros)[:5]

    # Limpiar y volver a insertar
    for elem in ultimos.findall('numero'):
        ultimos.remove(elem)
    for n in ultimos_numeros:
        ET.SubElement(ultimos, 'numero').text = n

    ultimo_global.text = str(numero)

    escribir_datos(tree)
    return jsonify({'success': True})

@app.route('/resetear', methods=['POST'])
def resetear():
    tree, root = leer_datos()

    balotas = root.find('balotas')
    for balota in balotas.findall('balota'):
        balota.set('ESTADO', '')
        balota.set('ULTIMO', '')

    ultimos = root.find('ultimos')
    if ultimos is not None:
        for elem in ultimos.findall('numero'):
            ultimos.remove(elem)

    ultimo_global = root.find('ultimo_global')
    if ultimo_global is not None:
        ultimo_global.text = ''

    escribir_datos(tree)
    return jsonify({'reset': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)