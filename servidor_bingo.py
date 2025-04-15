from flask import Flask, request, send_file
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
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
        if balota.get("NUMERO") == numero:
            balota.set("ULTIMO_NUMERO_GLOBAL", numero)
        else:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "OK"

@app.route("/xml")
def xml():
    return send_file(XML_PATH, mimetype="application/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Aquí está el cambio clave
    app.run(host="0.0.0.0", port=port)
