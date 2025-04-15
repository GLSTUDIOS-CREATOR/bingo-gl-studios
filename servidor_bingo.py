from flask import Flask, request
import xml.etree.ElementTree as ET

app = Flask(__name__)
XML_PATH = "static/datos_bingo.xml"

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")
    if not numero:
        return "Número no proporcionado", 400
    numero = str(numero)

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    for balota in root.findall("balota"):
        if balota.attrib["NUMERO"] == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
        else:
            balota.set("ULTIMO", "")
    for b in root.findall("balota"):
        if b.attrib["NUMERO"] == "0":
            b.set("ULTIMO_NUMERO_GLOBAL", numero)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "OK"

@app.route("/resetear")
def resetear():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    for balota in root.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        if balota.attrib["NUMERO"] == "0":
            balota.set("ULTIMO_NUMERO_GLOBAL", "")
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Reset OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
