def calculate_C(A, B):
    C = 15 * A - (A * (A - 1)) // 2 + B
    return C

# 例:
for a in range(0, 16):
    for b in range(a, 16):
        C = calculate_C(a, b)
        print(f"A: {a}, B: {b}, C: {C}")
