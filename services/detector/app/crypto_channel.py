"""AES-GCM encrypt/decrypt for the simulated secure transmission channel.

Payload format sent over the wire (and understood by apps/api's ingest route):
    base64(nonce) + "." + base64(ciphertext_with_tag)

The key is derived once from TRANSPORT_SECRET via SHA-256 — a static shared secret, which is
fine for a prototype simulating "the channel is encrypted" but is explicitly flagged in
docs/building/01-architecture.md as not a real key-management design.
"""
from __future__ import annotations

import base64
import hashlib
import json

from Crypto.Cipher import AES

from .config import TRANSPORT_SECRET

_KEY = hashlib.sha256(TRANSPORT_SECRET.encode("utf-8")).digest()  # 32 bytes -> AES-256


def encrypt_json(payload: dict) -> str:
    plaintext = json.dumps(payload).encode("utf-8")
    cipher = AES.new(_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return (
        base64.b64encode(cipher.nonce).decode("ascii")
        + "."
        + base64.b64encode(ciphertext + tag).decode("ascii")
    )


def decrypt_json(blob: str) -> dict:
    nonce_b64, body_b64 = blob.split(".", 1)
    nonce = base64.b64decode(nonce_b64)
    body = base64.b64decode(body_b64)
    ciphertext, tag = body[:-16], body[-16:]
    cipher = AES.new(_KEY, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(plaintext.decode("utf-8"))
