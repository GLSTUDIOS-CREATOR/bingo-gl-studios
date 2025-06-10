import csv

# LAS COLUMNAS EXACTAS SEGÚN EL CARTÓN Y TU FIGURA
CAMPOS_LETRA_Y = ['b1', 'i2', 'n4', 'n5', 'g2', 'o1']

def leer_numeros_marcados(path_numeros):
    with open(path_numeros, 'r', encoding='utf-8') as f:
        contenido = f.read()
        numeros = []
        for parte in contenido.replace('\n', ',').split(','):
            parte = parte.strip()
            if parte.isdigit():
                numeros.append(int(parte))
        return numeros

def revisar_figura_letray(path_cartones, numeros_marcados):
    with open(path_cartones, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            id_carton = row.get('numero') or row.get('\ufeffnumero') or row.get('NUMERO') or ''
            numeros_figura = []
            for col in CAMPOS_LETRA_Y:
                valor = row.get(col)
                if valor and valor.strip().isdigit() and int(valor) != 0:
                    numeros_figura.append(int(valor))
            # DEBUG: imprime qué está comparando
            print(f"Cartón {id_carton}: valores figura Y -> {numeros_figura}")
            if all(num in numeros_marcados for num in numeros_figura):
                print(f"¡CARTÓN GANADOR POR LETRA Y! ID: {id_carton}")
                return id_carton
    print("Ningún cartón es ganador por figura LETRA Y.")
    return None

if __name__ == "__main__":
    path_cartones = "data/Srs_ib1.csv"
    path_numeros = "data/numeros_marcados.txt"
    numeros_marcados = leer_numeros_marcados(path_numeros)
    print(f"Números sorteados: {numeros_marcados}")
    revisar_figura_letray(path_cartones, numeros_marcados)
