from uuid import uuid1

from flask import Flask, request, jsonify 
 
simulations = {}

app = Flask(__name__)


@app.route("/create_simulation", methods=["POST"])
def create_simulation_handler():
    """ Creates a simulation with the given parameters and returns an id to 
    further evolve the simulation
    """
    simulation_id = str(uuid1())

    return jsonify(
        id=simulation_id
    ) 

@app.route("/get_next_step", methods=["POST"])
def get_next_step_handler():
    """ Gets the next step of the simulation 
    """
    return jsonify()



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)