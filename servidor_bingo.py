
from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
XML_PATH = os.path.join("static", "datos_bingo.xml")

@app.route("/")
def index():
    return send_from_directory("static", "PANEL_BINGO_75.html")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")

    if not numero:
        return jsonify({"error": "Número no proporcionado"}), 400

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for balota in root.findall("balota"):
        num = balota.find("NUMERO").text
        if num == numero:
            balota.find("ESTADO").text = numero
            balota.find("ULTIMO").text = numero
        else:
            balota.find("ULTIMO").text = ""

    # Actualizar ULTIMO_NUMERO_GLOBAL en la primera balota solamente
    primera = root.findall("balota")[0]
    if primera.find("ULTIMO_NUMERO_GLOBAL") is not None:
        primera.find("ULTIMO_NUMERO_GLOBAL").text = numero

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return jsonify({"message": "Número guardado correctamente"})

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for balota in root.findall("balota"):
        balota.find("ESTADO").text = ""
        balota.find("ULTIMO").text = ""
        ultimo_global = balota.find("ULTIMO_NUMERO_GLOBAL")
        if ultimo_global is not None:
            ultimo_global.text = ""

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return jsonify({"message": "XML reseteado correctamente"})

@app.route("/xml")
def servir_xml():
    return send_from_directory("static", "datos_bingo.xml")

if __name__ == "__main__":
    app.run(debug=True)
