"""SHA-256 canonical checksum calculation (SDD 3.5, SEC-02, NFR-08)."""

import hashlib
import json


class ChecksumService:
    @staticmethod
    def compute(state: dict) -> str:
        """Compute SHA-256 hex digest over canonical JSON representation."""
        canonical = json.dumps(state, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def verify(cls, state: dict, checksum: str) -> bool:
        """Verify state against an expected checksum."""
        return cls.compute(state) == checksum
