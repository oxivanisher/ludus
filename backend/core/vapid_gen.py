"""
Run this module to generate a VAPID key pair for Web Push.

    python -m core.vapid_gen

Copy the output into your .env file.
"""

from py_vapid import Vapid
from py_vapid.utils import b64urlencode
from cryptography.hazmat.primitives import serialization


def main() -> None:
    v = Vapid()
    v.generate_keys()
    private_der = v.private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_raw = v.public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    print("Add these to your .env file:\n")
    print(f"VAPID_PRIVATE_KEY={b64urlencode(private_der).decode()}")
    print(f"VAPID_PUBLIC_KEY={b64urlencode(public_raw).decode()}")


if __name__ == "__main__":
    main()
