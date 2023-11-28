from model import TrainModel, TrainDescription, StationDescription
from model.serializer import serialize_model

modelo = TrainModel(
    TrainDescription(10, 10),
    [
        StationDescription((10, 0), 10),
        StationDescription((20, 0), 10),
        StationDescription((30, 0), 10)
    ]
)

from uuid import uuid1

from flask import Flask, request, jsonify 

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

    
    return jsonify(
        simulationId=simulation_id
    ) 

@app.route("/get_next_step", methods=["POST"])
def get_next_step_handler():
    """ Gets the next step of the simulation 
    """
    data = serialize_model(modelo)
    modelo.step()
    return jsonify(
        **data
    )

if __name__ == '__main__':
    app.run(debug=True)
