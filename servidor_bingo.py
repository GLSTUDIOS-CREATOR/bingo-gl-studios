from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route("/xml", methods=["GET"])
def serve_xml():
    return send_from_directory("static", "datos_bingo.xml")

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.json.get("numero")
    tree = ET.parse("static/datos_bingo.xml")
    root = tree.getroot()

    balotas_padre = root.find("balotas")
    if balotas_padre is None:
        return "Estructura XML inválida: falta <balotas>", 500

    for balota in balotas_padre.findall("balota"):
        num = balota.find("NUMERO").text
        if num == str(numero):
            balota.find("ESTADO").text = str(numero)
            balota.find("ULTIMO").text = str(numero)
        else:
            balota.find("ULTIMO").text = ""

    # Actualizar el valor de <ULTIMO_NUMERO_GLOBAL> en la raíz
    ultimo_global = root.find("ULTIMO_NUMERO_GLOBAL")
    if ultimo_global is not None:
        ultimo_global.text = str(numero)

    tree.write("static/datos_bingo.xml", encoding="utf-8", xml_declaration=True)
    return "OK"

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse("static/datos_bingo.xml")
    root = tree.getroot()

    balotas_padre = root.find("balotas")
    if balotas_padre is None:
        return "Estructura XML inválida: falta <balotas>", 500

    for balota in balotas_padre.findall("balota"):
        balota.find("ESTADO").text = ""
        balota.find("ULTIMO").text = ""

    ultimo_global = root.find("ULTIMO_NUMERO_GLOBAL")
    if ultimo_global is not None:
        ultimo_global.text = ""

    tree.write("static/datos_bingo.xml", encoding="utf-8", xml_declaration=True)
    return "Reset completo"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
