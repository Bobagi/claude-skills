import sys, subprocess, json
from PIL import Image
S=r"C:/Users/Gusta/AppData/Local/Temp/claude/3f86890063b11cdd/5ec50a8f-c289-4ee1-a5a2-4eea6b394ff7/scratchpad"
def render(name, tents, campos, lookat, fov=40, lighti=3.0, lightyaw=180, skyexp=1.1, skytint="0.30f,0.36f,0.42f,1f", fogd=0.006, W=3840, H=2160, lamppos=(-16,2,-12), lampi=0, mask=False, mode=None):
    s=open(S+"/shot2.cs",encoding="utf-8").read()
    ts=", ".join("new float[]{%s}"%",".join("%sf"%v for v in t) for t in tents)
    rep={"OUTNAME":name,"TENTS":ts,"FOV":"%sf"%fov,"CAMPOS":",".join("%sf"%v for v in campos),"LOOKAT":",".join("%sf"%v for v in lookat),
         "LIGHTI":"%sf"%lighti,"LIGHTYAW":"%sf"%lightyaw,"SKYEXP":"%sf"%skyexp,"SKYTINT":skytint,"FOGD":"%sf"%fogd,"RW":str(W),"RH":str(H),"LAMPPOS":",".join("%sf"%v for v in lamppos),"LAMPI":"%sf"%lampi,"PASSMODE":str(mode if mode is not None else (3 if mask else 0))}
    for k,v in rep.items(): s=s.replace(k,v)
    open(S+"/_run.cs","w",encoding="utf-8").write(s)
    out=subprocess.run([sys.executable,S+"/mcp.py","code",S+"/_run.cs"],capture_output=True,text=True).stdout
    print(out[:400])
    im=Image.open(S+"/keyart/%s.png"%name); im.resize((1280,int(1280*im.height/im.width))).save(S+"/keyart/%s_s.jpg"%name,quality=88)
