from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

ASSET_URL = (
    "https://raw.githubusercontent.com/"
    "MonarchCastleTech/.github/main/profile/icon.png"
)
EXPECTED_BLOB_SHA = "9207bb10f49b0f0958adbf51b2c0d89a965f7484"
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "dashboard"
    / "public"
    / "brand"
    / "mct-icon.png"
)


def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(
        header + content,
        usedforsecurity=False,
    ).hexdigest()


def import_logo() -> Path:
    response = httpx.get(
        ASSET_URL,
        follow_redirects=True,
        timeout=httpx.Timeout(30.0, connect=15.0),
        headers={"User-Agent": "superlig-forecast-brand-import/1.0"},
    )
    response.raise_for_status()
    content = response.content
    actual_sha = git_blob_sha(content)
    if actual_sha != EXPECTED_BLOB_SHA:
        raise RuntimeError(
            "MCT logo checksum mismatch: "
            f"expected {EXPECTED_BLOB_SHA}, received {actual_sha}"
        )
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Pinned MCT asset is not a PNG")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(content)
    return OUTPUT_PATH


if __name__ == "__main__":
    print(import_logo())
