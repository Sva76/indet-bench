"""Reject suspiciously large or malformed ZIP inputs before parsing archived scores.

This is a resource bound and path check, not a malware detector.
No archive files are ever extracted to disk by IndetBench.
"""
from __future__ import annotations

from pathlib import PurePosixPath
from zipfile import ZipFile

MAX_MEMBERS = 2_000
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000


def check_zip_archive(
    archive: ZipFile,
    *,
    max_members: int = MAX_MEMBERS,
    max_member_bytes: int = MAX_MEMBER_BYTES,
    max_archive_bytes: int = MAX_ARCHIVE_BYTES,
    max_compression_ratio: int = MAX_COMPRESSION_RATIO,
) -> None:
    """Bound decompression size, member count and compression ratio."""
    members = archive.infolist()
    if len(members) > max_members:
        raise ValueError("ZIP contains too many members")
    total = 0
    for member in members:
        filename = member.filename.replace("\\", "/")
        path = PurePosixPath(filename)
        if path.is_absolute() or ".." in path.parts or not filename.strip():
            raise ValueError("ZIP contains unsafe member path")
        if member.flag_bits & 0x1:
            raise ValueError("Encrypted ZIP members are unsupported")
        if member.file_size > max_member_bytes:
            raise ValueError("ZIP member uncompressed size exceeds safety limit")
        total += member.file_size
        if total > max_archive_bytes:
            raise ValueError("ZIP total uncompressed size exceeds safety limit")
        if member.file_size and member.file_size / max(1, member.compress_size) > max_compression_ratio:
            raise ValueError("ZIP compression ratio exceeds safety limit")
