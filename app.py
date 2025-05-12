from flask import Flask, render_template, request, jsonify
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

XML_PATH = os.path.join('static', 'datos_bingo.xml')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/marcar_numero', methods=['POST'])
def marcar_numero():
    numero = request.json['numero']
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    numeros = root.find('numeros')
    ultimos5 = root.find('ultimos5')
    totalMarcados_el = root.find('totalMarcados')

    marcado_actual = False

    for num in numeros.findall('numero'):
        if num.get('valor') == numero:
            if num.get('marcado') == '0':
                num.set('marcado', numero)
                marcado_actual = True
            else:
                num.set('marcado', '0')
                marcado_actual = False
            break

    ultimo_global = root.find('ultimo_numero')
    if ultimo_global is None:
        ultimo_global = ET.SubElement(root, 'ultimo_numero')

    if marcado_actual:
        ultimo_global.text = numero
    else:
        ultimo_global.text = ''

    ultimos_numeros = ultimos5.text.split(',') if ultimos5.text else []

    if marcado_actual:
        ultimos_numeros.insert(0, numero)
        ultimos_numeros = ultimos_numeros[:5]
    else:
        if numero in ultimos_numeros:
            ultimos_numeros.remove(numero)

    ultimos5.text = ','.join(ultimos_numeros)
    total_marcados = sum(1 for n in numeros.findall('numero') if n.get('marcado') != '0')
    totalMarcados_el.text = str(total_marcados)

    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)

    return jsonify({
        'marcado': marcado_actual,
        'totalMarcados': total_marcados,
        'ultimos5': ultimos_numeros,
        'ultimo_numero': ultimo_global.text
    })
@app.route('/resetear', methods=['POST'])
def resetear():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for num in root.find('numeros').findall('numero'):
        num.set('marcado', '')

    root.find('ultimos5').text = ''
    root.find('totalMarcados').text = '0'
    ultimo = root.find('ultimo_numero')
    if ultimo is not None:
        ultimo.text = ''

    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)