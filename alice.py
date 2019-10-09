import pickle
import json
import random
from utils import encrypt, get_label
from circuit import LogicCircuit
from config import ADDRESS, PORT, INPUT_CIRCUIT_FILENAME
import requests

URL = "http://{0}:{1}/alice".format(ADDRESS, PORT)


class Alice:
    def __init__(self):
        self.circuit = LogicCircuit(INPUT_CIRCUIT_FILENAME)
        self._p_bits = self._generate_pbits()
        self._wire_labels = self._generate_wire_labels()
        self._garbled_gates = self._get_garbled_gates()
        self._input = self._get_input()
        self._input_labels = self._get_input_labels()
        self._input_pbits = self._get_input_pbits()
        self._send_garbled_circuit_data()

    def _send_garbled_circuit_data(self):
        data = {
            'garbled-gates': json.dumps(self._garbled_gates),
            'alice-input-labels': json.dumps(self._input_labels),
            'alice-input-pbits': json.dumps(self._input_pbits)
        }

        r = requests.post(url=URL, data=data)
        print(r.text)

    def _get_input(self):
        return {wire: random.randint(0, 1) for wire in self.circuit.alice_input_wires}

    def _get_input_labels(self):
        input_labels = dict()
        for wire, bit in self._input.items():
            input_labels.update({wire: self._wire_labels[wire][bit].decode()})
        return input_labels

    def _get_input_pbits(self):
        input_pbits = dict()
        for wire, bit in self._input.items():
            input_pbits.update({wire: self._p_bits[wire][bit]})
        return input_pbits

    def _generate_pbits(self):
        p_bits = dict()
        for wire in self.circuit.wires:
            rand_int = random.randint(0, 1)
            p_bits.update({wire: [rand_int, int(not rand_int)]})

        return p_bits

    def _generate_wire_labels(self):
        return {wire: [get_label(), get_label()] for wire in self.circuit.wires}

    def _get_garbled_gates(self):
        garbled_gates = dict()
        for gate in self.circuit.gates:

            if gate.name == 'NOT':
                input_wire = gate.input_wires[0]
                garbled_gate = [None] * 2

                for input_bit in (0, 1):
                    label = self._wire_labels[input_wire][input_bit]
                    location = self._p_bits[input_wire][input_bit]
                    output_bit = gate.evaluate(input_bit)
                    msg = pickle.dumps(output_bit)
                    garbled_gate[location] = encrypt(msg, label).decode()

            else:
                input_wire1 = gate.input_wires[0]
                input_wire2 = gate.input_wires[1]

                garbled_gate = [None] * 4
                for input_bit1 in (0, 1):
                    for input_bit2 in (0, 1):
                        label1 = self._wire_labels[input_wire1][input_bit1]
                        label2 = self._wire_labels[input_wire2][input_bit2]

                        p_bit1 = self._p_bits[input_wire1][input_bit1]
                        p_bit2 = self._p_bits[input_wire2][input_bit2]
                        location = 2 * p_bit1 + p_bit2

                        output_bit = gate.evaluate(input_bit1, input_bit2)
                        msg = pickle.dumps(output_bit)
                        garbled_gate[location] = encrypt(encrypt(msg, label1), label2).decode()

            garbled_gates.update({gate.id: garbled_gate})

        return garbled_gates


if __name__ == "__main__":
    a = Alice()
