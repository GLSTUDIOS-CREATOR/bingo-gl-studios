from flask import Flask, request, send_file
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

@app.route("/xml")
def servir_xml():
    return send_file("static/datos_bingo.xml")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")

    ruta_xml = os.path.join("static", "datos_bingo.xml")
    tree = ET.parse(ruta_xml)
    root = tree.getroot()

    balotas_nodo = root.find("balotas")
    if balotas_nodo is None:
        return "Estructura XML incorrecta (no hay nodo <balotas>)", 500

    for balota in balotas_nodo.findall("balota"):
        if balota.attrib["NUMERO"] == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
        else:
            balota.set("ULTIMO", "")

    primera_balota = balotas_nodo.findall("balota")[0]
    primera_balota.set("ULTIMO_NUMERO_GLOBAL", numero)

    tree.write(ruta_xml, encoding="utf-8", xml_declaration=True)
    return "OK"

@app.route("/reset", methods=["POST"])
def reset():
    ruta_xml = os.path.join("static", "datos_bingo.xml")
    tree = ET.parse(ruta_xml)
    root = tree.getroot()

    balotas_nodo = root.find("balotas")
    if balotas_nodo is None:
        return "Estructura XML incorrecta", 500

    for balota in balotas_nodo.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")

    primera = balotas_nodo.findall("balota")[0]
    primera.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(ruta_xml, encoding="utf-8", xml_declaration=True)
    return "RESET OK"

if __name__ == "__main__":
    app.run(debug=True)