#!/usr/bin/env python3
"""Are two HDF5 files the same data? Array by array, not by file hash.

Written for sherd-worn ticket 05: TORA's build scripts now import their wear code
from the package, and any change to a built array means the switch changed
something it should not have. A file hash cannot answer that: write_u10_worn.py
stores results in the order its workers finish, so two identical datasets can
have different bytes on disk. So this walks both files in sorted order and
requires the same names, kinds, dtypes, shapes, attributes and array bytes, and
the same manifest if one is given. NaNs compare by their bytes.

Exit 0 identical, 1 different. The file hashes are printed for the record only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


def walk(path):
    items = {"/": None}
    with h5py.File(path, "r") as f:
        f.visit(lambda name: items.__setitem__(name, None))
    return sorted(items)


def same_value(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype != b.dtype or a.shape != b.shape:
        return False
    if a.dtype == object:
        return a.tolist() == b.tolist()
    return a.tobytes() == b.tobytes()


def compare_files(pa, pb):
    """Every difference between two files, as one line each."""
    diffs = []
    na, nb = walk(pa), walk(pb)
    diffs += [f"only in A: {n}" for n in sorted(set(na) - set(nb))]
    diffs += [f"only in B: {n}" for n in sorted(set(nb) - set(na))]
    n_arrays = 0
    with h5py.File(pa, "r") as fa, h5py.File(pb, "r") as fb:
        for name in sorted(set(na) & set(nb)):
            a, b = fa[name], fb[name]
            if set(a.attrs) != set(b.attrs):
                diffs.append(f"attribute names: {name}")
            for k in sorted(set(a.attrs) & set(b.attrs)):
                if not same_value(a.attrs[k], b.attrs[k]):
                    diffs.append(f"attribute {k}: {name}")
            if isinstance(a, h5py.Group) != isinstance(b, h5py.Group):
                diffs.append(f"group against dataset: {name}")
            elif isinstance(a, h5py.Dataset):
                n_arrays += 1
                if a.dtype != b.dtype:
                    diffs.append(f"dtype {a.dtype} against {b.dtype}: {name}")
                elif a.shape != b.shape:
                    diffs.append(f"shape {a.shape} against {b.shape}: {name}")
                elif not same_value(a[()], b[()]):
                    diffs.append(f"values: {name}")
    return diffs, len(na), n_arrays


def compare_manifests(pa, pb):
    # through dumps, because NaN != NaN and the manifests hold NaNs for unmeasured things
    a, b = json.loads(Path(pa).read_text()), json.loads(Path(pb).read_text())
    text = lambda x: json.dumps(x, sort_keys=True)
    if text(a) == text(b):
        return []
    if not (isinstance(a, dict) and isinstance(b, dict)):
        return ["manifest differs"]
    return [f"manifest: {k}" for k in sorted(set(a) | set(b)) if text(a.get(k)) != text(b.get(k))]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--manifest-a")
    ap.add_argument("--manifest-b")
    ap.add_argument("--out", help="write the result here as JSON")
    args = ap.parse_args()

    diffs, n_names, n_arrays = compare_files(args.a, args.b)
    if args.manifest_a and args.manifest_b:
        diffs += compare_manifests(args.manifest_a, args.manifest_b)
    res = {"a": args.a, "b": args.b, "identical": not diffs,
           "names": n_names, "arrays": n_arrays,
           "n_differences": len(diffs), "first_differences": diffs[:50],
           "sha256_a": sha256(args.a), "sha256_b": sha256(args.b)}
    print(json.dumps({k: res[k] for k in ("identical", "names", "arrays", "n_differences",
                                          "first_differences", "sha256_a", "sha256_b")}, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1))
    raise SystemExit(0 if res["identical"] else 1)


if __name__ == "__main__":
    main()
