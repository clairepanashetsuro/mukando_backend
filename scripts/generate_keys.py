"""Generate local RS256 JWT keys for development."""
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]
KEYS = ROOT / "keys"
PRIVATE = KEYS / "private.pem"
PUBLIC = KEYS / "public.pem"

KEYS.mkdir(exist_ok=True)
if PRIVATE.exists() or PUBLIC.exists():
    raise SystemExit("JWT keys already exist; delete them first if you intentionally want to regenerate them.")

private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE.write_bytes(private.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
))
PUBLIC.write_bytes(private.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
))
print(f"Generated {PRIVATE}")
print(f"Generated {PUBLIC}")
