import os, base58

def generate_base58(length = 32):
    base58_full = base58.b58encode(os.urandom(length))
    first_32 = base58_full[0:32]
    return first_32

if __name__ == "__main__":
    print(generate_base58(32))
