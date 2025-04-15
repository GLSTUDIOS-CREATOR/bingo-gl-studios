
from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__, static_url_path="/static")

XML_PATH = os.path.join("static", "datos_bingo.xml")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")
    if not numero:
        return "Número no proporcionado", 400

    try:
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        balotas_root = root.find("balotas")
        if balotas_root is None:
            return "Estructura del XML incorrecta", 500

        # Limpiar todos los campos "ULTIMO"
        for balota in balotas_root.findall("balota"):
            balota.find("ULTIMO").text = ""

        # Marcar el número y ponerlo como último
        for balota in balotas_root.findall("balota"):
            num_text = balota.find("NUMERO").text
            if num_text == numero:
                balota.find("ESTADO").text = numero
                balota.find("ULTIMO").text = numero
                break

        # Actualizar campo ULTIMO_NUMERO_GLOBAL en la primera fila
        ultimo_global = root.find("ULTIMO_NUMERO_GLOBAL")
        if ultimo_global is not None:
            ultimo_global.text = numero

        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
        return "OK", 200

    except Exception as e:
        return f"Error al guardar: {str(e)}", 500

@app.route("/reset", methods=["POST"])
def reset():
    try:
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        balotas_root = root.find("balotas")
        if balotas_root is None:
            return "Estructura del XML incorrecta", 500

        for balota in balotas_root.findall("balota"):
            balota.find("ESTADO").text = ""
            balota.find("ULTIMO").text = ""

        ultimo_global = root.find("ULTIMO_NUMERO_GLOBAL")
        if ultimo_global is not None:
            ultimo_global.text = ""

        tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
        return "Reseteado", 200
    except Exception as e:
        return f"Error al resetear: {str(e)}", 500

@app.route("/")
def index():
    return send_from_directory("static", "PANEL_BINGO_75.html")

if __name__ == "__main__":
    app.run(debug=True)
