from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def format_abdm_timestamp(moment: Optional[datetime] = None) -> str:
    """Return an ABDM-safe UTC timestamp with exactly 3 milliseconds and Z."""

    current_moment = moment or datetime.now(timezone.utc)
    utc_moment = current_moment.astimezone(timezone.utc)
    return utc_moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _ensure_base64_padding(value: str) -> str:
    missing_padding = len(value) % 4
    if missing_padding:
        return value + ("=" * (4 - missing_padding))
    return value


def _decode_base64_bytes(value: str | bytes | None) -> bytes:
    if value is None:
        raise ValueError("Missing base64 value")

    if isinstance(value, bytes):
        return value

    normalized_value = _ensure_base64_padding(value.strip())
    try:
        return base64.b64decode(normalized_value, validate=False)
    except Exception:
        return base64.urlsafe_b64decode(normalized_value)


def _encode_base64_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _encode_hex_bytes(value: bytes) -> str:
    return value.hex()


def _decode_hex_bytes(value: str | None) -> bytes:
    if value is None:
        raise ValueError("Missing hex value")
    normalized_value = value.strip()
    if len(normalized_value) % 2 != 0:
        raise ValueError("Hex value must contain an even number of characters")
    return bytes.fromhex(normalized_value)


def _first_string(payload: Any, *keys: str) -> Optional[str]:
    if not isinstance(payload, dict):
        return None

    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _lookup_path(payload: Any, *path: str) -> Any:
    current_value = payload
    for key in path:
        if not isinstance(current_value, dict):
            return None
        current_value = current_value.get(key)
    return current_value


@dataclass(slots=True)
class AbdmCurve25519KeyPair:
    private_key: X25519PrivateKey
    public_key_bytes: bytes
    nonce_bytes: bytes

    @classmethod
    def generate(cls, nonce_length: int = 12) -> "AbdmCurve25519KeyPair":
        private_key = X25519PrivateKey.generate()
        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        nonce_bytes = secrets.token_bytes(nonce_length)
        return cls(
            private_key=private_key,
            public_key_bytes=public_key_bytes,
            nonce_bytes=nonce_bytes,
        )

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, str]) -> "AbdmCurve25519KeyPair":
        private_key = X25519PrivateKey.from_private_bytes(_decode_base64_bytes(snapshot["private_key"]))
        public_key_bytes = _decode_base64_bytes(snapshot["public_key"])
        nonce_bytes = _decode_base64_bytes(snapshot["nonce"])
        return cls(
            private_key=private_key,
            public_key_bytes=public_key_bytes,
            nonce_bytes=nonce_bytes,
        )

    @property
    def public_key_b64(self) -> str:
        return _encode_base64_bytes(self.public_key_bytes)

    @property
    def private_key_b64(self) -> str:
        private_key_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return _encode_base64_bytes(private_key_bytes)

    @property
    def nonce_b64(self) -> str:
        return _encode_base64_bytes(self.nonce_bytes)

    @property
    def private_key_hex(self) -> str:
        private_key_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return _encode_hex_bytes(private_key_bytes)

    @property
    def public_key_hex(self) -> str:
        return _encode_hex_bytes(self.public_key_bytes)

    @property
    def nonce_hex(self) -> str:
        return _encode_hex_bytes(self.nonce_bytes)

    def snapshot(self) -> Dict[str, str]:
        return {
            "private_key": self.private_key_b64,
            "public_key": self.public_key_b64,
            "nonce": self.nonce_b64,
        }

    def hex_snapshot(self) -> Dict[str, str]:
        return {
            "private_key_hex": self.private_key_hex,
            "public_key_hex": self.public_key_hex,
            "nonce_hex": self.nonce_hex,
        }

    @classmethod
    def from_hex_storage(cls, private_key_hex: str, nonce_hex: str) -> "AbdmCurve25519KeyPair":
        private_key = X25519PrivateKey.from_private_bytes(_decode_hex_bytes(private_key_hex))
        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        nonce_bytes = _decode_hex_bytes(nonce_hex)
        return cls(
            private_key=private_key,
            public_key_bytes=public_key_bytes,
            nonce_bytes=nonce_bytes,
        )

    def request_key_material(self) -> Dict[str, Any]:
        # ABDM sandbox payloads are strict about formatting, so keep the curve,
        # key, and nonce payload explicit and easy to audit.
        return {
            "cryptoAlg": "ECDH",
            "curve": "Curve25519",
            "dhPublicKey": {
                "key": self.public_key_b64,
                "parameters": {
                    "curve": "Curve25519",
                },
                "expiry": format_abdm_timestamp(datetime.now(timezone.utc) + timedelta(minutes=15)),
            },
            "nonce": self.nonce_b64,
        }

    def _derive_aes_key(
        self,
        peer_public_key_b64: str,
        peer_nonce_b64: Optional[str],
        *,
        info_label: bytes = b"ABDM-HIU-HEALTH-DATA",
    ) -> bytes:
        peer_public_key = X25519PublicKey.from_public_bytes(_decode_base64_bytes(peer_public_key_b64))
        shared_secret = self.private_key.exchange(peer_public_key)

        salt_bytes = _decode_base64_bytes(peer_nonce_b64) if peer_nonce_b64 else self.nonce_bytes
        info = info_label + b"|" + self.nonce_bytes
        if peer_nonce_b64:
            info += b"|" + _decode_base64_bytes(peer_nonce_b64)

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            info=info,
        )
        return hkdf.derive(shared_secret)

    def _extract_encrypted_components(self, envelope: Any) -> Dict[str, Optional[str]]:
        if isinstance(envelope, str):
            try:
                envelope = json.loads(envelope)
            except ValueError as exc:
                raise ValueError("Encrypted ABDM envelope was not valid JSON") from exc

        if not isinstance(envelope, dict):
            raise ValueError("Encrypted ABDM envelope must be a dictionary or JSON string")

        container = envelope
        nested_payload = envelope.get("payload")
        if isinstance(nested_payload, dict):
            container = nested_payload

        response_payload = envelope.get("response")
        if isinstance(response_payload, dict):
            container = response_payload

        hi_response_payload = envelope.get("hiResponse") or envelope.get("hi_response")
        if isinstance(hi_response_payload, dict):
            container = hi_response_payload

        key_material = (
            envelope.get("keyMaterial")
            or envelope.get("key_material")
            or envelope.get("hipKeyMaterial")
            or envelope.get("hip_key_material")
            or container.get("keyMaterial")
            or container.get("key_material")
        )
        if not isinstance(key_material, dict):
            key_material = {}

        peer_public_key_b64 = _first_string(
            key_material,
            "publicKey",
            "key",
            "dhPublicKey",
        )
        if not peer_public_key_b64 and isinstance(key_material.get("dhPublicKey"), dict):
            peer_public_key_b64 = _first_string(key_material["dhPublicKey"], "key")
        if not peer_public_key_b64:
            peer_public_key_b64 = _first_string(container, "publicKey", "key")

        peer_nonce_b64 = _first_string(key_material, "nonce", "senderNonce", "hipNonce")
        if not peer_nonce_b64:
            peer_nonce_b64 = _first_string(container, "nonce", "senderNonce", "hipNonce")

        ciphertext_b64 = _first_string(
            container,
            "encryptedData",
            "encrypted_data",
            "ciphertext",
            "cipherText",
            "data",
        )
        if not ciphertext_b64 and isinstance(envelope.get("data"), dict):
            ciphertext_b64 = _first_string(envelope["data"], "encryptedData", "ciphertext", "data")

        iv_b64 = _first_string(
            container,
            "iv",
            "initializationVector",
            "gcmNonce",
        )
        if not iv_b64:
            iv_b64 = _first_string(key_material, "iv", "nonce")
        if not iv_b64:
            iv_b64 = _first_string(container, "nonce")

        aad_b64 = _first_string(container, "aad", "associatedData", "associated_data")

        if not peer_public_key_b64 or not ciphertext_b64:
            raise ValueError("ABDM encrypted payload is missing the peer public key or ciphertext")

        return {
            "peer_public_key_b64": peer_public_key_b64,
            "peer_nonce_b64": peer_nonce_b64,
            "ciphertext_b64": ciphertext_b64,
            "iv_b64": iv_b64,
            "aad_b64": aad_b64,
        }

    def decrypt_encrypted_payload(self, envelope: Any) -> bytes:
        components = self._extract_encrypted_components(envelope)
        aes_key = self._derive_aes_key(
            components["peer_public_key_b64"],
            components["peer_nonce_b64"],
        )

        aes_gcm = AESGCM(aes_key)
        nonce_bytes = _decode_base64_bytes(components["iv_b64"])
        ciphertext_bytes = _decode_base64_bytes(components["ciphertext_b64"])
        aad_bytes = _decode_base64_bytes(components["aad_b64"]) if components["aad_b64"] else None

        try:
            return aes_gcm.decrypt(nonce_bytes, ciphertext_bytes, aad_bytes)
        except Exception as exc:
            raise ValueError("Failed to decrypt ABDM AES-256-GCM payload") from exc

    def decrypt_json_bundle(self, envelope: Any) -> Dict[str, Any]:
        plaintext_bytes = self.decrypt_encrypted_payload(envelope)
        plaintext_text = plaintext_bytes.decode("utf-8")
        parsed_payload = json.loads(plaintext_text)
        if not isinstance(parsed_payload, dict):
            raise ValueError("Decrypted ABDM payload must decode to a JSON object")
        return parsed_payload