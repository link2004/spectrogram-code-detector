def generate_combinations():
    combinations = []
    c = 0  # カウント変数Cを初期化
    for a in range(0, 16):
        for b in range(a, 16):  # bはaから始めることで重複を避ける
            combinations.append((a, b, c))
            c += 1  # Cを1増やす
    return combinations

def print_combinations():
    combinations = generate_combinations()
    for a, b, c in combinations:
        print(f"A: {a}, B: {b}, C: {c}")

import math

def find_A_B(C):
    A = math.floor((33 - math.sqrt(1089 - 8 * C)) / 2)
    S_A = 16 * A - (A * (A - 1)) // 2
    B = A + (C - S_A)
    return A, B


if __name__ == "__main__":
    print_combinations()
    for c in range(0, 136):
        a, b = find_A_B(c)
        print(f"C: {c} -> A: {a}, B: {b}")
