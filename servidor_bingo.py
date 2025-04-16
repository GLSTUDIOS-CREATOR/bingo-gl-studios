
from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET

app = Flask(__name__, static_url_path='/static')
XML_PATH = "static/datos_bingo.xml"

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

    for balota in balotas:
        balota.set("ULTIMO_NUMERO_GLOBAL", "")
    if balotas:
        for balota in balotas:
            if balota.get("NUMERO") == numero:
                balota.set("ULTIMO_NUMERO_GLOBAL", numero)
                break

    tree.write(XML_PATH)
    return "OK", 200

@app.route("/resetear", methods=["POST"])
def resetear():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    for balota in root.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")
    tree.write(XML_PATH)
    return "Reset OK", 200

if __name__ == "__main__":
    app.run(debug=True)
