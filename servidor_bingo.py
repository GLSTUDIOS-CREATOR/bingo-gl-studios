from flask import Flask, request, send_file
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

XML_PATH = "static/datos_bingo.xml"

@app.route("/")
def index():
    return send_file("static/PANEL_BINGO_75.html")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")
    if not numero:
        return "Número no proporcionado", 400

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    balotas = root.findall("balota")

    for balota in balotas:
        balota.set("ULTIMO", "")

    for balota in balotas:
        if balota.get("NUMERO") == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
        else:
            balota.set("ESTADO", balota.get("ESTADO") or "")

    if balotas:
        balotas[0].set("ULTIMO_NUMERO_GLOBAL", numero)
        for balota in balotas[1:]:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Actualizado", 200

@app.route("/resetear", methods=["POST"])
def resetear():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    balotas = root.findall("balota")
    for balota in balotas:
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Reset completado", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
