from flask import Flask, request
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

    balotas = root.findall("balota")
    for balota in balotas:
        if balota.get("NUMERO") == numero:
            balota.set("ESTADO", numero)
            balota.set("ULTIMO", numero)
        else:
            balota.set("ULTIMO", "")

    # Establecer el último número global solo en la primera balota
    if balotas:
        balotas[0].set("ULTIMO_NUMERO_GLOBAL", numero)
        for balota in balotas[1:]:
            balota.set("ULTIMO_NUMERO_GLOBAL", "")

    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    return "Guardado exitosamente", 200

if __name__ == "__main__":
    app.run(debug=True)
