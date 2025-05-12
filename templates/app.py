from flask import Flask, render_template
from bingo.bingo_blueprint import bp_bingo
from figuras.figuras_blueprint import bp_figuras
from impresion.impresion_blueprint import bp_impresion

app = Flask(__name__, template_folder='templates', static_folder='static')

app.register_blueprint(bp_bingo)
app.register_blueprint(bp_figuras)
app.register_blueprint(bp_impresion)

@app.route('/')
def index():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
