
from flask import Flask, request, send_from_directory
import csv
import os

app = Flask(__name__, static_folder='static')

CSV_FILE = os.path.join('static', 'datos_bingo.csv')

@app.route('/')
def home():
    return send_from_directory('static', 'PANEL_BINGO_75.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.json.get('numero')
    estado = request.json.get('estado')

    if numero is None or estado is None:
        return {'mensaje': 'Datos incompletos'}, 400

    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        datos = list(reader)

    for fila in datos:
        if fila['NUMERO'] == str(numero):
            fila['ESTADO'] = str(numero) if estado else '0'

    for fila in datos:
        fila['ULTIMO'] = str(numero) if fila['NUMERO'] == str(numero) and estado else '0'

    for i, fila in enumerate(datos):
        fila['ULTIMO_NUMERO_GLOBAL'] = str(numero) if i == 0 and estado else ''

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['NUMERO', 'ESTADO', 'ULTIMO', 'ULTIMO_NUMERO_GLOBAL'])
        writer.writeheader()
        writer.writerows(datos)

    return {'mensaje': 'Guardado exitosamente'}

@app.route('/resetear', methods=['POST'])
def resetear():
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        datos = list(reader)

    for fila in datos:
        fila['ESTADO'] = '0'
        fila['ULTIMO'] = '0'
        fila['ULTIMO_NUMERO_GLOBAL'] = ''

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['NUMERO', 'ESTADO', 'ULTIMO', 'ULTIMO_NUMERO_GLOBAL'])
        writer.writeheader()
        writer.writerows(datos)

    return {'mensaje': 'Reinicio exitoso'}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
