
from flask import Flask, request, send_from_directory
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
XML_FILE = os.path.join(app.root_path, 'static', 'datos_bingo.xml')

def actualizar_ultimo_global(root, numero):
    # Crear nodo si no existe
    if root.find("balota/ULTIMO_NUMERO_GLOBAL") is None:
        balota_global = ET.Element("balota")
        ultimo_global = ET.Element("ULTIMO_NUMERO_GLOBAL")
        ultimo_global.text = str(numero)
        balota_global.append(ultimo_global)
        root.insert(0, balota_global)
    else:
        root.find("balota/ULTIMO_NUMERO_GLOBAL").text = str(numero)

@app.route("/guardar", methods=["POST"])
def guardar():
    numero = request.form.get("numero")
    if not numero:
        return "Número no recibido", 400

    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    balotas = root.findall("balota")[1:]  # Saltamos la primera fila global

    # Marcar la balota correspondiente
    for balota in balotas:
        num = balota.find("NUMERO").text
        if num == numero:
            balota.find("ESTADO").text = numero
            balota.find("ULTIMO").text = numero
        else:
            balota.find("ULTIMO").text = ""

    actualizar_ultimo_global(root, numero)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return "OK", 200

@app.route("/reset", methods=["POST"])
def reset():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    balotas = root.findall("balota")[1:]  # Saltamos la primera fila global

    for balota in balotas:
        balota.find("ESTADO").text = ""
        balota.find("ULTIMO").text = ""

    actualizar_ultimo_global(root, "")
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
    return "Reset OK", 200

@app.route("/xml")
def xml():
    return send_from_directory("static", "datos_bingo.xml")

if __name__ == "__main__":
    app.run(debug=True)
