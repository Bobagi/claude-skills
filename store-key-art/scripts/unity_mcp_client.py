"""Cliente minimo do MCP for Unity por HTTP.
uso: python mcp.py tools | tool <nome> <json> | code <arquivo.cs> | resource <uri>"""
import json, sys, urllib.request, os

URL = "http://127.0.0.1:8080/mcp"
SESS = os.path.join(os.path.dirname(__file__), ".mcp_session")


def post(payload, sid=None):
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if sid:
        req.add_header("mcp-session-id", sid)
    with urllib.request.urlopen(req, timeout=600) as r:
        sid2 = r.headers.get("mcp-session-id") or sid
        body = r.read().decode("utf-8", "replace")
    msgs = []
    if body.lstrip().startswith("{"):
        msgs.append(json.loads(body))
    else:
        for line in body.splitlines():
            if line.startswith("data:"):
                try:
                    msgs.append(json.loads(line[5:].strip()))
                except Exception:
                    pass
    return sid2, msgs


def session():
    if os.path.exists(SESS):
        return open(SESS).read().strip()
    sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "cli", "version": "1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    open(SESS, "w").write(sid)
    return sid


def call(method, params):
    sid = session()
    try:
        _, msgs = post({"jsonrpc": "2.0", "id": 2, "method": method, "params": params}, sid)
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            os.remove(SESS)
            sid = session()
            _, msgs = post({"jsonrpc": "2.0", "id": 2, "method": method, "params": params}, sid)
        else:
            raise
    for m in msgs:
        if "result" in m:
            res = m["result"]
            if isinstance(res, dict) and "content" in res:
                for c in res["content"]:
                    print(c.get("text", c))
            else:
                print(json.dumps(res, indent=1)[:20000])
        elif "error" in m:
            print("ERROR", m["error"])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "tools":
        sid = session()
        _, msgs = post({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}, sid)
        for m in msgs:
            for t in m.get("result", {}).get("tools", []):
                print(t["name"])
    elif a[0] == "schema":
        sid = session()
        _, msgs = post({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}, sid)
        for m in msgs:
            for t in m.get("result", {}).get("tools", []):
                if t["name"] == a[1]:
                    print(json.dumps(t["inputSchema"], indent=1)[:4000])
    elif a[0] == "tool":
        call("tools/call", {"name": a[1], "arguments": json.loads(a[2])})
    elif a[0] == "code":
        call("tools/call", {"name": "execute_code", "arguments": {"action": "execute", "code": open(a[1], encoding="utf-8").read()}})
    elif a[0] == "resource":
        call("resources/read", {"uri": a[1]})
