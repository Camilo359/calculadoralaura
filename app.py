from flask import Flask, request, send_file, render_template
import math
import numpy as np
import pandas as pd
import io
import os

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
    
        workbook = writer.book
        worksheet = writer.sheets['Resultados']
    
        # Crear los gráficos
        chart1 = workbook.add_chart({'type': 'line'})
        chart2 = workbook.add_chart({'type': 'line'})
    
        # Agregar datos a los gráficos
        # Rastreo vs O
        chart1.add_series({
            'name': 'Oxígeno disuelto (O)',
            'categories': ['Resultados', 1, 0, len(df), 0],  # x (m)
            'values':     ['Resultados', 1, 1, len(df), 1],  # O (mg/L)
            'line': {'color': 'blue'},
        })
        chart1.set_title({'name': 'Rastreo vs O'})
        chart1.set_x_axis({'name': 'Distancia (m)'})
        chart1.set_y_axis({'name': 'O (mg/L)'})
        chart1.set_style(10)
    
        # Rastreo vs L
        chart2.add_series({
            'name': 'Demanda Bioquímica de Oxígeno (L)',
            'categories': ['Resultados', 1, 0, len(df), 0],  # x (m)
            'values':     ['Resultados', 1, 2, len(df), 2],  # L (mg/L)
            'line': {'color': 'red'},
        })
        chart2.set_title({'name': 'Rastreo vs L'})
        chart2.set_x_axis({'name': 'Distancia (m)'})
        chart2.set_y_axis({'name': 'L (mg/L)'})
        chart2.set_style(10)
    
        # Insertar los gráficos en la hoja
        worksheet.insert_chart('E2', chart1, {'x_offset': 25, 'y_offset': 10})
        worksheet.insert_chart('E20', chart2, {'x_offset': 25, 'y_offset': 10})
    
    output.seek(0)
    return send_file(output, download_name="resultados.xlsx", as_attachment=True)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
