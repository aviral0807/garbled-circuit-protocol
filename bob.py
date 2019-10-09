from circuit import LogicCircuit
from flask import Flask, request
from config import ADDRESS, PORT
import json

INPUT_CIRCUIT_FILENAME = 'input_circuit.json'


class Bob:
    def __init__(self):
        self.circuit = LogicCircuit(INPUT_CIRCUIT_FILENAME)
        self._garbled_gates = None
        self._alice_input_labels = None
        self._alice_input_pbits = None
        self._bob_input_labels = None
        self._bob_input_pbits = None

        server = Flask(__name__)

        @server.route('/alice', methods=['POST'])
        def _get_garbled_circuit_data():

            self._garbled_gates = json.loads(request.form['garbled-gates'])
            self._alice_input_labels = json.loads(request.form['alice-input-labels'])
            self._alice_input_pbits = json.loads(request.form['alice-input-pbits'])

            print(self._garbled_gates)
            print(self._alice_input_labels)
            print(self._alice_input_pbits)

            return "ok"

        server.run(ADDRESS, PORT)


if __name__ == "__main__":
    b = Bob()
