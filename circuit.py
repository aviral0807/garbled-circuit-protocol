import json


class LogicGate:
    def __init__(self, name, input_wires, output_wire):
        self.name = name
        self.input_wires = input_wires
        self.output_wire = output_wire
        self.id = self.output_wire

        switch = {
            "OR": lambda b1, b2: b1 or b2,
            "AND": lambda b1, b2: b1 and b2,
            "XOR": lambda b1, b2: b1 ^ b2,
            "NOR": lambda b1, b2: not (b1 or b2),
            "NAND": lambda b1, b2: not (b1 and b2),
            "XNOR": lambda b1, b2: not (b1 ^ b2),
            "NOT": lambda b1: int(not b1)
        }
        self.evaluate = switch[self.name]


class LogicCircuit:
    def __init__(self, filename):
        with open(filename) as input_circuit:
            json_circuit = json.load(input_circuit)

        self.name = json_circuit['name']
        self.alice_input_wires = json_circuit['alice']
        self.bob_input_wires = json_circuit['bob']
        self.output_wires = json_circuit['out']
        self.gates = list()

        gates = json_circuit['gates']
        wires = self.alice_input_wires + self.bob_input_wires + self.output_wires

        for gate in gates:
            gate_name = gate['type']
            input_wires = gate['in']
            output_wire = gate['id']

            self.gates.append(LogicGate(gate_name, input_wires, output_wire))
            wires.append(output_wire)
            wires += input_wires

        self.wires = sorted(list(set(wires)))


if __name__ == "__main__":
    a = LogicCircuit('input_circuit.json')
    print(a.wires)
