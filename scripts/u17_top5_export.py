"""Export the ranker's top attempts as posed sherd meshes for the conservator's look (ticket 07).

Order exactly as Layers 1+2 rank (l2_top_look.py): Layer 1 pass, then worst-sherd gap, then
profile. For each of the top K, writes rank<N>.ply: every sherd's full mesh placed by that
attempt's move, one fixed colour per sherd (the same colour for a sherd in every file), in
millimetres. Also top.json: rank, attempt id, worst gap, Layer 1 profile, and the colour
legend. Reads no answer key, and writes no label: the first look is blind.

Usage: python scripts/u17_top5_export.py --bundles B (the folder holding sherds.npz) --l2 juglet_l2.json --ranks ranks.json
           --out DIR [--k 5] [--pot-mm 65]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from l2_report import gaps  # noqa: E402

COLOURS = [("blue", (31, 119, 180)), ("orange", (255, 127, 14)), ("green", (44, 160, 44)),
           ("red", (214, 39, 40)), ("purple", (148, 103, 189)), ("brown", (140, 86, 75)),
           ("pink", (227, 119, 194)), ("olive", (188, 189, 34)), ("cyan", (23, 190, 207)),
           ("grey", (127, 127, 127)), ("navy", (0, 0, 128)), ("gold", (255, 200, 0))]


def write_ply(path, verts, faces, cols):
    v = np.concatenate(verts).astype("<f4")
    c = np.concatenate([np.tile(np.array(k, np.uint8), (len(x), 1)) for x, k in zip(verts, cols)])
    off = np.cumsum([0] + [len(x) for x in verts[:-1]])
    f = np.concatenate([x + o for x, o in zip(faces, off)]).astype("<i4")
    vt = np.empty(len(v), [("x", "<f4"), ("y", "<f4"), ("z", "<f4"),
                           ("r", "u1"), ("g", "u1"), ("b", "u1")])
    vt["x"], vt["y"], vt["z"] = v.T
    vt["r"], vt["g"], vt["b"] = c.T
    ft = np.empty(len(f), [("n", "u1"), ("i", "<i4", 3)])
    ft["n"], ft["i"] = 3, f
    head = (f"ply\nformat binary_little_endian 1.0\nelement vertex {len(v)}\n"
            "property float x\nproperty float y\nproperty float z\n"
            "property uchar red\nproperty uchar green\nproperty uchar blue\n"
            f"element face {len(f)}\nproperty list uchar int vertex_indices\nend_header\n")
    with open(path, "wb") as fh:
        fh.write(head.encode())
        fh.write(vt.tobytes())
        fh.write(ft.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for k in ("bundles", "l2", "ranks", "out"):
        ap.add_argument(f"--{k}", required=True, type=Path)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--pot-mm", type=float, default=None,
                    help="pot size in mm, for bundles whose sherds.npz predates pot_mm (Juglet: 65)")
    a = ap.parse_args()
    l2 = {r["id"]: r for r in json.loads(a.l2.read_text())["attempts"]}
    rk = {r["id"]: r for r in json.loads(a.ranks.read_text())["attempts"]}
    worst = {i: max(gaps(r)) for i, r in l2.items()}
    order = sorted(rk, key=lambda i: (not rk[i]["layer1_pass"], worst[i], rk[i]["profile_mm"]))
    z = np.load(a.bundles / "sherds.npz")
    k = int(z["k"])
    V = [z[f"v{j}"].astype(float) for j in range(k)]
    F = [z[f"f{j}"].astype(np.int64) for j in range(k)]
    cols = [COLOURS[j % len(COLOURS)] for j in range(k)]
    pot_mm = float(z["pot_mm"]) if "pot_mm" in z.files else a.pot_mm
    if pot_mm is None:
        sys.exit("sherds.npz has no pot_mm: pass --pot-mm")
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, aid in enumerate(order[: a.k], 1):
        b = np.load(a.bundles / "bundles" / f"{aid}.npz")
        P = [v @ R.T + t for v, R, t in zip(V, b["R"].astype(float), b["t"].astype(float))]
        write_ply(a.out / f"rank{n}.ply", P, F, [c for _, c in cols])
        rows.append(dict(rank=n, id=aid, layer1_pass=bool(rk[aid]["layer1_pass"]),
                         worst_gap_pct=round(float(worst[aid]), 3),
                         profile_mm=round(float(rk[aid]["profile_mm"]), 3),
                         box_mm=np.ptp(np.concatenate(P), 0).round(1).tolist()))
        print(f"rank {n}: {aid}  worst gap {worst[aid]:.2f}% of pot, "
              f"box {rows[-1]['box_mm']} mm -> {a.out / f'rank{n}.ply'}")
    (a.out / "top.json").write_text(json.dumps(dict(
        units="mm", pot_mm=pot_mm, order="Layer 1 pass, worst-sherd gap, profile",
        sherd_colours={j: name for j, (name, _) in enumerate(cols)}, attempts=rows), indent=1))
    print(f"-> {a.out / 'top.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
