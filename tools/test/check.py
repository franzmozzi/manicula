"""Drive headless chromium over CDP in real time: change the controls and viewport of index.html and
measure fingertip alignment after each step.  usage: check.py [url]"""
import json, subprocess, sys, time, urllib.request, websocket
URL = sys.argv[1] if len(sys.argv) > 1 else "file://" + __import__("os").path.abspath(__file__ + "/../../../index.html")
proc = subprocess.Popen(["chromium", "--headless=new", "--disable-gpu", "--no-sandbox", "--remote-debugging-port=9333", "--remote-allow-origins=*",
                         "--window-size=1280,1600", URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json")); break
        except Exception: time.sleep(0.2)
    page = next(t for t in tabs if t["type"] == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], suppress_origin=True)
    n = [0]
    def call(method, **params):
        n[0] += 1; ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == n[0]: return m
    def ev(expr):
        r = call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        return r["result"].get("result", {}).get("value", r)
    call("Runtime.enable")
    def viewport(w): call("Emulation.setDeviceMetricsOverride", width=w, height=1600, deviceScaleFactor=1, mobile=w < 600)
    ev("new Promise(r => { const t = () => document.documentElement.dataset.ready === 'true' ? r() : setTimeout(t, 100); t(); })")
    ev(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'measure.js')).read())
    steps = [
        ("initial", ""),
        # alternative targets taken from the page itself, so the steps follow the content file
        ("alt targets: 4th/2nd suggestion, item 5, 2nd suggestion", "const opt = (id, n) => document.querySelectorAll(`#${id} option`)[n].value; set('target-1', opt('targets-1', 3)); set('target-2', opt('targets-2', 1)); set('item-3', '5'); set('target-4', opt('targets-4', 1))"),
        ("col 420 (ResizeObserver)", "set('col-w', 420)"),
        ("finger-pad 40", "set('finger-pad', 40)"),
        ("manicule 150%", "set('mani-zoom', 150)"),
        ("manicule 50%", "set('mani-zoom', 50)"),
        ("viewport 375 (media query)", "VIEWPORT:375"),
        ("viewport 1000", "VIEWPORT:1000"),
    ]
    if not ev("!!document.getElementById('controls')"):   # barebone page: no controls, only viewports
        steps = [st for st in steps if not st[1] or st[1].startswith("VIEWPORT:")]
    steps.append(("block geometry", "GEOM"))
    for name, js in steps:
        if js.startswith("VIEWPORT:"): viewport(int(js.split(':')[1]))
        elif js == "GEOM":
            print("== block geometry (per-block --finger-pad / --bleed as the engine reads them)")
            for row in ev("maniculae.map((b) => { const cs = getComputedStyle(b.el); return `${b.el.id} ${b.side} scale ${b.scale} pad ${cs.getPropertyValue('--finger-pad')} bleed ${cs.getPropertyValue('--bleed')}`; })"):
                print("   ", row)
            continue
        elif js: ev(js)
        time.sleep(0.8)
        m = ev("measure()")
        if "vw" not in m: print("measure failed:", json.dumps(m)[:600]); break
        print("==", name, "vw", m["vw"], "sw", m["sw"])
        for b in m["blocks"]:
            print("   ", b["id"], b["status"], "| gap", b["gap"], "| outOfCol", b["outOfCol"], "| overlaps", b["overlaps"], "| segOk", b["segOk"], "| img", b["imgW"], b["imgL"], b["imgR"])
finally:
    proc.terminate()
