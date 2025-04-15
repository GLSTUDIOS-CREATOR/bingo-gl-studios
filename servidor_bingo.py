from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

XML_PATH = os.path.join("static", "datos_bingo.xml")

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        data = request.json
        numero = str(data.get("numero"))

        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        balotas = root.findall("balota")

        for balota in balotas:
            if balota.get("NUMERO") == numero:
                balota.set("ESTADO", numero)
                balota.set("ULTIMO", numero)
            else:
                balota.set("ULTIMO", "")

        # Ultimo numero global
        for balota in balotas:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")
        if balotas:
            balotas[0].set("ULTIMO_NUMERO_GLOBAL", numero)

        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/reset", methods=["POST"])
def reset():
    try:
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        for balota in root.findall("balota"):
            balota.set("ESTADO", "")
            balota.set("ULTIMO", "")
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
        return {"status": "reseteado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/xml")
def xml():
    return send_from_directory("static", "datos_bingo.xml")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
