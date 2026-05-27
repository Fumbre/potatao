import jwt
import time

# --- Configuration ---
SECRET_KEY = "pico2w-ultra-secure-key"
# A standard JSON payload for testing
PAYLOAD_DATA = '{"user_id":42,"device":"pico2w","authenticated":true}'

print("=========================================")
print("        MicroPython JWT C-Module Test    ")
print("=========================================")

# 1. Test successful token creation
print("\n[TEST 1] Creating a valid JWT...")
try:
    token = jwt.create_token(PAYLOAD_DATA, SECRET_KEY)
    print("Successfully generated JWT:")
    print(token)
except Exception as e:
    print("Failed to create token:", e)

# 2. Test successful verification
print("\n[TEST 2] Verifying the valid JWT...")
decoded = jwt.verify_token(token, SECRET_KEY)
print("Verification Result (Decoded Payload):")
print(decoded)

# 3. Test verification with a corrupted/incorrect secret key
print("\n[TEST 3] Verifying with a WRONG secret key (Signature Tampering)...")
tampered_decode = jwt.verify_token(token, "wrong_secret_key")
print("Verification Result:")
print(tampered_decode) 
# Expecting: "Signature verification failed. Token tampered or invalid secret."

# 4. Test verification with a broken JWT structure
print("\n[TEST 4] Verifying a broken JWT string (Format Error)...")
broken_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload" # Missing the second dot
format_error_decode = jwt.verify_token(broken_token, SECRET_KEY)
print("Verification Result:")
print(format_error_decode)
# Expecting: "Invalid JWT format. Missing dot separators."

print("\n=========================================")
print("              Test Complete              ")
print("=========================================")