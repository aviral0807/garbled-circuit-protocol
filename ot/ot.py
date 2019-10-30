from hashlib import sha256
from itertools import combinations
from random import SystemRandom
from ot.mulinv import mulinv

RSA_bits = 1024

cryptorand = SystemRandom()


def randint(n):
    return cryptorand.randrange(n)


def moddiv(a, b, n):
    return a * mulinv(b, n) % n


def prod(x):
    p = 1
    for i in x:
        p *= i
    return p


def hasher(b):
    return sha256(b).hexdigest()


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

        partial = map(lambda q: moddiv(q * y[i], d, g), partial)
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
