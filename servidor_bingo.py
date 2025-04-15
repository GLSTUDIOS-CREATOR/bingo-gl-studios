from flask import Flask, request, send_file
import xml.etree.ElementTree as ET

app = Flask(__name__)

XML_PATH = "static/datos_bingo.xml"

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")
    if not numero:
        return "Número no proporcionado", 400

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    balota = root.findall("balota")
    for balota in balota:
        if balota.get("NUMERO") == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
        else:
            balota.set("ULTIMO", "")

    # Actualizar ULTIMO_NUMERO_GLOBAL en la primera balota
    if balota:
        for b in balota:
            b.set("ULTIMO_NUMERO_GLOBAL", "")
        balota[0].set("ULTIMO_NUMERO_GLOBAL", numero)

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Guardado"

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for balota in root.findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
        balota.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Reseteado"

@app.route("/xml", methods=["GET"])
def obtener_xml():
    return send_file(XML_PATH, mimetype="application/xml")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
