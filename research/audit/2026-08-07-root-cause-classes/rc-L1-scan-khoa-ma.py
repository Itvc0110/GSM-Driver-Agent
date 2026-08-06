import ast, pathlib, yaml
ROOT = pathlib.Path.cwd()
cfg = yaml.safe_load((ROOT/"configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
def exists(d):
    n=cfg
    for p in d.split("."):
        if not isinstance(n,dict) or p not in n: return False
        n=n[p]
    return True
def recv(node):
    v=node.func.value
    if isinstance(v,ast.Name): return v.id
    if isinstance(v,ast.Attribute): return v.attr
    if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute): return v.func.attr
    return ""
CFG_RECV={"cfg","config","_cfg","conf"}
hits=[]
for pat in ("src/**/*.py","scripts/*.py","ui/backend/app/**/*.py","tests/*.py","ui/backend/tests/*.py"):
    for f in ROOT.glob(pat):
        try: tree=ast.parse(f.read_text(encoding="utf-8",errors="replace"))
        except SyntaxError: continue
        for n in ast.walk(tree):
            if not (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                    and n.func.attr=="get" and n.args): continue
            a0=n.args[0]
            if not (isinstance(a0,ast.Constant) and isinstance(a0.value,str)): continue
            k=a0.value
            if "." not in k: continue
            if recv(n) not in CFG_RECV: continue
            if exists(k): continue
            d=ast.unparse(n.args[1]) if len(n.args)>1 else "<<KeyError>>"
            hits.append(f"{f.relative_to(ROOT).as_posix()}:{n.lineno}  cfg.get('{k}')  KHONG TON TAI -> {d}")
for h in sorted(set(hits)): print(h)
print(f"\nTONG {len(set(hits))}")
