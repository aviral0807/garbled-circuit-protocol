import json
import pickle

from flask import Flask, request

from circuit import LogicCircuit
from config import ADDRESS, PORT, INPUT_CIRCUIT_FILENAME
from utils.crypto import decrypt, rand_int, hasher
from utils.next_prime import next_prime
from utils.ot import lagrange, strip_padding, int_to_bytes
from utils.util import keys_to_int, mod_div


class Bob:
    def __init__(self):
        self.circuit = LogicCircuit(INPUT_CIRCUIT_FILENAME)
        self._input = self._get_input()
        
        self._garbled_gates = None
        
        self._alice_input_labels = None
        self._alice_input_pbits = None
        
        self._bob_input_labels = dict()
        self._bob_input_pbits = dict()
        
        self._ot_request_list = self._get_ot_request_list()
        self._R = []
        self._pubkey = None
        self._hashes = None
        self._secret_length = None
        
        self._output_labels = list()
        self._output = None

        @server.route('/alice/garbled-circuit', methods=['POST'])
        def _get_garbled_circuit_data():
            self._garbled_gates = json.loads(request.form['garbled-gates'], object_pairs_hook=keys_to_int)

            self._alice_input_labels = json.loads(request.form['alice-input-labels'], object_pairs_hook=keys_to_int)
            self._alice_input_pbits = json.loads(request.form['alice-input-pbits'], object_pairs_hook=keys_to_int)
            return "ok"

        @server.route('/alice/output', methods=['POST'])
        def _get_output():
            self._output = request.json
            print("Output is")
            print(self._output)

            return "ok"

        @server.route('/alice/ot1', methods=['POST'])
        def _get_oblivious_transfer_data1():
            self._pubkey = json.loads(request.form['pubkey'])
            self._hashes = json.loads(request.form['hashes'])
            self._secret_length = json.loads(request.form['secret_length'])

            t = []
            for j in range(len(self._ot_request_list)):
                r = rand_int(self._pubkey['n'])
                self._R.append(r)
                t.append(pow(r, self._pubkey['e'], self._pubkey['n']))  # the encrypted random value

            g = next_prime(self._pubkey['n'])
            f = lagrange(self._ot_request_list, t, g)

            string_f = json.dumps([str(x) for x in f])

            return string_f

        @server.route('/alice/ot2', methods=['POST'])
        def _get_oblivious_transfer_data2():
            g = request.json
            # print(g)
            decrypted = []
            for j in range(len(self._ot_request_list)):
                d = mod_div(g[self._ot_request_list[j]], self._R[j], self._pubkey['n'])
                dec_bytes = int_to_bytes(d)
                decrypted.append(strip_padding(dec_bytes, self._secret_length))

                if hasher(decrypted[j]) != self._hashes[self._ot_request_list[j]]:
                    print("Hashes don't match. Either something messed up or Alice is up to something.")

            self.decrypted = [pickle.loads(byte_tuple) for byte_tuple in decrypted]

            for i, data in enumerate(self.decrypted):
                label, pbit = data
                self._bob_input_labels.update({self.circuit.bob_input_wires[i]: label})
                self._bob_input_pbits.update({self.circuit.bob_input_wires[i]: pbit})

            self.solve_circuit()

            response = json.dumps(self._output_labels)
            return response

    def _get_ot_request_list(self):
        request_list = []
        for wire, bit in self._input.items():
            request_list.append(2 * (wire - 1) + bit)
        return request_list

    def _get_input(self):
        print("Enter Bob input bits :")
        while True:
            bob_input = list(map(int, input().split()))
            try:
                assert (len(bob_input) == len(self.circuit.bob_input_wires))
            except AssertionError:
                print("Bob input length doesn't match\nPlease try again!")
            else:
                break

        return {self.circuit.bob_input_wires[i]: bob_input[i] for i in range(len(self.circuit.bob_input_wires))}

    def solve_circuit(self):
        wire_label_table = {**self._alice_input_labels, **self._bob_input_labels}
        wire_pbits_table = {**self._alice_input_pbits, **self._bob_input_pbits}

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

        self._output_labels = {output_wire: wire_label_table[output_wire] for output_wire in self.circuit.output_wires}


if __name__ == "__main__":
    server = Flask(__name__)
    b = Bob()
    server.run(ADDRESS, PORT)
