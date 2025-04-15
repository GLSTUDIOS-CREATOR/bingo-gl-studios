from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_url_path='', static_folder='static')
XML_PATH = os.path.join(os.path.dirname(__file__), 'static', 'datos_bingo.xml')

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "PANEL_BINGO_75.html")

@app.route("/xml")
def xml():
    return send_from_directory(app.static_folder, "datos_bingo.xml")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.json.get("numero")

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    balotas_container = root.find("balotas")
    if balotas_container is None:
        return "Estructura XML inválida", 500

    balotas = balotas_container.findall("balota")

    for balota in balotas:
        if balota.get("NUMERO") == str(numero):
            balota.set("ESTADO", str(numero))
            balota.set("ULTIMO", str(numero))
        else:
            balota.set("ULTIMO", "")

    # Limpiar ULTIMO_NUMERO_GLOBAL de todas las balotas
    for balota in balotas:
        if "ULTIMO_NUMERO_GLOBAL" in balota.attrib:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

    # Establecer el nuevo número en la primera balota como ULTIMO_NUMERO_GLOBAL
    balotas[0].set("ULTIMO_NUMERO_GLOBAL", str(numero))

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    balotas_container = root.find("balotas")
    if balotas_container is None:
        return "Estructura XML inválida", 500

    for balota in balotas_container.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        if "ULTIMO_NUMERO_GLOBAL" in balota.attrib:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
