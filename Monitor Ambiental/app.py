from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from threading import Thread
import time
import requests
from flask_cors import CORS
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
CORS(app)  # Permite CORS

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datos_sensor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Lectura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float, nullable=False)
    humedad = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

@app.before_request
def iniciar_bd_y_hilo():
    db.create_all()
    thread = Thread(target=consultar_arduino_periodicamente)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    # Asume que index.html está en la misma carpeta que app.py
    return send_from_directory('.', 'index.html')

@app.route('/datos', methods=['GET'])
def obtener_datos():
    lectura = Lectura.query.order_by(Lectura.fecha.desc()).first()
    if lectura:
        return jsonify({
            "temperatura": lectura.temperatura,
            "humedad": lectura.humedad,
            "fecha": lectura.fecha.isoformat()
        })
    else:
        return jsonify({"temperatura": None, "humedad": None, "fecha": None})
    
@app.route('/reporte', methods=['GET'])
def generar_reporte():
    # Consultar los últimos 50 registros ordenados del más reciente al más antiguo
    lecturas = Lectura.query.order_by(Lectura.fecha.desc()).limit(50).all()

    # Opcional: invertir para que queden del más antiguo al más reciente en el CSV
    lecturas.reverse()

    from io import StringIO
    import csv
    from flask import Response

    si = StringIO()
    cw = csv.writer(si)

    # Encabezados
    cw.writerow(['Fecha', 'Temperatura', 'Humedad'])

    for lec in lecturas:
        cw.writerow([lec.fecha.isoformat(), lec.temperatura, lec.humedad])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=reporte.csv"}
    )

def consultar_arduino_periodicamente():
    ip_arduino = "http://172.20.10.2"
    intervalo = 10
    while True:
        try:
            respuesta = requests.get(ip_arduino, timeout=5)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                temp = datos.get('temperatura')
                hum = datos.get('humedad')
                if temp is not None and hum is not None:
                    with app.app_context():
                        lectura = Lectura(temperatura=temp, humedad=hum)
                        db.session.add(lectura)
                        db.session.commit()
                        print(f"Guardado: Temp={temp}, Hum={hum}")
            else:
                print(f"Error consulta Arduino: {respuesta.status_code}")
        except Exception as e:
            print(f"Error petición Arduino: {e}")
        time.sleep(intervalo)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)