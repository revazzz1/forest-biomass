"""Read single files out of the BioMassters zip archives on Hugging Face.

Neither Hugging Face repo hosts loose TIFFs: `train_features` is a 14-part
split zip (~150 GB) and `train_agbm` a single zip. A selective download is
therefore HTTP range requests: read each archive's central directory once,
then fetch and inflate one entry at a time.
"""
from __future__ import annotations

import struct
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

BASE = "https://huggingface.co/datasets/ibm-nasa-geospatial/BioMassters/resolve/main/"
PARTS = {"train_features": 14, "train_agbm": 1}  # archive -> number of split parts
PART_SIZE = 10_737_418_240  # bytes per split part (10 GiB)
SLACK = 512  # local header + name + extra never exceed this


def part_name(archive: str, disk: int) -> str:
    """Split zips number parts .z01 .. .zNN and keep the last one as .zip."""
    return f"{archive}.zip" if disk == PARTS[archive] - 1 else f"{archive}.z{disk + 1:02d}"


def _get(name: str, byte_range: str) -> bytes:
    req = urllib.request.Request(BASE + name, headers={"Range": f"bytes={byte_range}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _central_directory(archive: str) -> bytes:
    last = part_name(archive, PARTS[archive] - 1)
    tail = _get(last, "-200")
    i = tail.rfind(b"PK\x06\x06")  # zip64 end-of-central-directory
    if i >= 0:
        size, off = struct.unpack("<QQ", tail[i + 40 : i + 56])
    else:
        i = tail.rfind(b"PK\x05\x06")
        size, off = struct.unpack("<II", tail[i + 12 : i + 20])
    return _get(last, f"{off}-{off + size - 1}")


def _parse(archive: str, cd: bytes) -> list[dict]:
    rows, i = [], 0
    while cd[i : i + 4] == b"PK\x01\x02":
        f = struct.unpack("<IHHHHHHIIIHHHHHII", cd[i : i + 46])
        method, crc, csize, usize, nlen, xlen, clen, disk, off = f[4], f[7], f[8], f[9], f[10], f[11], f[12], f[13], f[16]
        name = cd[i + 46 : i + 46 + nlen].decode()
        extra, j = cd[i + 46 + nlen : i + 46 + nlen + xlen], 0
        while j + 4 <= len(extra):  # zip64 extra field overrides the 0xFFFF.. sentinels
            hid, hsz = struct.unpack("<HH", extra[j : j + 4])
            body, k = extra[j + 4 : j + 4 + hsz], 0
            if hid == 1:
                if usize == 0xFFFFFFFF:
                    usize, k = struct.unpack("<Q", body[k : k + 8])[0], k + 8
                if csize == 0xFFFFFFFF:
                    csize, k = struct.unpack("<Q", body[k : k + 8])[0], k + 8
                if off == 0xFFFFFFFF:
                    off, k = struct.unpack("<Q", body[k : k + 8])[0], k + 8
                if disk == 0xFFFF:
                    disk = struct.unpack("<I", body[k : k + 4])[0]
            j += 4 + hsz
        if not name.endswith("/"):
            rows.append(dict(archive=archive, name=name.rsplit("/", 1)[-1], method=method, crc=crc,
                             csize=csize, usize=usize, disk=disk, off=off))
        i += 46 + nlen + xlen + clen
    return rows


def archive_index(cache: Path) -> pd.DataFrame:
    """One row per file in both archives; ~33 MB of central directory, cached as parquet."""
    path = cache / "zip_index.parquet"
    if not path.exists():
        rows = [r for a in PARTS for r in _parse(a, _central_directory(a))]
        pd.DataFrame(rows).to_parquet(path, index=False)
    return pd.read_parquet(path)


def fetch_entry(e: pd.Series) -> bytes:
    """Fetch one archive entry by range request, following it into the next part if it straddles."""
    need = SLACK + e.csize
    raw = _get(part_name(e.archive, e.disk), f"{e.off}-{min(e.off + need, PART_SIZE) - 1}")
    if len(raw) < need:
        raw += _get(part_name(e.archive, e.disk + 1), f"0-{need - len(raw) - 1}")
    sig, nlen, xlen = struct.unpack("<I", raw[:4])[0], *struct.unpack("<HH", raw[26:30])
    assert sig == 0x04034B50, f"bad local header for {e['name']}"
    data = raw[30 + nlen + xlen : 30 + nlen + xlen + e.csize]
    out = zlib.decompress(data, -15) if e.method == 8 else data
    assert len(out) == e.usize and zlib.crc32(out) == e.crc, f"corrupt download: {e['name']}"
    return out


def download(names: list[str], index: pd.DataFrame, dest: Path, workers: int = 8) -> None:
    """Fetch every named file into `dest`, skipping ones already there."""
    todo = index[index.name.isin(set(names) - {p.name for p in dest.iterdir()})]

    def one(e: pd.Series) -> None:
        tmp = dest / (e["name"] + ".part")
        tmp.write_bytes(fetch_entry(e))
        tmp.rename(dest / e["name"])

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, (e for _, e in todo.iterrows())))
