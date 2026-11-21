# -*- coding: utf-8 -*-
import json, struct, math, csv
import numpy as np
SRC=r"G:\DragonSwordMod\03_work\work\refsrc\ch_aria_mesh_body.glb"
d=open(SRC,"rb").read(); off=12; total=struct.unpack_from("<I",d,8)[0]; chunks=[]
while off<total:
    clen,ctype=struct.unpack_from("<II",d,off); off+=8
    chunks.append((ctype,d[off:off+clen])); off+=clen
gltf=json.loads(chunks[0][1].decode("utf-8"))
nodes=[dict(n) for n in gltf["nodes"]]
jlist=list(gltf["skins"][0]["joints"])
jname2j={nodes[n]["name"]:i for i,n in enumerate(jlist)}
rows=list(csv.DictReader(open(r"G:\DragonSwordMod\01_refs\Aria_RefPose.csv",encoding="utf-8")))
N=len(rows); names=[r["name"] for r in rows]; par=[int(r["parent"]) for r in rows]
tl=[[float(r["tx"])/100,float(r["ty"])/100,float(r["tz"])/100] for r in rows]
ql=[[float(r["qw"]),float(r["qx"]),float(r["qy"]),float(r["qz"])] for r in rows]
def tconv(t): return [t[0],t[2],t[1]]
def qconv(q): return [q[1],q[3],q[2],-q[0]]
for i,n in enumerate(names):
    if n in jname2j: continue
    jname2j[n]=len(jlist); jlist.append(len(nodes)); nodes.append({"name":n})
for k,ni in enumerate(jlist):
    nm=nodes[ni]["name"]; i=names.index(nm)
    nodes[ni]["translation"]=tconv(tl[i]); nodes[ni]["rotation"]=qconv(ql[i]); nodes[ni]["scale"]=[1,1,1]
    nodes[ni].pop("children",None)
for i,n in enumerate(names):
    if par[i]<0: continue
    nodes[jlist[jname2j[names[par[i]]]]].setdefault("children",[]).append(jlist[jname2j[n]])
roots=[jlist[jname2j[n]] for i,n in enumerate(names) if par[i]<0]
def mat_qt(t,q):
    x,y,z,w=q; n=math.sqrt(w*w+x*x+y*y+z*z) or 1; x,y,z,w=x/n,y/n,z/n,w/n
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    M=np.eye(4); M[:3,:3]=R; M[:3,3]=t; return M
W=[np.eye(4)]*len(nodes)
def walk(ni,pm):
    nd=nodes[ni]; M=pm@mat_qt(nd["translation"],nd["rotation"]); W[ni]=M
    for c in nd.get("children",[]): walk(c,M)
skel=[i for i,nd in enumerate(nodes) if "ao_LOD0" in nd.get("name","")]
base=mat_qt(nodes[skel[0]].get("translation",[0,0,0]),nodes[skel[0]].get("rotation",[0,0,0,1])) if skel else np.eye(4)
for r in roots: walk(r,base)
ibms=np.array([np.linalg.inv(W[ni]).T.flatten() for ni in jlist],dtype=np.float32)
# 网格数据
z=np.load(r"G:\DragonSwordMod\03_work\work\_data\mesh_src_aria_fing3.npz",allow_pickle=True)
pos=z["pos"]; uv=z["uv"]; bidx=z["bidx"]; bw=z["bw"]; tri=z["tri"]; gnames=list(z["gnames"])
gbone={n:i for i,n in enumerate(gnames)}
# 顶点组索引 -> 关节索引
lut=np.zeros(len(gnames),dtype=np.int64)
for i,n in enumerate(gnames):
    lut[i]=jname2j.get(n,0)
J=lut[bidx]
Wq=bw/np.maximum(bw.sum(axis=1,keepdims=True),1e-9)
posG=np.stack([pos[:,0],pos[:,2],pos[:,1]],axis=1)
uvG=np.stack([uv[:,0],1.0-uv[:,1]],axis=1)   # 恢复翻转V（与用户认可那版一致）
buf=bytearray(); views=[]; accs=[]
CT={np.dtype(np.float32):5126,np.dtype(np.uint16):5123,np.dtype(np.uint32):5125}
def add_acc(arr,typ,target=None,minmax=False):
    while len(buf)%4: buf.append(0)
    o=len(buf); b=arr.tobytes(); buf.extend(b)
    v={"buffer":0,"byteOffset":o,"byteLength":len(b)}
    if target: v["target"]=target
    views.append(v)
    a={"bufferView":len(views)-1,"componentType":CT[arr.dtype],"count":int(arr.shape[0] if arr.ndim>1 else arr.size),"type":typ}
    if minmax: a["min"]=arr.min(axis=0).tolist(); a["max"]=arr.max(axis=0).tolist()
    accs.append(a); return len(accs)-1
A_POS=add_acc(posG.astype(np.float32),"VEC3",34962,True)
A_NRM=None
A_UV=add_acc(uvG.astype(np.float32),"VEC2",34962)
A_J=add_acc(J.astype(np.uint16),"VEC4",34962)
A_W=add_acc(Wq.astype(np.float32),"VEC4",34962)
A_IBM=add_acc(ibms,"MAT4")
prims=[]
for m in sorted(np.unique(tri[:,3])):
    sel=tri[tri[:,3]==m][:,:3]
    if sel.size==0: continue
    A_I=add_acc(sel.astype(np.uint32).reshape(-1),"SCALAR",34963)
    prims.append({"attributes":{"POSITION":A_POS,"TEXCOORD_0":A_UV,"JOINTS_0":A_J,"WEIGHTS_0":A_W},"indices":A_I,"material":int(m)})
mesh_node=len(nodes); nodes.append({"name":"ch_aria_mesh_body","mesh":0,"skin":0})
gltf["nodes"]=nodes
gltf["skins"]=[{"joints":jlist,"inverseBindMatrices":A_IBM,"skeleton":jlist[0]}]
gltf["scenes"]=[{"nodes":[jlist[0],mesh_node]}]; gltf["scene"]=0
gltf["meshes"]=[{"name":"ch_aria_mesh_body","primitives":prims}]
gltf["materials"]=[{"name":"ch_aria_base_body_mi","pbrMetallicRoughness":{"baseColorFactor":[0.9,0.9,0.9,1],"metallicFactor":0,"roughnessFactor":0.8}},
 {"name":"ch_aria_base_skin_mi","pbrMetallicRoughness":{"baseColorFactor":[0.95,0.85,0.8,1],"metallicFactor":0,"roughnessFactor":0.8}},
 {"name":"ch_aria_base_hair_mi","pbrMetallicRoughness":{"baseColorFactor":[0.6,0.45,0.35,1],"metallicFactor":0,"roughnessFactor":0.8}},
 {"name":"ch_aria_base_wp_mi","pbrMetallicRoughness":{"baseColorFactor":[0.85,0.85,0.85,1],"metallicFactor":0,"roughnessFactor":0.8}}]
gltf["accessors"]=accs; gltf["bufferViews"]=views; gltf["buffers"]=[{"byteLength":len(buf)}]
js=json.dumps(gltf,separators=(",",":")).encode()
def pad4(b,c):
    while len(b)%4: b+=c
    return b
js=pad4(js,b" "); bin_=pad4(bytes(buf),b"\x00")
tot=12+8+len(js)+8+len(bin_)
out=bytearray(); out+=struct.pack("<III",0x46546C67,2,tot)
out+=struct.pack("<II",len(js),0x4E4F534A)+js
out+=struct.pack("<II",len(bin_),0x004E4942)+bin_
open(r"G:\DragonSwordMod\03_work\work\_glb\aria_fing3.glb","wb").write(out)
print("glb MB=%.2f joints=%d prims=%d verts=%d tris=%d" % (len(out)/1e6,len(jlist),len(prims),len(pos),len(tri)))