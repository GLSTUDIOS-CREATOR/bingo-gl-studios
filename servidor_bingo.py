
from flask import Flask, request, jsonify, send_from_directory
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

XML_FILE = "static/datos_bingo.xml"

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.json.get("numero")
    if numero is None:
        return jsonify({"error": "Número no proporcionado"}), 400

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    # Marcar el estado y el último del número seleccionado
    balotas = root.find("balotas")
    for balota in balotas.findall("balota"):
        num = balota.find("NUMERO").text
        if num == str(numero):
            balota.find("ESTADO").text = str(numero)
            balota.find("ULTIMO").text = str(numero)
        else:
            balota.find("ULTIMO").text = ""

    # Actualizar el valor del ULTIMO_NUMERO_GLOBAL (en la primera balota)
    primera_balota = balotas.find("balota")
    if primera_balota is not None:
        ultimo_global = primera_balota.find("ULTIMO_NUMERO_GLOBAL")
        if ultimo_global is None:
            ultimo_global = ET.SubElement(primera_balota, "ULTIMO_NUMERO_GLOBAL")
        ultimo_global.text = str(numero)

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True}), 200

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    balotas = root.find("balotas")
    for balota in balotas.findall("balota"):
        balota.find("ESTADO").text = ""
        balota.find("ULTIMO").text = ""
    primera_balota = balotas.find("balota")
    if primera_balota is not None:
        ultimo_global = primera_balota.find("ULTIMO_NUMERO_GLOBAL")
        if ultimo_global is not None:
            ultimo_global.text = ""

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True}), 200

@app.route("/xml")
def servir_xml():
    return send_from_directory("static", "datos_bingo.xml")

if __name__ == "__main__":
    app.run(debug=True)
