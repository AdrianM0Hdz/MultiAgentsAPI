from uuid import uuid1

from flask import Flask, request, jsonify 

from model import Mapa

simulations = {}

app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def index():
    return "Hola equipo"

@app.route("/create_simulation", methods=["POST"])
def create_simulation_handler():
    """ Creates a simulation with the given parameters and returns an id to 
    further evolve the simulation
    """
    data = request.get_json() 
    if not data:
        return jsonify(
            msg="no json body given"
        ), 400
    simulation_id = str(uuid1())
    
    estaciones = data["estaciones"]
    estacion_size = data["estacionSize"]
    steps_de_espera = data["stepsDeEspera"]
    capacidad_vagon = data["capacidadVagon"]
    personas_en_estacion = data["personasEnEstacion"]

    simulations[simulation_id] = Mapa(estaciones, estacion_size, 
                                      steps_de_espera, capacidad_vagon, 
                                      personas_en_estacion)
    
    return jsonify(
        simulationId=simulation_id
    ) 

@app.route("/get_next_step", methods=["POST"])
def get_next_step_handler():
    """ Gets the next step of the simulation 
    """
    data = request.get_json() 
    if not data:
        return jsonify(
            msg="no json body given"
        ), 400
    simulation_id = str(data["simulationId"])

    simulation = simulations[simulation_id]
    datos = simulation.agregarDatosAlJson()

    # serlializamos los datos

    estaciones = []
    vagones = []
    personas = []

    for key in datos: 
        if "Estacion" in key: 
            estaciones.append(datos[key])
        elif "Vagon" in key: 
            vagones.append(datos[key])
        else: 
            personas.append(datos[key])
    
    simulation.step()
    
    return jsonify(
        estaciones=estaciones,
        vagones=vagones, 
        personas=personas
    )

if __name__ == '__main__':
    app.run(debug=True)
