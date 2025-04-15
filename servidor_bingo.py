from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

RUTA_XML = os.path.join('static', 'datos_bingo.xml')

@app.route('/')
def home():
    return send_from_directory('static', 'PANEL_BINGO_75.html')

@app.route('/xml')
def obtener_xml():
    return send_from_directory('static', 'datos_bingo.xml')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.form.get('numero')
    if not numero:
        return 'Número no recibido', 400

    tree = ET.parse(RUTA_XML)
    root = tree.getroot()

    # Reiniciar ULTIMO en todas las balotas
    for balota in root.findall('balota'):
        balota.set('ULTIMO', '')

    # Buscar la balota correspondiente
    balota_objetivo = None
    for balota in root.findall('balota'):
        if balota.get('NUMERO') == numero:
            balota.set('ESTADO', numero)
            balota.set('ULTIMO', numero)
            balota_objetivo = balota

    # Si no se encontró la balota, retornar error
    if not balota_objetivo:
        return 'Número no encontrado', 404

    # Limpiar ULTIMO_NUMERO_GLOBAL en todas las balotas
    for balota in root.findall('balota'):
        balota.set('ULTIMO_NUMERO_GLOBAL', '')

    # Colocar el ULTIMO_NUMERO_GLOBAL solo en la primera balota
    primera_balota = root.find('balota')
    if primera_balota is not None:
        primera_balota.set('ULTIMO_NUMERO_GLOBAL', numero)

    tree.write(RUTA_XML, encoding='utf-8', xml_declaration=True)
    return 'Número guardado', 200

@app.route('/reset', methods=['POST'])
def reset():
    tree = ET.parse(RUTA_XML)
    root = tree.getroot()

    for balota in root.findall('balota'):
        balota.set('ESTADO', '')
        balota.set('ULTIMO', '')
        balota.set('ULTIMO_NUMERO_GLOBAL', '')

    tree.write(RUTA_XML, encoding='utf-8', xml_declaration=True)
    return 'Reseteado', 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
