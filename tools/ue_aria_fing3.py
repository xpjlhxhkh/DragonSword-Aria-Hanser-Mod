import unreal
import os

LOG = r"G:\DragonSwordMod\03_work\work\_logs\ue_aria_fing3.txt"
GLB = r"G:\DragonSwordMod\03_work\work\_glb\aria_fing3.glb"
STEM = "aria_fing3"
MD = "/Game/Art/Character/Player/DS_Aria/Meshs"
MATS = ["M_body", "M_skin", "M_hair", "M_wp"]


def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")


if not os.path.exists(GLB):
    raise SystemExit("glb missing: " + GLB)
W("GLB = %s  size=%d" % (GLB, os.path.getsize(GLB)))

eas = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

for p in [MD + "/ch_aria_mesh_body", MD + "/ch_aria_mesh_body_Skeleton",
          MD + "/" + STEM, MD + "/" + STEM + "_Skeleton", MD + "/" + STEM + "_PhysicsAsset"]:
    if eas.does_asset_exist(p):
        eas.delete_asset(p)
        W("deleted " + p)

t = unreal.AssetImportTask()
t.filename = GLB
t.destination_path = MD
t.replace_existing = True
t.automated = True
t.save = True
AT.import_asset_tasks([t])

if not eas.does_asset_exist(MD + "/" + STEM):
    raise SystemExit("import failed")
W("imported=True")

if eas.does_asset_exist(MD + "/" + STEM + "_Skeleton"):
    W("sk=%s" % eas.rename_asset(MD + "/" + STEM + "_Skeleton", MD + "/ch_aria_mesh_body_Skeleton"))
W("mesh=%s" % eas.rename_asset(MD + "/" + STEM, MD + "/ch_aria_mesh_body"))
if eas.does_asset_exist(MD + "/" + STEM + "_PhysicsAsset"):
    W("phys=%s" % eas.rename_asset(MD + "/" + STEM + "_PhysicsAsset", MD + "/aria_uv_PhysicsAsset"))

mesh = eas.load_asset(MD + "/ch_aria_mesh_body")
if mesh is None:
    raise SystemExit("mesh load failed")

slots = mesh.get_editor_property("materials")
W("slots=%d" % len(slots))
new = []
for i, s in enumerate(slots):
    mat = eas.load_asset(MD + "/" + MATS[i]) if i < len(MATS) else None
    st = s.copy()
    st.set_editor_property("material_interface", mat)
    new.append(st)
    W("  slot[%d] <- %s (%s)" % (i, MATS[i] if i < len(MATS) else "?", mat))
mesh.set_editor_property("materials", new)
eas.save_loaded_asset(mesh)

try:
    W("skeleton=%s" % (mesh.get_editor_property("skeleton").get_name() if mesh.get_editor_property("skeleton") else "NULL"))
except Exception as e:
    W("skeleton read EXC %s" % e)
W("done")
