
from flask import Flask, request, jsonify, send_from_directory
import csv
import os

app = Flask(__name__, static_folder='static')
CSV_FILE = os.path.join(app.static_folder, 'datos_bingo.csv')

def leer_datos():
    datos = []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            datos.append(fila)
    return datos

def escribir_datos(datos):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['NUMERO', 'ESTADO', 'ULTIMO', 'ULTIMO_NUMERO_GLOBAL']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(datos)

@app.route('/')
def inicio():
    return send_from_directory(app.static_folder, 'PANEL_BINGO_75.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    numero = request.json.get('numero')
    datos = leer_datos()
    for fila in datos:
        if fila['NUMERO'] == str(numero):
            fila['ESTADO'] = str(numero)
            fila['ULTIMO'] = str(numero)
        else:
            fila['ULTIMO'] = ''
    for fila in datos:
        fila['ULTIMO_NUMERO_GLOBAL'] = str(numero) if fila == datos[0] else ''
    escribir_datos(datos)
    return jsonify({'ok': True})

@app.route('/resetear', methods=['POST'])
def resetear():
    datos = leer_datos()
    for fila in datos:
        fila['ESTADO'] = '0'
        fila['ULTIMO'] = ''
        fila['ULTIMO_NUMERO_GLOBAL'] = '' if fila != datos[0] else '0'
    escribir_datos(datos)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)
