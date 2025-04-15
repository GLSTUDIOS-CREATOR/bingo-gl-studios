
from flask import Flask, request, jsonify, send_from_directory, send_file
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'datos_bingo.xml')

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'PANEL_BINGO_75.html')

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.json.get("numero")
    if not numero:
        return jsonify({"error": "Número no proporcionado"}), 400

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    ultimos = root.find("ultimos")
    if ultimos is None:
        ultimos = ET.SubElement(root, "ultimos")

    ultimo_global = root.find("ultimo_global")
    if ultimo_global is None:
        ultimo_global = ET.SubElement(root, "ultimo_global")

    balotas = root.find("balotas").findall("balota")

    for balota in balotas:
        if balota.get("NUMERO") == str(numero):
            balota.set("ESTADO", str(numero))
            balota.set("ULTIMO", str(numero))
        else:
            balota.set("ULTIMO", "")

    # Actualizar últimos 5
    historial = [b.get("NUMERO") for b in balotas if b.get("ESTADO")]
    ultimos.text = ",".join(historial[-5:])

    # Actualizar el último número global en la primera fila
    if balotas:
        balotas[0].set("ULTIMO_NUMERO_GLOBAL", str(numero))

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

@app.route("/reset", methods=["POST"])
def resetear():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    for balota in root.find("balotas").findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")

    ultimos = root.find("ultimos")
    if ultimos is not None:
        ultimos.text = ""

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

@app.route("/xml")
def servir_xml():
    return send_file(XML_FILE, mimetype="application/xml")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
