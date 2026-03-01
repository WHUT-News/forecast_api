"""
Unicode text encoding utilities.
"""
from typing import Tuple, Optional

SUPPORTED_ENCODINGS = ["utf-8", "utf-16", "utf-32"]
DEFAULT_ENCODING = "utf-8"


def detect_optimal_encoding(text: str) -> str:
    if not text:
        return DEFAULT_ENCODING

    cjk_count = 0
    total_chars = len(text)

    for char in text:
        code_point = ord(char)
        if (0x4E00 <= code_point <= 0x9FFF or
            0x3400 <= code_point <= 0x4DBF or
            0x20000 <= code_point <= 0x2A6DF or
            0x2A700 <= code_point <= 0x2B73F or
            0x2B740 <= code_point <= 0x2B81F or
            0x3000 <= code_point <= 0x303F or
            0x3040 <= code_point <= 0x309F or
            0x30A0 <= code_point <= 0x30FF or
            0xAC00 <= code_point <= 0xD7AF):
            cjk_count += 1

    cjk_ratio = cjk_count / total_chars if total_chars > 0 else 0

    if cjk_ratio > 0.5:
        return "utf-16"

    return "utf-8"


def encode_text(text: str, encoding: Optional[str] = None) -> Tuple[bytes, str, int]:
    if not text:
        return b"", DEFAULT_ENCODING, 0

    if encoding is None:
        encoding = detect_optimal_encoding(text)

    encoding = encoding.lower()
    if encoding not in SUPPORTED_ENCODINGS:
        raise ValueError(
            f"Unsupported encoding: {encoding}. Supported: {SUPPORTED_ENCODINGS}"
        )

    encoded = text.encode(encoding)
    return encoded, encoding, len(encoded)


def decode_text(data: bytes, encoding: str) -> str:
    if not data:
        return ""

    encoding = (encoding or DEFAULT_ENCODING).lower()
    if encoding not in SUPPORTED_ENCODINGS:
        raise ValueError(
            f"Unsupported encoding: {encoding}. Supported: {SUPPORTED_ENCODINGS}"
        )

    return data.decode(encoding, errors="replace")
