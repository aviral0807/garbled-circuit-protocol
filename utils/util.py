def keys_to_int(x):
    return {int(k): v for k, v in x}


def prod(x):
    p = 1
    for i in x:
        p *= i
    return p


def e_gcd(b, n):
    """
    Takes positive integers a, b as input, and return a triple (g, x, y), such that
    ax + by = g = gcd(a, b).
    """
    x0, x1, y0, y1 = 1, 0, 0, 1
    while n != 0:
        q, b, n = b // n, n, b % n
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return b, x0, y0


def mul_inv(b, n):
    g, x, _ = e_gcd(b, n)
    if g == 1:
        return x % n


def mod_div(a, b, n):
    return a * mul_inv(b, n) % n
