import pickle
import json
import random

import rsa

from utils import encrypt, get_label, keys_to_int
from circuit import LogicCircuit
from config import ADDRESS, PORT, INPUT_CIRCUIT_FILENAME
import requests
from ot.next_prime import next_prime
from ot.ot import *

URL = "http://{0}:{1}/alice".format(ADDRESS, PORT)
OURL1 = "http://{0}:{1}/alice/ot1".format(ADDRESS, PORT)
OURL2 = "http://{0}:{1}/alice/ot2".format(ADDRESS, PORT)


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
        self._ot_messages = self._get_ot_messages()
        self._output = dict()

        self._ot_setup()

    def _ot_setup(self):
        (pubkey, private_key) = rsa.newkeys(RSA_bits)
        self.pubkey = pubkey
        self.private_key = private_key
        self.G = next_prime(self.pubkey.n)

        self.hashes = []

        for m in self._ot_messages:
            self.hashes.append(hasher(m))
        data = {
            "pubkey": json.dumps({"e": self.pubkey.e, "n": self.pubkey.n}),
            "hashes": json.dumps(self.hashes),
            "secret_length": json.dumps(len(self._ot_messages[0]))
        }

        response = requests.post(url=OURL1, data=data)

        string_f = json.loads(response.text)
        string_f = list(map(int, string_f))
        assert len(string_f) == len(self.circuit.bob_input_wires)

        G = []
        for i in range(len(self._ot_messages)):
            F = pow(compute_poly(string_f, i, self.G), self.private_key.d, self.pubkey.n)
            G.append((F * bytes_to_int(self._ot_messages[i])) % self.pubkey.n)

        response = requests.post(url=OURL2, json=G)

        self._output_labels = json.loads(response.text, object_pairs_hook=keys_to_int)

        for output_wire in self.circuit.output_wires:
            self._output.update({output_wire: self._wire_labels[output_wire].index(self._output_labels[output_wire])})

        print("Output is")
        print(self._output)

    def _get_ot_messages(self):
        messages = []
        for wire in self.circuit.wires:
            for i in range(2):
                message = (self._wire_labels[wire][i], self._p_bits[wire][i])
                pickle_message = pickle.dumps(message)
                messages.append(pickle_message)
        return messages

    def _send_garbled_circuit_data(self):
        data = {
            'garbled-gates': json.dumps(self._garbled_gates),
            'alice-input-labels': json.dumps(self._input_labels),
            'alice-input-pbits': json.dumps(self._input_pbits)
        }

        requests.post(url=URL, data=data)

    def _get_input(self):
        print("Enter Alice input bits :")
        while True:
            alice_input = list(map(int, input().split()))
            try:
                assert (len(alice_input) == len(self.circuit.alice_input_wires))
            except AssertionError:
                print("Alice input length doesn't match\nPlease try again!")
            else:
                break

        return {self.circuit.alice_input_wires[i]: alice_input[i] for i in range(len(self.circuit.alice_input_wires))}

    def _get_input_labels(self):
        input_labels = dict()
        for wire, bit in self._input.items():
            input_labels.update({wire: self._wire_labels[wire][bit]})
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
        return {wire: [get_label().decode(), get_label().decode()] for wire in self.circuit.wires}

    def _get_garbled_gates(self):
        garbled_gates = dict()
        for gate in self.circuit.gates:

            if gate.name == 'NOT':
                input_wire = gate.input_wires[0]
                output_wire = gate.output_wire

                garbled_gate = [None] * 2

                for input_bit in (0, 1):
                    label = self._wire_labels[input_wire][input_bit]
                    location = self._p_bits[input_wire][input_bit]
                    output_bit = gate.evaluate(input_bit)

                    output_label = self._wire_labels[output_wire][output_bit]
                    output_pbit = self._p_bits[output_wire][output_bit]

                    msg = pickle.dumps((output_label, output_pbit))

                    garbled_gate[location] = encrypt(msg, label).decode()

            else:
                input_wire1 = gate.input_wires[0]
                input_wire2 = gate.input_wires[1]
                output_wire = gate.output_wire

                garbled_gate = [None] * 4
                for input_bit1 in (0, 1):
                    for input_bit2 in (0, 1):
                        label1 = self._wire_labels[input_wire1][input_bit1]
                        label2 = self._wire_labels[input_wire2][input_bit2]

                        p_bit1 = self._p_bits[input_wire1][input_bit1]
                        p_bit2 = self._p_bits[input_wire2][input_bit2]
                        location = 2 * p_bit1 + p_bit2
                        output_bit = gate.evaluate(input_bit1, input_bit2)

                        output_label = self._wire_labels[output_wire][output_bit]
                        output_pbit = self._p_bits[output_wire][output_bit]

                        msg = pickle.dumps((output_label, output_pbit))

                        garbled_gate[location] = encrypt(encrypt(msg, label1), label2).decode()

            garbled_gates.update({gate.id: garbled_gate})

        return garbled_gates


if __name__ == "__main__":
    a = Alice()
