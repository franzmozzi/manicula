"""Try every word (and every list entry) as target at three viewport widths; report non-converging ones."""
import json, os, subprocess, sys, time, urllib.request, websocket
URL = "file://" + os.path.abspath(__file__ + "/../../../" + (sys.argv[2] if len(sys.argv) > 2 else "index.html"))
proc = subprocess.Popen(["chromium","--headless=new","--disable-gpu","--no-sandbox","--remote-debugging-port=9335","--remote-allow-origins=*",URL],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try: tabs=json.load(urllib.request.urlopen("http://127.0.0.1:9335/json")); break
        except Exception: time.sleep(0.2)
    ws=websocket.create_connection(next(t for t in tabs if t["type"]=="page")["webSocketDebuggerUrl"],suppress_origin=True)
    n=[0]
    def call(m,**p):
        n[0]+=1; ws.send(json.dumps({"id":n[0],"method":m,"params":p}))
        while True:
            r=json.loads(ws.recv())
            if r.get("id")==n[0]: return r
    ev=lambda e: call("Runtime.evaluate",expression=e,awaitPromise=True,returnByValue=True)["result"].get("result",{}).get("value")
    ev("new Promise(r=>{const t=()=>document.documentElement.dataset.ready==='true'?r():setTimeout(t,100);t();})")
    zoom = sys.argv[1] if len(sys.argv) > 1 else "100"   # usage: sweep.py [manicule %] [page, e.g. barebone.html]
    ev(f"document.documentElement.style.setProperty('--mani-zoom', '{int(zoom) / 100}')")
    for w in (375, 830, 1280):
        call("Emulation.setDeviceMetricsOverride",width=w,height=1600,deviceScaleFactor=1,mobile=w<600)
        time.sleep(0.6)
        res = ev("""(() => { const out = [];
          for (const b of maniculae) {
            const isList = b.kind === 'list', keep = b.override;
            const targets = isList ? b.items.map((_, i) => String(i + 1))
              : [...new Set(b.items.flatMap((it) => it.text.split(/[\\s;:,.]+/)).filter((x) => x.length > 2))];
            const g = b.readGeometry(); const t0 = performance.now(); let fails = [], forced = 0, maxPasses = 0;
            for (const t of targets) { b.override = t; const r = b.solve(g);
              if (!r.blocked && (r.lineIndex < 0 || r.error > 0.5)) fails.push(t + ':' + (r.error ?? 'nf'));
              if (r.forcedBreak) forced++; maxPasses = Math.max(maxPasses, r.passes); }
            b.override = keep;
            out.push({ id: b.el.id, targets: targets.length, fails: fails.slice(0, 8), nfails: fails.length, forced, maxPasses, msPerSolve: +((performance.now() - t0) / targets.length).toFixed(2) }); }
          return out; })()""")
        for r in res: print(w, json.dumps(r, ensure_ascii=False))
finally: proc.terminate()
