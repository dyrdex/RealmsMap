"""Compare the one-page SVG map with the tile POC. Headless Chromium, software rendering.
Usage: python3 measure.py [shot.png]   (serves ../ on :8765)"""
import json, os, sys, time, threading, http.server, functools, statistics as st
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PORT = 8765
PAGES = {'old (one SVG page)': '/realm_map.html', 'tiles (Leaflet POC)': '/site/index.html'}
VIEWS = {'desktop 1920x1080': dict(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1),
         'phone 390x844 @3x': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True)}

FT_START = '()=>{window.__ft=[];let l=performance.now();window.__ftOn=true;const f=n=>{if(!window.__ftOn)return;window.__ft.push(n-l);l=n;requestAnimationFrame(f)};requestAnimationFrame(f)}'
FT_STOP = '()=>{window.__ftOn=false;return window.__ft.slice(1)}'
TILES_IN_VIEW = '''()=>{const W=innerWidth,H=innerHeight;const t=[...document.querySelectorAll('img.leaflet-tile-loaded')].filter(i=>{const r=i.getBoundingClientRect();return r.right>0&&r.bottom>0&&r.left<W&&r.top<H&&getComputedStyle(i.parentElement.parentElement).opacity!=='0'});return t.length}'''

def ft(v):
    return {'median_ms': round(st.median(v), 1), 'p90_ms': round(sorted(v)[int(len(v) * .9)], 1), 'frames': len(v)} if v else None

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def serve():
    h = functools.partial(Q, directory=ROOT)
    s = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def run(b, pname, url, vname, vopt, shot=None):
    ctx = b.new_context(color_scheme='light', **vopt)
    pg = ctx.new_page()
    got = {'bytes': 0, 'requests': 0, 'tiles': 0}
    def on_resp(r):
        try:
            n = len(r.body())
        except Exception:
            n = 0
        got['bytes'] += n; got['requests'] += 1; got['tiles'] += '/tiles/' in r.url
    pg.on('response', on_resp)
    W, H = vopt['viewport']['width'], vopt['viewport']['height']
    t0 = time.time()
    pg.goto(f'http://127.0.0.1:{PORT}{url}', wait_until='load')
    if 'tiles' in url:
        pg.wait_for_function('window.__ready')
    pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(200)
    out = {'first_view_ms': round((time.time() - t0) * 1000), 'first_view_kb': round(got['bytes'] / 1024),
           'first_view_tiles': got['tiles'], 'dom_elements': pg.evaluate('document.querySelectorAll("*").length')}
    tiles = 'tiles' in url
    # frame driver: run fn(i) on each of n frames, then idle 500 ms; returns frame intervals
    DRIVE = """async ([kind,n,step])=>{const T=document.querySelector(%s);
      const r=T.getBoundingClientRect();const cx=r.left+r.width/2,cy=r.top+r.height/2;
      const ft=[];let last=performance.now();
      const wheel=d=>T.dispatchEvent(new WheelEvent('wheel',{deltaY:d,clientX:cx,clientY:cy,bubbles:true,cancelable:true}));
      const W=document.getElementById('world');
      const pan=dx=>{if(window.__map){__map.panBy([dx,0],{animate:false})}else{const t=W.getAttribute('transform');W.setAttribute('transform',t.replace(/translate\\(([-\\d.e]+),/,(m,x)=>'translate('+(+x-dx)+','))}};
      await new Promise(res=>{let i=0;const f=now=>{ft.push(now-last);last=now;
        if(i<n){kind==='pan'?pan(step):wheel(step);i++;requestAnimationFrame(f)}
        else{const t0=now;const g=n2=>{ft.push(n2-last);last=n2;if(n2-t0<500)requestAnimationFrame(g);else res()};requestAnimationFrame(g)}};requestAnimationFrame(f)});
      return {ft:ft.slice(1),ms:Math.round(ft.slice(1).reduce((a,b)=>a+b,0))}}""" % ("'.leaflet-container'" if tiles else "'#map'")
    SCALE = '__map.getZoom()' if tiles else '+document.getElementById("world").getAttribute("transform").match(/scale\\(([\\d.]+)\\)/)[1]'
    def drive(kind, n, step):
        r = pg.evaluate(DRIVE, [kind, n, step]); v = r['ft']
        return {'wall_ms': r['ms'], 'median_ms': round(st.median(v), 1), 'p90_ms': round(sorted(v)[int(len(v) * .9)], 1), 'worst_ms': round(max(v)), 'frames': len(v)}
    out['zoom_in'] = drive('wheel', 60, -12)          # 60 frames of wheel, about 2 zoom levels
    out['zoom_after_wheel'] = round(pg.evaluate(SCALE), 2)
    # set deep view: 32 px/room centred on Darkhaven Square
    if tiles:
        pg.evaluate('__map.setView([0,0],5,{animate:false})')
    else:
        pg.evaluate("""()=>{const W=document.getElementById('world'),s=document.getElementById('map').getBoundingClientRect();W.setAttribute('transform',`translate(${s.width/2},${s.height/2}) scale(32)`)}""")
    pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(300)
    if tiles:
        out['tiles_in_view_z5'] = pg.evaluate(TILES_IN_VIEW)
    b0 = got['bytes']; t0 = got['tiles']
    out['pan_deep'] = drive('pan', 90, 12)            # 90 frames x 12 px = 1080 px pan
    pg.wait_for_load_state('networkidle')
    out['pan_kb'] = round((got['bytes'] - b0) / 1024); out['pan_tiles'] = got['tiles'] - t0
    if shot:
        pg.screenshot(path=shot)
    out['zoom_out'] = drive('wheel', 60, 12)
    out['total_kb'] = round(got['bytes'] / 1024); out['total_tiles'] = got['tiles']
    ctx.close()
    return out

def main():
    shot = sys.argv[1] if len(sys.argv) > 1 else None
    srv = serve()
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for vn, vo in VIEWS.items():
            for pn, url in PAGES.items():
                res[f'{pn} | {vn}'] = run(b, pn, url, vn, vo, shot if (shot and 'tiles' in url and 'desktop' in vn) else None)
        b.close()
    srv.shutdown()
    json.dump(res, open(os.path.join(os.path.dirname(__file__), 'out', 'measure_report.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main()
