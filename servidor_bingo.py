
from flask import Flask, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_folder='static')
XML_FILE = os.path.join(app.static_folder, 'xml')

@app.route("/")
def inicio():
    return send_from_directory(app.static_folder, "PANEL_BINGO_75.html")

def leer_xml():
    tree = ET.parse(XML_FILE)
    return tree, tree.getroot()

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.json.get("numero")
    if not numero:
        return jsonify({"error": "Número no proporcionado"}), 400

    tree, root = leer_xml()

    balotas = root.find("balotas")
    ultimos = root.find("ULTIMOS")
    ultimo_global = root.find("ULTIMO_NUMERO_GLOBAL")
    ultima_balota = root.find("ULTIMA_BALOTA")

    for balota in balotas.findall("balota"):
        if balota.get("NUMERO") == str(numero):
            balota.set("ESTADO", str(numero))
            balota.set("ULTIMO", str(numero))
        else:
            balota.set("ULTIMO", "")

    if ultimo_global is not None:
        ultimo_global.text = str(numero)

    if ultima_balota is not None:
        ultima_balota.set("NUMERO", str(numero))

    if ultimos is not None:
        historial = [b.get("NUMERO") for b in balotas.findall("balota") if b.get("ESTADO")]
        ultimos.text = ",".join(historial[-5:])

    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"mensaje": f"Número {numero} guardado correctamente"})

@app.route("/reset", methods=["POST"])
def resetear():
    tree, root = leer_xml()
    for balota in root.find("balotas").findall("balota"):
        balota.set("ESTADO", "")
        balota.set("ULTIMO", "")
    ultimo_global = root.find("ULTIMO_NUMERO_GLOBAL")
    if ultimo_global is not None:
        ultimo_global.text = "0"
    ultimos = root.find("ULTIMOS")
    if ultimos is not None:
        ultimos.text = ""
    ultima_balota = root.find("ULTIMA_BALOTA")
    if ultima_balota is not None:
        ultima_balota.set("NUMERO", "")
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return jsonify({"mensaje": "Reinicio completo"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
