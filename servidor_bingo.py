
from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

XML_PATH = os.path.join("static", "datos_bingo.xml")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")
    if not numero:
        return "Número no recibido", 400

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    # Resetear atributos anteriores
    for balota in root.findall("balota"):
        if balota.attrib.get("ULTIMO") == numero:
            balota.set("ULTIMO", "")
        if balota.attrib.get("ULTIMO_NUMERO_GLOBAL") == numero:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

    # Actualizar balota marcada
    for balota in root.findall("balota"):
        if balota.get("NUMERO") == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
            balota.set("ULTIMO_NUMERO_GLOBAL", numero)
            break

    # Limpiar los últimos 5 y agregar el nuevo al final
    ultimos = root.findall("ultimo")
    if len(ultimos) >= 5:
        root.remove(ultimos[0])
    nuevo = ET.Element("ultimo")
    nuevo.text = numero
    root.append(nuevo)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Guardado", 200

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for balota in root.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")

    for ultimo in root.findall("ultimo"):
        root.remove(ultimo)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Reset completo", 200

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/")
def inicio():
    return send_from_directory(".", "PANEL_BINGO_75.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
