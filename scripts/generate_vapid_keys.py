#!/usr/bin/env python3
"""
Generate VAPID key pair for Web Push notifications.

Run once to generate keys, then add them to your environment variables:
  VAPID_PUBLIC_KEY  — goes in env vars (and is sent to browsers)
  VAPID_PRIVATE_KEY — goes in env vars (keep secret!)
  VAPID_CLAIM_EMAIL — your contact email

Usage:
  python3 scripts/generate_vapid_keys.py
"""

import base64
from py_vapid import Vapid
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption,
)


def main():
    vapid = Vapid()
    vapid.generate_keys()

    # Private key as PEM (for VAPID_PRIVATE_KEY env var)
    private_pem = vapid.private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ).decode().strip()

    # Public key as base64url (applicationServerKey for browsers)
    raw_pub = vapid.public_key.public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(raw_pub).decode().rstrip("=")

    print("=" * 60)
    print("VAPID Keys Generated Successfully")
    print("=" * 60)
    print()
    print("Add these to your environment variables (Railway, .env, etc.):")
    print()
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print()
    print("VAPID_PRIVATE_KEY (set as multi-line env var or escape newlines):")
    print(private_pem)
    print()
    print("# For single-line env var, use \\n escaping:")
    escaped = private_pem.replace("\n", "\\n")
    print(f"VAPID_PRIVATE_KEY={escaped}")
    print()
    print("VAPID_CLAIM_EMAIL=your-email@example.com")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
