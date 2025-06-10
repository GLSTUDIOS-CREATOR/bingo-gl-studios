from flask import Blueprint, render_template, request, redirect, url_for, flash
import xml.etree.ElementTree as ET
import os

bp_usuarios = Blueprint('usuarios', __name__, template_folder='templates')
XML_PATH = os.path.join('static', 'data', 'usuarios.xml')

def leer_usuarios():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    usuarios = []
    for u in root.findall('usuario'):
        usuarios.append({'nombre': u.find('nombre').text, 'clave': u.find('clave').text})
    return usuarios

def guardar_usuarios(lista_usuarios):
    root = ET.Element('usuarios')
    for usuario in lista_usuarios:
        u = ET.SubElement(root, 'usuario')
        ET.SubElement(u, 'nombre').text = usuario['nombre']
        ET.SubElement(u, 'clave').text = usuario['clave']
    tree = ET.ElementTree(root)
    tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)

@bp_usuarios.route('/usuarios')
def panel_usuarios():
    usuarios = leer_usuarios()
    return render_template('usuarios_panel.html', usuarios=usuarios)

@bp_usuarios.route('/usuarios/agregar', methods=['POST'])
def agregar_usuario():
    usuarios = leer_usuarios()
    nombre = request.form['nombre'].strip()
    clave = request.form['clave'].strip()
    # Verifica que no se repita
    if any(u['nombre'].lower() == nombre.lower() for u in usuarios):
        flash('El usuario ya existe.', 'danger')
    else:
        usuarios.append({'nombre': nombre, 'clave': clave})
        guardar_usuarios(usuarios)
        flash('Usuario agregado exitosamente.', 'success')
    return redirect(url_for('usuarios.panel_usuarios'))

@bp_usuarios.route('/usuarios/editar/<nombre>', methods=['POST'])
def editar_usuario(nombre):
    usuarios = leer_usuarios()
    for u in usuarios:
        if u['nombre'].lower() == nombre.lower():
            u['nombre'] = request.form['nuevo_nombre'].strip()
            u['clave'] = request.form['nueva_clave'].strip()
            break
    guardar_usuarios(usuarios)
    flash('Usuario editado.', 'success')
    return redirect(url_for('usuarios.panel_usuarios'))

@bp_usuarios.route('/usuarios/eliminar/<nombre>', methods=['POST'])
def eliminar_usuario(nombre):
    usuarios = leer_usuarios()
    usuarios = [u for u in usuarios if u['nombre'].lower() != nombre.lower()]
    guardar_usuarios(usuarios)
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('usuarios.panel_usuarios'))
