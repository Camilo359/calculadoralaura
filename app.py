from flask import Flask, request, send_file, render_template
import math
import numpy as np
import pandas as pd
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    # Obtener datos del formulario
    caudal_rio = float(request.form['caudal_rio'])
    dbo_rio = float(request.form['dbo_rio'])
    oxigeno_disuelto_rio = float(request.form['oxigeno_disuelto_rio'])
    oxigeno_saturacion_rio = float(request.form['oxigeno_saturacion_rio'])
    velocidad_rio = float(request.form['velocidad_rio'])
    ancho_rio = float(request.form['ancho_rio'])
    profundidad_rio = float(request.form['profundidad_rio'])

    caudal_vertimiento = float(request.form['caudal_vertimiento'])
    dbo_vertimiento = float(request.form['dbo_vertimiento'])
    oxigeno_vertimiento = float(request.form['oxigeno_vertimiento'])

    caudal_despues = float(request.form['caudal_despues'])
    dbo_despues = float(request.form['dbo_despues'])
    oxigeno_despues = float(request.form['oxigeno_despues'])

    kd = float(request.form['kd'])
    ka = float(request.form['ka'])

    x = float(request.form['x'])
    salto_rastreo = float(request.form['salto_rastreo'])

    puntos_rastreo = np.arange(0, x + salto_rastreo, salto_rastreo)

    resultados1 = []
    resultados2 = []

    for X2 in puntos_rastreo:
        try:
            # Ecuación 1
            termino1 = (kd / (ka - kd))
            exp1 = math.exp(-kd * X2 / (velocidad_rio * 86400))
            exp2 = math.exp(-ka * X2 / (velocidad_rio * 86400))
            parte1 = termino1 * (exp1 - exp2) * dbo_despues
            parte2 = (oxigeno_saturacion_rio - oxigeno_despues) * math.exp(-ka * X2 / (velocidad_rio * 86400))
            resultado1 = oxigeno_saturacion_rio - parte1 - parte2
        except ZeroDivisionError:
            resultado1 = float('nan')

        try:
            # Ecuación 2
            resultado2 = dbo_despues * math.exp(-(kd * X2) / (velocidad_rio * 86400))
        except ZeroDivisionError:
            resultado2 = float('nan')

        resultados1.append(resultado1)
        resultados2.append(resultado2)

    # Crear DataFrame y Excel
    df = pd.DataFrame({
        'x (m)': puntos_rastreo,
        'O (mg/L)': resultados1,
        'L (mg/l)': resultados2
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    output.seek(0)

    return send_file(output, download_name="resultados.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
