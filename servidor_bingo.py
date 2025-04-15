
from flask import Flask, request, send_file
import xml.etree.ElementTree as ET

app = Flask(__name__)
XML_PATH = "static/datos_bingo.xml"

@app.route("/")
def home():
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
        if balota.get("NUMERO") == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
        else:
            balota.set("ULTIMO", "")

    # Asignar último número global en la primera balota
    if balotas:
        balotas[0].set("ULTIMO_NUMERO_GLOBAL", numero)
        for b in balotas[1:]:
            b.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Guardado OK"

@app.route("/resetear", methods=["POST"])
def resetear():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    for balota in root.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Reset OK"

@app.route("/xml")
def ver_xml():
    return send_file(XML_PATH)
