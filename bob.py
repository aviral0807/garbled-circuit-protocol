from circuit import LogicCircuit
from flask import Flask, request
from config import ADDRESS, PORT, INPUT_CIRCUIT_FILENAME
from utils import keys_to_int, decrypt
import json
import pickle


class Bob:
    def __init__(self):
        self.circuit = LogicCircuit(INPUT_CIRCUIT_FILENAME)
        self._garbled_gates = None
        self._input = self._get_input()
        self._alice_input_labels = None
        self._alice_input_pbits = None
        self._bob_input_labels = None
        self._bob_input_pbits = None
        self.wire_labels = None

        print(self._input.values())

        # server = Flask(__name__)

        @server.route('/alice', methods=['POST', 'GET'])
        def _get_garbled_circuit_data():
            self._garbled_gates = json.loads(request.form['garbled-gates'], object_pairs_hook=keys_to_int)
            self._alice_input_labels = json.loads(request.form['alice-input-labels'], object_pairs_hook=keys_to_int)
            self._alice_input_pbits = json.loads(request.form['alice-input-pbits'], object_pairs_hook=keys_to_int)

            wire_labels = json.loads(request.form['wire-labels'], object_pairs_hook=keys_to_int)
            self.wire_labels = wire_labels

            p_bits = json.loads(request.form['p-bits'], object_pairs_hook=keys_to_int)

            self._bob_input_labels = dict()
            self._bob_input_pbits = dict()

            for wire, bit in self._input.items():
                self._bob_input_labels.update({wire: wire_labels[wire][bit]})
                self._bob_input_pbits.update({wire: p_bits[wire][bit]})

            self.solve_circuit()
            return "ok"

        # server.run(ADDRESS, PORT)

    def _get_input(self):

        while True:
            bob_input = list(map(int, input().split()))
            try:
                assert (len(bob_input) == len(self.circuit.bob_input_wires))
            except AssertionError:
                print("Bob input length doesn't match\nPlease try again\n")
            else:
                break

        return {self.circuit.bob_input_wires[i]: bob_input[i] for i in range(len(self.circuit.bob_input_wires))}

    def solve_circuit(self):
        wire_label_table = dict()
        wire_pbits_table = dict()

        for wire, label in self._alice_input_labels.items():
            wire_label_table[wire] = label
        for wire, label in self._bob_input_labels.items():
            wire_label_table[wire] = label

        for wire, pbit in self._alice_input_pbits.items():
            wire_pbits_table[wire] = pbit
        for wire, pbit in self._bob_input_pbits.items():
            wire_pbits_table[wire] = pbit

        for gate in self.circuit.gates:
            if gate.name == 'NOT':
                input_wire1 = gate.input_wires[0]

                label1 = wire_label_table[input_wire1]

                location = wire_pbits_table[input_wire1]

                msg = self._garbled_gates[gate.id][location].encode()

                decrypted_msg = decrypt(msg, label1)
                output_label, output_pbit = pickle.loads(decrypted_msg)

                wire_label_table.update({gate.output_wire: output_label})
                wire_pbits_table.update({gate.output_wire: output_pbit})

            else:
                input_wire1 = gate.input_wires[0]
                input_wire2 = gate.input_wires[1]

                label1 = wire_label_table[input_wire1]
                label2 = wire_label_table[input_wire2]

                p_bit1 = wire_pbits_table[input_wire1]
                p_bit2 = wire_pbits_table[input_wire2]

                location = 2 * p_bit1 + p_bit2

                msg = self._garbled_gates[gate.id][location].encode()

                decrypted_msg = decrypt(decrypt(msg, label2), label1)
                output_label, output_pbit = pickle.loads(decrypted_msg)

                wire_label_table.update({gate.output_wire: output_label})
                wire_pbits_table.update({gate.output_wire: output_pbit})

        ans = []
        for output_wire in self.circuit.output_wires:
            ans.append(self.wire_labels[output_wire].index(wire_label_table[output_wire]))

        print(ans)


if __name__ == "__main__":
    server = Flask(__name__)
    b = Bob()
    server.run(ADDRESS, PORT)
