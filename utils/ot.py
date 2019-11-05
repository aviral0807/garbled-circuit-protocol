import json
from itertools import combinations

import requests
import rsa

from config import API_CALL
from config import RSA_bits
from utils.crypto import hasher
from utils.next_prime import next_prime
from utils.util import mod_div, prod, keys_to_int

OT1_URL = "ot1"
OT2_URL = "ot2"


def lagrange(x, y, g):
    assert len(x) == len(y) and len(x) > 0, "Lengths of x and y must equal and non-zero."
    x_len = len(x)
    f = [0] * x_len
    for i in range(x_len):
        partial = []
        combo_list = list(x)
        combo_list.pop(i)
        for j in range(x_len):
            c = 0
            for k in combinations(combo_list, j):
                c += prod(map(lambda q: -q, k))
            partial.append(c)
        d = 1
        for j in range(x_len):
            if j != i:
                d *= x[i] - x[j]

        partial = map(lambda q: mod_div(q * y[i], d, g), partial)
        f = [(m + n) % g for m, n in zip(f, partial)]  # also needs % G

    for i in range(x_len):
        assert compute_poly(f, x[i], g) == y[i], i
    return f


def bytes_to_int(m):
    return int.from_bytes(m, byteorder="big")


def int_to_bytes(i):
    return i.to_bytes(RSA_bits // 8, byteorder="big")


def strip_padding(b, secret_length):
    return b[(RSA_bits // 8 - secret_length):]
    # return b


def compute_poly(f, x, m):
    y = 0
    for i in range(len(f)):
        y += f[i] * pow(x, len(f) - 1 - i, m)
    return y % m


def alice_side_ot(messages):
    (pubkey, private_key) = rsa.newkeys(RSA_bits)
    pubkey = pubkey
    private_key = private_key
    G = next_prime(pubkey.n)

    hashes = []

    for m in messages:
        hashes.append(hasher(m))
    data = {
        "pubkey": json.dumps({"e": pubkey.e, "n": pubkey.n}),
        "hashes": json.dumps(hashes),
        "secret_length": json.dumps(len(messages[0]))
    }

    response = requests.post(url=API_CALL + OT1_URL, data=data)

    string_f = json.loads(response.text)
    string_f = list(map(int, string_f))
    g = []
    for i in range(len(messages)):
        f = pow(compute_poly(string_f, i, G), private_key.d, pubkey.n)
        g.append((f * bytes_to_int(messages[i])) % pubkey.n)

    response = requests.post(url=API_CALL + OT2_URL, json=g)
    output_labels = json.loads(response.text, object_pairs_hook=keys_to_int)

    return output_labels
