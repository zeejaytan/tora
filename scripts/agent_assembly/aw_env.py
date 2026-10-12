"""A rebuild of the AssemblyWorld tool set, as a command line, for one blind reassembly task.

Ticket `.scratch/agent-assembly/issues/02`. AssemblyWorld (arXiv 2609.40353v1) did not
release its environment, so this follows its Table A-2 tool by tool. The agent sees rendered
views and pose read-backs only; mesh vertices are never printed, and the answer key is not
here at all (it stays on Spartan, `prep_tasks.py` -> secret/).

    list_objects                 part and group ids
    get_object ID                centre position, orientation quaternion (w,x,y,z), box extents
    get_scene / get_state        conventions, groups, camera, every pose
    capture_scene                1024x768 render, 38 deg vertical field of view; prints the PNG path
    move_camera                  --yaw/--pitch (orbit, deg), --zoom (factor), --pan-x/--pan-y,
                                 --reset (frame every part)
    translate_objects IDS --vec X Y Z [--frame world|camera]
    rotate_objects IDS --angles AX AY AZ [--frame world|camera] [--pivot X Y Z]
                                 X then Y then Z, degrees; default pivot is the mean centre
    set_object_pose ID [--position X Y Z] [--quat W X Y Z]
    group_objects NAME IDS / ungroup_objects NAME
    start_episode / finish       finish writes final.json (the poses that get scored)

Two choices of ours, both stated in the ticket: a part's position is its centre (the paper's
body origins "need not coincide with visual part centres", which only makes the agent's job
harder), and each render carries a legend naming the part colours plus a small world-axes
triad at the origin (X red, Y green, Z blue).

Usage:  PYOPENGL_PLATFORM=osmesa python aw_env.py --task DIR <command> [args]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

PALETTE = [(230, 97, 1), (35, 120, 200), (60, 170, 80), (200, 50, 150), (240, 200, 30),
           (120, 80, 200), (30, 190, 190), (150, 90, 40), (220, 60, 60), (110, 110, 110)]
W, H, VFOV = 1024, 768, 38.0


def rot_xyz(ax, ay, az):
    ax, ay, az = np.radians([ax, ay, az])
    Rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]])
    Ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]])
    Rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class Env:
    def __init__(self, task_dir):
        self.dir = Path(task_dir)
        self.meta = json.loads((self.dir / "task.json").read_text())
        self.meshes = {p: trimesh.load(self.dir / "pieces" / f"{p}.ply", process=False)
                       for p in self.meta["parts"]}
        self.c0 = {p: np.asarray(m.vertices).mean(0) for p, m in self.meshes.items()}
        sp = self.dir / "state.json"
        if sp.exists():
            s = json.loads(sp.read_text())
            self.T = {p: np.asarray(t) for p, t in s["T"].items()}
            self.groups, self.cam, self.n_views = s["groups"], s["camera"], s["n_views"]
            self.started = s.get("started", False)
        else:
            self.T = {p: np.eye(4) for p in self.meshes}
            self.groups, self.n_views, self.started = {}, 0, False
            self.cam = {}
            self.reset_camera()

    # ---------- state ----------
    def save(self, cmd, args, result):
        (self.dir / "state.json").write_text(json.dumps({
            "T": {p: t.tolist() for p, t in self.T.items()}, "groups": self.groups,
            "camera": self.cam, "n_views": self.n_views, "started": self.started}))
        with open(self.dir / "log.jsonl", "a") as f:
            f.write(json.dumps({"t": time.time(), "cmd": cmd, "args": args, "result": result,
                                "T": {p: t.tolist() for p, t in self.T.items()},
                                "camera": self.cam}) + "\n")

    def resolve(self, ids):
        out = []
        for i in ids:
            if i in self.groups:
                out += self.groups[i]
            elif i in self.T:
                out.append(i)
            else:
                raise SystemExit(f"unknown id: {i}")
        return list(dict.fromkeys(out))

    def centre(self, p):
        return self.T[p][:3, :3] @ self.c0[p] + self.T[p][:3, 3]

    def world_verts(self, p):
        return trimesh.transform_points(np.asarray(self.meshes[p].vertices), self.T[p])

    # ---------- camera ----------
    def reset_camera(self):
        pts = np.vstack([self.world_verts(p) for p in self.meshes]) if self.T else None
        lo, hi = pts.min(0), pts.max(0)
        r = float(np.linalg.norm(hi - lo)) / 2
        self.cam = {"target": ((lo + hi) / 2).tolist(), "yaw": -60.0, "pitch": 35.0,
                    "distance": r / np.tan(np.radians(VFOV / 2)) * 0.8}

    def cam_axes(self):
        y, p = np.radians(self.cam["yaw"]), np.radians(self.cam["pitch"])
        back = np.array([np.cos(p) * np.cos(y), np.cos(p) * np.sin(y), np.sin(p)])
        right = np.cross([0, 0, 1], back)
        if np.linalg.norm(right) < 1e-6:
            right = np.array([1.0, 0, 0])
        right /= np.linalg.norm(right)
        up = np.cross(back, right)
        return right, up, back

    def cam_pose(self):
        right, up, back = self.cam_axes()
        P = np.eye(4)
        P[:3, 0], P[:3, 1], P[:3, 2] = right, up, back
        P[:3, 3] = np.asarray(self.cam["target"]) + self.cam["distance"] * back
        return P

    # ---------- render ----------
    def render(self):
        import pyrender
        from PIL import Image, ImageDraw
        scene = pyrender.Scene(bg_color=[0.93, 0.93, 0.93, 1.0], ambient_light=[0.25] * 3)
        for k, p in enumerate(self.meta["parts"]):
            m = self.meshes[p].copy()
            m.apply_transform(self.T[p])
            col = [c / 255 for c in PALETTE[k % len(PALETTE)]] + [1.0]
            mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=col, metallicFactor=0.0,
                                                     roughnessFactor=0.8, doubleSided=True)
            scene.add(pyrender.Mesh.from_trimesh(m, material=mat, smooth=False))
        L = 0.3
        for axis, col in zip(np.eye(3), [(1, 0, 0), (0, 0.6, 0), (0, 0, 1)]):
            cyl = trimesh.creation.cylinder(radius=0.008, segment=[[0, 0, 0], axis * L])
            mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=list(col) + [1.0])
            scene.add(pyrender.Mesh.from_trimesh(cyl, material=mat))
        P = self.cam_pose()
        scene.add(pyrender.PerspectiveCamera(yfov=np.radians(VFOV), aspectRatio=W / H,
                                             znear=0.001 * self.cam["distance"],
                                             zfar=100 * self.cam["distance"]), pose=P)
        scene.add(pyrender.DirectionalLight(intensity=2.5), pose=P)
        key = np.eye(4)
        key[:3, :3] = trimesh.transformations.rotation_matrix(
            np.radians(-50), [1, 0, 0])[:3, :3] @ trimesh.transformations.rotation_matrix(
            np.radians(30), [0, 0, 1])[:3, :3]
        scene.add(pyrender.DirectionalLight(intensity=2.0), pose=key)
        r = pyrender.OffscreenRenderer(W, H)
        col, _ = r.render(scene)
        r.delete()
        img = Image.fromarray(col)
        d = ImageDraw.Draw(img)
        for k, p in enumerate(self.meta["parts"]):
            d.rectangle([10, 10 + 20 * k, 26, 26 + 20 * k], fill=PALETTE[k % len(PALETTE)])
            d.text((32, 12 + 20 * k), p, fill=(0, 0, 0))
        c = self.cam
        d.text((10, H - 20), f"yaw {c['yaw']:.0f}  pitch {c['pitch']:.0f}  distance "
               f"{c['distance']:.3f}   axes at origin: X red, Y green, Z blue", fill=(0, 0, 0))
        self.n_views += 1
        out = self.dir / "views" / f"{self.n_views:04d}.png"
        out.parent.mkdir(exist_ok=True)
        img.save(out)
        return str(out.resolve())


def quat_of(R):
    q = trimesh.transformations.quaternion_from_matrix(np.block([[R, np.zeros((3, 1))],
                                                                 [np.zeros((1, 3)), 1]]))
    return [round(float(x), 5) for x in q]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("cmd")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--vec", nargs=3, type=float)
    ap.add_argument("--angles", nargs=3, type=float)
    ap.add_argument("--frame", choices=["world", "camera"], default="world")
    ap.add_argument("--pivot", nargs=3, type=float)
    ap.add_argument("--position", nargs=3, type=float)
    ap.add_argument("--quat", nargs=4, type=float)
    ap.add_argument("--yaw", type=float, default=0.0)
    ap.add_argument("--pitch", type=float, default=0.0)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--pan-x", type=float, default=0.0)
    ap.add_argument("--pan-y", type=float, default=0.0)
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    env = Env(a.task)
    args = {k: v for k, v in vars(a).items() if k not in ("task",)}
    cmd = a.cmd

    if cmd == "list_objects":
        res = {"parts": env.meta["parts"], "groups": env.groups}
    elif cmd == "get_object":
        p = env.resolve(a.ids)[0]
        obb = env.meshes[p].bounding_box_oriented.primitive.extents
        res = {"id": p, "position": [round(float(x), 5) for x in env.centre(p)],
               "quaternion_wxyz": quat_of(env.T[p][:3, :3]),
               "local_box_extents": [round(float(x), 5) for x in sorted(obb, reverse=True)]}
    elif cmd in ("get_scene", "get_state"):
        res = {"conventions": env.meta["conventions"] + "; rotations X then Y then Z, degrees; "
               "quaternions (w,x,y,z); a part's position is its centre",
               "groups": env.groups, "camera": env.cam,
               "parts": {p: {"position": [round(float(x), 5) for x in env.centre(p)],
                             "quaternion_wxyz": quat_of(env.T[p][:3, :3])} for p in env.T}}
    elif cmd == "capture_scene":
        res = {"image": env.render()}
    elif cmd == "move_camera":
        if a.reset:
            env.reset_camera()
        env.cam["yaw"] = (env.cam["yaw"] + a.yaw + 180) % 360 - 180
        env.cam["pitch"] = float(np.clip(env.cam["pitch"] + a.pitch, -89, 89))
        env.cam["distance"] /= max(a.zoom, 1e-3)
        right, up, _ = env.cam_axes()
        env.cam["target"] = (np.asarray(env.cam["target"]) + a.pan_x * right
                             + a.pan_y * up).tolist()
        res = {"camera": env.cam}
    elif cmd == "translate_objects":
        v = np.asarray(a.vec)
        if a.frame == "camera":
            right, up, back = env.cam_axes()
            v = v[0] * right + v[1] * up + v[2] * back
        for p in env.resolve(a.ids):
            env.T[p][:3, 3] += v
        res = {"status": "ok"}
    elif cmd == "rotate_objects":
        ps = env.resolve(a.ids)
        R = rot_xyz(*a.angles)
        if a.frame == "camera":
            C = np.stack(env.cam_axes(), axis=1)
            R = C @ R @ C.T
        piv = np.asarray(a.pivot) if a.pivot else np.mean([env.centre(p) for p in ps], axis=0)
        G = np.eye(4)
        G[:3, :3] = R
        G[:3, 3] = piv - R @ piv
        for p in ps:
            env.T[p] = G @ env.T[p]
        res = {"status": "ok", "pivot": [round(float(x), 5) for x in piv]}
    elif cmd == "set_object_pose":
        p = env.resolve(a.ids)[0]
        R = env.T[p][:3, :3]
        if a.quat:
            q = np.asarray(a.quat) / np.linalg.norm(a.quat)
            R = trimesh.transformations.quaternion_matrix(q)[:3, :3]
        pos = np.asarray(a.position) if a.position else env.centre(p)
        env.T[p][:3, :3] = R
        env.T[p][:3, 3] = pos - R @ env.c0[p]
        res = {"status": "ok"}
    elif cmd == "group_objects":
        name, members = a.ids[0], env.resolve(a.ids[1:])
        env.groups[name] = members
        res = {"status": "ok", "group": name, "members": members}
    elif cmd == "ungroup_objects":
        env.groups.pop(a.ids[0], None)
        res = {"status": "ok"}
    elif cmd == "start_episode":
        env.started = True
        res = {"status": "ok"}
    elif cmd == "finish":
        (env.dir / "final.json").write_text(json.dumps(
            {"task": env.meta["task"], "T": {p: t.tolist() for p, t in env.T.items()}}, indent=1))
        res = {"status": "ok", "written": str((env.dir / "final.json").resolve())}
    else:
        raise SystemExit(f"unknown command {cmd}")
    env.save(cmd, args, res)
    print(json.dumps(res))


if __name__ == "__main__":
    sys.exit(main())
