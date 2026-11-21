# -*- coding: utf-8 -*-
"""第二版：让五指都能动（含小指）。在 v1 基础上：
- 过渡带往手掌侧放宽到 2cm（along -0.020 -> +0.015）
- 每条顶点取最近 2 条指链混合（而不是只取 1 条）
"""
import bpy
import csv
import numpy as np

SRC = r"G:\DragonSwordMod\03_work\work\_blends\ad_phys2.blend"
DST = r"G:\DragonSwordMod\03_work\work\_blends\ad_phys2_finger2.blend"
CSV = r"G:\DragonSwordMod\01_refs\Aria_RefPose_world.csv"

bpy.ops.wm.open_mainfile(filepath=SRC)
obj = bpy.data.objects["hanser_mesh"]
me = obj.data

pos = {}
for r in csv.DictReader(open(CSV, encoding="utf-8")):
    pos[r["name"]] = np.array([float(r["world_x"]), float(r["world_y"]), float(r["world_z"])]) / 100.0

CHAINS = {}
for side in ("l", "r"):
    lst = []
    for base in ("index", "middle", "ring", "pinky", "thumb"):
        names = [f"{base}_01_{side}", f"{base}_02_{side}", f"{base}_03_{side}"]
        p0, p1, p2 = pos[names[0]], pos[names[1]], pos[names[2]]
        p3 = p2 + (p2 - p1)
        segs = [(p0, p1, names[0]), (p1, p2, names[1]), (p2, p3, names[2])]
        lst.append({"name": base, "p0": p0, "p3": p3, "segs": segs,
                    "dir": (p3 - p0) / max(np.linalg.norm(p3 - p0), 1e-6)})
    CHAINS[side] = lst

gidx = {g.name: g.index for g in obj.vertex_groups}


def seg_dist(p, a, b):
    ab = b - a
    t = float(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-12))
    t = max(0.0, min(1.0, t))
    return float(np.linalg.norm(p - (a + ab * t)))


report = {}
changed = 0
for side in ("l", "r"):
    hand_g = gidx[f"hand_{side}"]
    chains = CHAINS[side]
    n_done = 0
    for v in me.vertices:
        w_hand = 0.0
        for g in v.groups:
            if g.group == hand_g:
                w_hand = g.weight
                break
        if w_hand < 0.5:
            continue
        p = np.array([v.co.x, v.co.y, v.co.z])
        # 每条链的最小距离
        cds = [(min(seg_dist(p, a, b) for (a, b, n) in ch["segs"]), ch) for ch in chains]
        cds.sort(key=lambda x: x[0])
        picked = cds[:2]
        # 进度 t：用最近那条链的方向
        ch = picked[0][1]
        along = float(np.dot(p - ch["p0"], ch["dir"]))
        t = max(0.0, min(1.0, (along + 0.020) / 0.035))
        t = t * t * (3 - 2 * t)
        F = 0.95 * t
        if F <= 0.02:
            continue
        # 两条链各自最近的一段 + 第二近的一段
        cand = []
        for d, chx in picked:
            segs = sorted([(seg_dist(p, a, b), n) for (a, b, n) in chx["segs"]], key=lambda x: x[0])
            cand.extend(segs[:2])
        # 去重合并
        best = {}
        for d, n in cand:
            w = 1.0 / (d + 0.002) ** 2
            if n not in best or w > best[n]:
                best[n] = w
        s = sum(best.values())
        add = {n: F * w / s for n, w in best.items()}

        new = {}
        for g in v.groups:
            nm = obj.vertex_groups[g.group].name
            w = g.weight * (1.0 - F)
            if w > 1e-5:
                new[nm] = new.get(nm, 0.0) + w
        for nm, w in add.items():
            new[nm] = new.get(nm, 0.0) + w
        items = sorted(new.items(), key=lambda kv: -kv[1])[:4]
        ssum = sum(w for _, w in items)
        if ssum <= 0:
            continue
        items = [(nm, w / ssum) for nm, w in items]
        for g in list(v.groups):
            obj.vertex_groups[g.group].remove([v.index])
        for nm, w in items:
            obj.vertex_groups[nm].add([v.index], w, 'REPLACE')
        n_done += 1
        changed += 1
        for nm, w in items:
            if nm.startswith(("index", "middle", "ring", "pinky", "thumb")):
                report[nm] = report.get(nm, 0) + (1 if w > 0.25 else 0)
    print("side %s : processed %d hand verts" % (side, n_done))

print("changed verts:", changed)
for nm in sorted(report):
    print("   %-16s %d" % (nm, report[nm]))
tot = {s: sum(v for k, v in report.items() if k.endswith("_" + s)) for s in ("l", "r")}
print("L=%d R=%d" % (tot["l"], tot["r"]))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("saved", DST)
