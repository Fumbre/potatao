import os
import x25519

def bytes_to_hex(b):
    return "".join("{:02x}".format(x) for x in b)

print("--- 1. Testing X25519 RFC 7748 Vector ---")

# Standard test vector from RFC 7748 Section 5.2
# Alice's private key (scalar)
rfc_scalar = bytes([
    0x77, 0x07, 0x6d, 0x0a, 0x73, 0x18, 0xa5, 0x7d,
    0x3c, 0x16, 0xc1, 0x72, 0x51, 0xb2, 0x66, 0x45,
    0xdf, 0x4c, 0x2f, 0x87, 0xeb, 0xc0, 0x99, 0x2a,
    0xb1, 0x77, 0xfb, 0xa5, 0x1d, 0xb9, 0x2c, 0x2a
])

# Expected Alice's public key
rfc_expected_public = "8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a"

# Calculate public key using our new assembly module
calculated_public = x25519.calculate(rfc_scalar, x25519.BASE_POINT)
calculated_public_hex = bytes_to_hex(calculated_public)

print("Expected Public: ", rfc_expected_public)
print("Calculated Public:", calculated_public_hex)

if calculated_public_hex == rfc_expected_public:
    print("✅ RFC 7748 Vector Match! Assembly math is 100% accurate.")
else:
    print("❌ Vector Mismatch! Please check assembly compilation.")

print("\n--- 2. Testing Full Key Exchange Flow (ECDH) ---")

# Step 1: Generate Alice's Keypair
alice_private = os.urandom(32)
alice_public = x25519.calculate(alice_private, x25519.BASE_POINT)

# Step 2: Generate Bob's Keypair
bob_private = os.urandom(32)
bob_public = x25519.calculate(bob_private, x25519.BASE_POINT)

print("Alice Private:", bytes_to_hex(alice_private))
print("Alice Public: ", bytes_to_hex(alice_public))
print("Bob Private:  ", bytes_to_hex(bob_private))
print("Bob Public:   ", bytes_to_hex(bob_public))

# Step 3: ECDH Shared Secret Calculation
# Alice calculates secret using Bob's public key
alice_shared = x25519.calculate(alice_private, bob_public)

# Bob calculates secret using Alice's public key
bob_shared = x25519.calculate(bob_private, alice_public)

print("\nAlice Shared Secret:", bytes_to_hex(alice_shared))
print("Bob Shared Secret:  ", bytes_to_hex(bob_shared))

if alice_shared == bob_shared:
    print("✅ Key Exchange Successful! Both sides shared the same AES key.")
else:
    print("❌ Key Exchange Failed! Secrets do not match.")