"""Final pipeline stage: render the built ../realm_map.html into image tiles and write the
tiled site to ../site/ (index.html, tiles/, data/, vendor/) and the single-file preview
../realm_map_preview.html (everything inlined, for publishing as one page).
Called by build.py; run alone with: python3 site_build.py
Zoom z: 2**z px per room, z1..z5 rendered; tile (z,x,y) pixel 0 = world bounds x0,y0.
Needs: playwright (+ chromium), Pillow."""
import hashlib, base64, io, json, os, shutil, sys, time
from PIL import Image
from playwright.sync_api import sync_playwright

ZMIN, ZMAX, TS, CHUNK = 1, 5, 256, 2048
PAPER = (0x1B, 0x22, 0x20)   # --paper, the dark map background (the map is dark mode only)
# tiles: lossless WebP by default; TILE_QUALITY=90 (say) gives smaller high-quality lossy tiles
TILE_QUALITY = int(os.environ.get('TILE_QUALITY', '0'))
K = 2 ** ZMAX
SRC = os.path.abspath('../realm_map.html')
SITE = os.path.abspath('../site')
PREVIEW = os.path.abspath('../realm_map_preview.html')
# big area and maze names: kept live (sharp at every zoom), not baked into tiles
AREA_NAMES = ["The Forgotten Woods", "Shadow Grove", "Miden'nir", "The Maze of Trees",
              "Lost in the Swamp", "The Hidden Grove", "Ashen", "Forest", "Forest of Tears"]
CARD_KEYS = ('name', 'route', 'room', 'dir', 'note', 'kind', 'noroute', 'group', 'where', 'alt')

EXPORT_JS = '''(names)=>{
  const w=document.getElementById('world');
  const P=[...DATA.places,...((DATA.wild&&DATA.wild.places)||[])];
  const lab={};w.querySelectorAll('.plabel').forEach(t=>lab[t.dataset.i]=t);
  const pins={};w.querySelectorAll('#pins .pin').forEach(g=>pins[g.dataset.i]=g);
  const places=P.map((p,i)=>{const g=pins[i],t=lab[i];
    return {p,shape:g?[...g.children].filter(c=>!(c.tagName==='circle'&&c.getAttribute('fill')==='transparent')).map(c=>c.outerHTML).join(''):'',
      label:t?Object.fromEntries([...t.attributes].filter(a=>!['class','data-i'].includes(a.name)).map(a=>[a.name,a.value])):null}});
  const extras=[...w.querySelectorAll('#pins > :not(.pin):not(text)')].map(e=>e.outerHTML);
  const areas=[...w.querySelectorAll('text')].filter(t=>names.includes(t.textContent)&&!t.closest('#pins'));
  const defs=new Set();areas.forEach(t=>t.querySelectorAll('textPath').forEach(tp=>{const d=document.getElementById((tp.getAttribute('href')||tp.getAttribute('xlink:href')||'').slice(1));if(d)defs.add(d.outerHTML)}));
  return {bounds:DATA.wild.bounds,places,extras,areas:areas.map(t=>t.outerHTML),defs:[...defs]};
}'''

HIDE_JS = '''(names)=>{
  const st=document.createElement('style');
  st.textContent='html,body{background:#1B2220!important;margin:0;overflow:hidden}body>*{visibility:hidden}'+
    'svg#map{visibility:visible!important;position:fixed!important;left:0;top:0;width:%dpx!important;height:%dpx!important;z-index:2147483647}';
  document.head.appendChild(st);
  const w=document.getElementById('world');
  ['#pins','#routeLayer'].forEach(s=>w.querySelector(s).style.display='none');
  [...w.querySelectorAll('text')].filter(t=>names.includes(t.textContent)).forEach(t=>t.style.display='none');
  document.body.appendChild(document.getElementById('map'));
}''' % (CHUNK, CHUNK)

# The page's fonts (Alegreya, as served by Google Fonts), embedded from src/fonts so the bake and the
# label solver use the same letter shapes a visitor sees. The page script runs only after they load.
FACES = [('Alegreya', 'normal', w) for w in (400, 600, 700)] + [('Alegreya', 'italic', w) for w in (400, 600)] + \
        [('Alegreya Sans', 'normal', w) for w in (400, 500, 700)]
def font_page():
    import re
    h = open(SRC, encoding='utf-8').read()
    h = re.sub(r'<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>', '', h)
    css = ''.join("@font-face{font-family:'%s';font-style:%s;font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2')}" % (
        fam, st, w, base64.b64encode(open(os.path.join('fonts', '%s-latin-%d-%s.woff2' % (fam.lower().replace(' ', '-'), w, st)), 'rb').read()).decode())
        for fam, st, w in FACES)
    h = re.sub(r'<html([^>]*)>', r'<html\1 data-theme="dark">', h, count=1)   # dark only (forced as well as the default)
    h = h.replace('</head>', '<style>' + css + '</style></head>', 1)
    i = h.index('<script>\nconst DATA=')
    h = h[:i] + '<script type="text/x-deferred" id="__main">' + h[i + 8:]
    loads = ','.join('document.fonts.load("%s %d 1em \\"%s\\"")' % (st, w, fam) for fam, st, w in FACES)
    h = h.replace('</body>', '<script>Promise.all([%s]).then(()=>{const s=document.createElement("script");'
                  's.textContent=document.getElementById("__main").textContent;document.body.appendChild(s);window.__booted=true})</script></body>' % loads, 1)
    assert 'fonts.googleapis' not in h
    path = '/tmp/realm_map_fontpage.html'
    open(path, 'w', encoding='utf-8').write(h)
    return path

def r2(v):
    return [r2(x) for x in v] if isinstance(v, list) else round(v, 2)

def render():
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--force-color-profile=srgb'])
        pg = b.new_page(viewport={'width': CHUNK, 'height': CHUNK}, device_scale_factor=1, color_scheme='dark')
        pg.goto('file://' + font_page())
        pg.wait_for_function('window.__booted', timeout=60000); pg.wait_for_timeout(300)
        assert pg.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--paper").trim().toUpperCase()==="#1B2220"'), 'not dark'
        assert pg.evaluate('document.fonts.check("italic 400 1em Alegreya") && document.fonts.check("400 1em \\"Alegreya Sans\\"")'), 'fonts not loaded'
        live = pg.evaluate(EXPORT_JS, AREA_NAMES)
        pg.evaluate(HIDE_JS, AREA_NAMES)
        x0, y0, x1, y1 = live['bounds']
        Wp, Hp = int((x1 - x0) * K), int((y1 - y0) * K)
        mosaic = Image.new('RGB', (Wp, Hp), PAPER)
        for cy in range(0, Hp, CHUNK):
            for cx in range(0, Wp, CHUNK):
                pg.evaluate(f'''()=>new Promise(r=>{{document.getElementById('world').setAttribute('transform',
                  'translate({-x0*K-cx},{-y0*K-cy}) scale({K})');requestAnimationFrame(()=>requestAnimationFrame(r))}})''')
                mosaic.paste(Image.open(io.BytesIO(pg.screenshot())).convert('RGB'), (cx, cy))
        b.close()
    return live, mosaic

def write_tiles(mosaic, root):
    stats, img = {}, mosaic
    for z in range(ZMAX, ZMIN - 1, -1):
        if z < ZMAX:
            img = img.resize((-(-img.width // 2), -(-img.height // 2)), Image.LANCZOS)
        n = byt = 0
        for ty in range(-(-img.height // TS)):
            for tx in range(-(-img.width // TS)):
                tile = Image.new('RGB', (TS, TS), PAPER)
                tile.paste(img.crop((tx * TS, ty * TS, min(img.width, (tx + 1) * TS), min(img.height, (ty + 1) * TS))), (0, 0))
                d = os.path.join(root, str(z), str(tx)); os.makedirs(d, exist_ok=True)
                f = os.path.join(d, f'{ty}.webp')
                tile.save(f, 'WEBP', **({'quality': TILE_QUALITY, 'method': 6} if TILE_QUALITY else {'lossless': True, 'quality': 60, 'method': 4}))
                n += 1; byt += os.path.getsize(f)
        stats[z] = (n, round(byt / 1024))
    return stats

def main():
    t0 = time.time()
    live, mosaic = render()
    shutil.rmtree(SITE, ignore_errors=True)
    for d in ('tiles', 'data', 'vendor'):
        os.makedirs(os.path.join(SITE, d))
    stats = write_tiles(mosaic, os.path.join(SITE, 'tiles'))
    places, routes = [], []
    for q in live['places']:
        p = q['p']
        c = {k: p[k] for k in CARD_KEYS if k in p and p[k] not in (None, '', [], False)}
        c.update(i=p['i'], mx=round(p['mx'], 3), my=round(p['my'], 3), shape=q['shape'], label=q['label'])
        if p.get('opts'): c['opts'] = [{k: v for k, v in o.items() if k != 'segs' and v not in (None, '', False)} for o in p['opts']]   # route options: text on the card, lines in routes.json
        places.append(c)
        routes.append({'path': r2(p['path']), **({'segs': r2(p['segs'])} if p.get('segs') else {}), **({'opts': [r2(o['segs']) for o in p['opts']]} if p.get('opts') else {})})
    J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
    files = {'places.json': J({'bounds': live['bounds'], 'zmin': ZMIN, 'zmax': ZMAX, 'tile': TS, 'places': places, 'extras': live['extras']}),
             'areanames.json': J({'areas': live['areas'], 'defs': live['defs']}),
             'routes.json': J(routes)}
    for f, s in files.items():
        open(os.path.join(SITE, 'data', f), 'w', encoding='utf-8').write(s)
    for f in ('leaflet.js', 'leaflet.css'):
        shutil.copy(os.path.join('vendor', 'leaflet-1.9.4', f), os.path.join(SITE, 'vendor', f))
    page = open('site_template.html', encoding='utf-8').read().replace('__VERSION__', open('VERSION').read().strip())
    # a stamp of this build in the tile and data folder names (tiles/<stamp>/z/x/y.webp, data/<stamp>/...), so neither a browser nor the
    # Pages CDN can show tiles or data saved from an older build (a ?v= query was not enough: Oct 12, zoomed-in tiles stayed old)
    stamp = hashlib.sha1(open(SRC, 'rb').read() + ''.join(files.values()).encode()).hexdigest()[:10]
    os.rename(os.path.join(SITE, 'tiles'), os.path.join(SITE, '_tiles')); os.makedirs(os.path.join(SITE, 'tiles'))
    os.rename(os.path.join(SITE, '_tiles'), os.path.join(SITE, 'tiles', stamp))
    os.makedirs(os.path.join(SITE, 'data', stamp))
    for f, s in files.items():
        open(os.path.join(SITE, 'data', stamp, f), 'w', encoding='utf-8').write(s)
    for a, b in (("'tiles/{z}/{x}/{y}.webp'", "'tiles/" + stamp + "/{z}/{x}/{y}.webp'"), ("fetch('data/'+f)", "fetch('data/" + stamp + "/'+f)")):
        assert page.count(a) == 1; page = page.replace(a, b)
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(page)
    # single-file preview: same page with Leaflet, data and tiles inlined
    tiles = {}
    for z in range(ZMIN, ZMAX + 1):
        for dx in sorted(os.listdir(os.path.join(SITE, 'tiles', stamp, str(z))), key=int):
            for fy in sorted(os.listdir(os.path.join(SITE, 'tiles', stamp, str(z), dx)), key=lambda s: int(s[:-5])):
                tiles[f'{z}/{dx}/{fy[:-5]}'] = base64.b64encode(open(os.path.join(SITE, 'tiles', stamp, str(z), dx, fy), 'rb').read()).decode()
    rd = lambda f: open(os.path.join(SITE, f), encoding='utf-8').read()
    safe = lambda s: s.replace('</', '<\\/')
    pv = page.replace('<link rel="stylesheet" href="vendor/leaflet.css">', '<style>' + rd('vendor/leaflet.css') + '</style>')
    pv = pv.replace('<script src="vendor/leaflet.js"></script>', '<script>' + safe(rd('vendor/leaflet.js')) + '</script>\n<script>window.__INLINE={' +
                    ','.join(f'"{k}":{safe(v)}' for k, v in files.items()) + ',"tiles":' + J(tiles) + '};</script>')
    assert pv.count('window.__INLINE={') == 1 and '<style>' in pv
    open(PREVIEW, 'w', encoding='utf-8').write(pv)
    print('site written:', json.dumps({'tiles_per_level': {z: v[0] for z, v in stats.items()},
          'tiles_total': sum(v[0] for v in stats.values()), 'tiles_mb': round(sum(v[1] for v in stats.values()) / 1024, 2),
          'data_kb': {f: round(len(s.encode()) / 1024, 1) for f, s in files.items()},
          'preview_mb': round(os.path.getsize(PREVIEW) / 1048576, 2), 'seconds': round(time.time() - t0, 1)}))

if __name__ == '__main__':
    main()
