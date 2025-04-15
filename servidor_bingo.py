
from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

XML_PATH = os.path.join("static", "datos_bingo.xml")

@app.route("/xml")
def serve_xml():
    return send_from_directory("static", "datos_bingo.xml")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.json.get("numero")
    if numero is None:
        return jsonify({"error": "Número no proporcionado"}), 400

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    balotas = root.findall("balota")
    for balota in balotas:
        num = balota.find("NUMERO").text
        if num == str(numero):
            balota.find("ESTADO").text = str(numero)
            balota.find("ULTIMO").text = str(numero)
        else:
            balota.find("ULTIMO").text = ""

    # Actualiza la primera línea con el ULTIMO_NUMERO_GLOBAL
    for elem in root.findall("ULTIMO_NUMERO_GLOBAL"):
        elem.text = str(numero)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return jsonify({"message": "Número guardado correctamente"})

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for balota in root.findall("balota"):
        balota.find("ESTADO").text = ""
        balota.find("ULTIMO").text = ""

    for elem in root.findall("ULTIMO_NUMERO_GLOBAL"):
        elem.text = ""

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return jsonify({"message": "XML reseteado correctamente"})

if __name__ == "__main__":
    app.run(debug=True)
