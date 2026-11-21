import bpy, numpy as np
SRC = r"G:\DragonSwordMod\03_work\work\_blends\ad_phys2_finger2.blend"
NPZ = r"G:\DragonSwordMod\03_work\work\_data\mesh_src_aria_fing2.npz"
bpy.ops.wm.open_mainfile(filepath=SRC)
obj = bpy.data.objects["hanser_mesh"]
me = obj.data
me.uv_layers.active = me.uv_layers["UVMap"]
for m in list(obj.modifiers):
    if m.type == 'ARMATURE':
        obj.modifiers.remove(m)
obj.parent = None
uv = me.uv_layers["UVMap"]
uvs = np.zeros((len(me.vertices), 2))
for loop in me.loops:
    uvs[loop.vertex_index] = uv.data[loop.index].uv[:]
co = np.array([[v.co.x, v.co.y, v.co.z] for v in me.vertices], dtype=np.float64)
gname = {g.index: g.name for g in obj.vertex_groups}
idx = np.zeros((len(me.vertices), 4), dtype=np.int32)
wts = np.zeros((len(me.vertices), 4))
for i, v in enumerate(me.vertices):
    gs = sorted(v.groups, key=lambda g: -g.weight)[:4]
    for j, g in enumerate(gs):
        idx[i, j] = g.group
        wts[i, j] = g.weight
    s = wts[i].sum()
    if s > 0:
        wts[i] /= s
mats = [m.name if m else "" for m in me.materials]

def bucket(n):
    s = n.lower()
    if any(x in s for x in ("hair", "后发饰", "呆毛")):
        return 2
    # 脸/眼 也走 body 槽（body 材质没有 toon matcap，观感与手臂一致）
    if any(x in s for x in ("eye", "face")):
        return 0
    if any(x in s for x in ("legs", "skin", "toenail")):
        return 1
    if any(x in s for x in ("sock", "shoe", "耳环", "环", "挂饰", "项圈", "吊坠", "飘带", "装饰", "c1-2")):
        return 3
    return 0

double_mats = ("连衣裙", "星星裙饰品", "领子内衬", "腰带")
tri = []
cnt = {0:0,1:0,2:0,3:0}
dup = 0
for p in me.polygons:
    vs = list(p.vertices)
    mname = mats[p.material_index] if p.material_index < len(mats) else ""
    b = bucket(mname)
    cnt[b] += 1
    if len(vs) == 3:
        tri.append((vs[0], vs[1], vs[2], b))
        if any(x in mname for x in double_mats):
            tri.append((vs[0], vs[2], vs[1], b)); dup += 1
    else:
        for t in range(1, len(vs) - 1):
            tri.append((vs[0], vs[t], vs[t + 1], b))
            if any(x in mname for x in double_mats):
                tri.append((vs[0], vs[t + 1], vs[t], b)); dup += 1
print("double-sided dup tris:", dup)
tri = np.array(tri, dtype=np.int32)
print("faces per bucket:", cnt)
np.savez(NPZ, pos=co, uv=uvs, bidx=idx, bw=wts, tri=tri,
         gnames=np.array([gname[i] if i in gname else "" for i in range(len(obj.vertex_groups))], dtype=object))
print("dumped verts=%d tris=%d" % (len(co), len(tri)))
