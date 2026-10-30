"""Final pipeline stage: render the built ../realm_map.html into image tiles and write the
tiled site to ../site/ (index.html, tiles/, data/, vendor/, fonts/).
Called by build.py; run alone with: python3 site_build.py
Zoom z: 2**z px per room, z1..z5 rendered; tile (z,x,y) pixel 0 = world bounds x0,y0.
Needs: playwright (+ chromium), Pillow."""
import hashlib, base64, io, json, os, re, shutil, sys, time
from PIL import Image
from playwright.sync_api import sync_playwright

ZMIN, ZMAX, TS, CHUNK = 1, 5, 256, 2048
PAPER = (0x1B, 0x22, 0x20)   # --paper, the dark map background (the map is dark mode only)
# tiles: lossless WebP by default; TILE_QUALITY=90 (say) gives smaller high-quality lossy tiles
TILE_QUALITY = int(os.environ.get('TILE_QUALITY', '0'))
K = 2 ** ZMAX
SRC = os.path.abspath('../realm_map.html')
SITE = os.path.abspath('../site')
# encoded tiles from earlier builds, by a hash of their pixels: a tile whose pixels are unchanged is copied, not encoded again
# (GitHub Actions keeps this folder between runs; TILE_CACHE= turns it off)
TILE_CACHE = os.environ.get('TILE_CACHE', os.path.abspath('../.tile_cache'))
# big area and maze names: kept live (sharp at every zoom), not baked into tiles
AREA_NAMES = ["The Forgotten Woods", "Shadow Grove", "Miden'nir", "The Maze of Trees",
              "Lost in the Swamp", "The Hidden Grove", "Ashen", "Forest", "Forest of Tears"]
CARD_KEYS = ('name', 'route', 'room', 'dir', 'note', 'kind', 'noroute', 'group', 'where', 'alt', 'card', 'hidepath', 'rhead', 'deity', 'priests', 'astral', 'astrallocal', 'deco', 'poi', 'restricted')

EXPORT_JS = '''(names)=>{
  const w=document.getElementById('world');
  const P=[...DATA.places,...((DATA.wild&&DATA.wild.places)||[])];
  const lab={};w.querySelectorAll('.plabel:not([data-opt])').forEach(t=>lab[t.dataset.i]=t);
  const pins={};w.querySelectorAll('#pins .pin:not([data-opt])').forEach(g=>pins[g.dataset.i]=g);
  const more={};w.querySelectorAll('#pins .pin[data-opt]').forEach(g=>{const m=g.transform.baseVal.consolidate().matrix,t=w.querySelector(`.plabel[data-i="${g.dataset.i}"][data-opt="${g.dataset.opt}"]`);
    (more[g.dataset.i]=more[g.dataset.i]||[]).push({opt:+g.dataset.opt,mx:+m.e.toFixed(3),my:+m.f.toFixed(3),shape:[...g.children].filter(c=>!(c.tagName==='circle'&&c.getAttribute('fill')==='transparent')).map(c=>c.outerHTML).join(''),
      label:t?Object.fromEntries([...t.attributes].filter(a=>!['class','data-i','data-opt'].includes(a.name)).map(a=>[a.name,a.value])):null})});
  const places=P.map((p,i)=>{const g=pins[i],t=lab[i];
    return {p,more:more[i]||null,shape:g?[...g.children].filter(c=>!(c.tagName==='circle'&&c.getAttribute('fill')==='transparent')).map(c=>c.outerHTML).join(''):'',
      label:t?Object.fromEntries([...t.attributes].filter(a=>!['class','data-i'].includes(a.name)).map(a=>[a.name,a.value])):null}});
  const extras=[...w.querySelectorAll('#pins > :not(.pin):not(text)')].map(e=>e.outerHTML);
  const areas=[...w.querySelectorAll('text')].filter(t=>names.includes(t.textContent)&&!t.closest('#pins'));
  const defs=new Set();areas.forEach(t=>t.querySelectorAll('textPath').forEach(tp=>{const d=document.getElementById((tp.getAttribute('href')||tp.getAttribute('xlink:href')||'').slice(1));if(d)defs.add(d.outerHTML)}));
  return {bounds:DATA.wild.bounds,places,extras,areas:areas.map(t=>t.outerHTML),defs:[...defs],jumps:DATA.wild.jumps||[]};
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
FONT_FILE = lambda fam, st, w: '%s-latin-%d-%s.woff2' % (fam.lower().replace(' ', '-'), w, st)
# the site serves the same font files itself (3.0; was Google Fonts): latin range as Google's, shown with a fallback until loaded
FONT_CSS = ''.join("@font-face{font-family:'%s';font-style:%s;font-weight:%d;font-display:swap;src:url(fonts/%s) format('woff2');"
                   "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}"
                   % (fam, st, w, FONT_FILE(fam, st, w)) for fam, st, w in FACES)
FONT_PRELOAD = ('Alegreya', 'italic', 400), ('Alegreya Sans', 'normal', 400)    # the place names and the panels: wanted at first paint
def font_page():
    import re
    h = open(SRC, encoding='utf-8').read()
    h = re.sub(r'<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>', '', h)
    css = ''.join("@font-face{font-family:'%s';font-style:%s;font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2')}" % (
        fam, st, w, base64.b64encode(open(os.path.join('fonts', FONT_FILE(fam, st, w)), 'rb').read()).decode())
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
        b = p.chromium.launch(args=['--force-color-profile=srgb'], **({'executable_path': os.environ['PW_CHROME']} if os.environ.get('PW_CHROME') else {}))   # (PW_CHROME: a local browser, for runs outside CI)
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
    opts = {'quality': TILE_QUALITY, 'method': 6} if TILE_QUALITY else {'lossless': True, 'quality': 60, 'method': 4}
    salt = json.dumps(opts, sort_keys=True).encode()
    if TILE_CACHE: os.makedirs(TILE_CACHE, exist_ok=True)
    used, reused = set(), 0
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
                if TILE_CACHE:
                    h = hashlib.sha1(salt + tile.tobytes()).hexdigest() + '.webp'; c = os.path.join(TILE_CACHE, h); used.add(h)
                    if os.path.exists(c): shutil.copyfile(c, f); reused += 1
                    else: tile.save(f, 'WEBP', **opts); shutil.copyfile(f, c)
                else: tile.save(f, 'WEBP', **opts)
                n += 1; byt += os.path.getsize(f)
        stats[z] = (n, round(byt / 1024))
    if TILE_CACHE:
        for h in os.listdir(TILE_CACHE):                                         # (only this build's tiles are kept)
            if h not in used: os.remove(os.path.join(TILE_CACHE, h))
        print('tiles reused from the cache:', reused, 'of', sum(v[0] for v in stats.values()))
    return stats

# RODPEDIA: the owner's list of areas (Oct 29): name, level range, RoDpedia link (empty: no link); matched to the cards by name
# ('The', '(Nation)', '(Arena)', case and punctuation aside), plus ALIAS where the list's name differs from the card's.
ALIAS = {'Dwarven Catacombs (Northern Entrance)': ['Dwarven Catacombs'], 'Fathomless Depths': ['Blood Sea - Fathomless Depths'],
         'Otherland': ['Otherland', 'Otherland (Northern)', 'Otherland (Southern)'], 'The Mire': ['The Mire', 'The Mire (Central)']}

def rodpedia():
    N = lambda s: re.sub(r'[^a-z0-9]', '', re.sub(r'\s*\((nation|arena)\)\s*$', '', s.lower()).replace('the ', ''))
    out = {}
    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rodpedia.tsv'), encoding='utf-8'):
        name, lvl, url = (line.rstrip('\n').split('\t') + ['', ''])[:3]
        lvl = re.sub(r'^m\s+|\s+m$', '', lvl.strip())                           # (two stray 'm's in the owner's list)
        for n in ALIAS.get(name, [name]):
            out.setdefault(N(n), {'lvl': lvl, **({'wiki': url.strip()} if url.strip() else {})})
    return lambda name: out.get(N(name))

def deitylinks():   # DEITIES: the owner's deity links (Oct 29): name, link (no level range)
    N = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
    out = {}
    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deities.tsv'), encoding='utf-8'):
        name, url = (line.rstrip('\n').split('\t') + [''])[:2]
        if url.strip(): out[N(name)] = {'wiki': url.strip()}
    return lambda name: out.get(N(name))

def main():
    t0 = time.time()
    live, mosaic = render()
    shutil.rmtree(SITE, ignore_errors=True)
    for d in ('tiles', 'data', 'vendor', 'fonts'):
        os.makedirs(os.path.join(SITE, d))
    stats = write_tiles(mosaic, os.path.join(SITE, 'tiles'))
    places, routes = [], []
    rod, dei = rodpedia(), deitylinks()
    for q in live['places']:
        p = q['p']
        c = {k: p[k] for k in CARD_KEYS if k in p and p[k] not in (None, '', [], False)}
        c.update(i=p['i'], mx=round(p['mx'], 3), my=round(p['my'], 3), shape=q['shape'], label=q['label'])
        if not p.get('deity') and rod(p['name']): c.update(rod(p['name']))
        if p.get('deity') and dei(p['name']): c.update(dei(p['name']))                       # level range + RoDpedia link (Oct 29)
        if q.get('more'): c['more'] = q['more']                                                # a place's other markers (Oct 25)
        if p.get('opts'): c['opts'] = [{k: v for k, v in o.items() if k != 'segs' and v not in (None, '', False)} for o in p['opts']]   # route options: text on the card, lines in routes.json
        places.append(c)
        routes.append({'path': r2(p['path']), **({'segs': r2(p['segs'])} if p.get('segs') else {}), **({'opts': [r2(o['segs']) for o in p['opts']]} if p.get('opts') else {}), **({'sail': r2(p['sail'])} if p.get('sail') else {})})
    J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
    files = {'places.json': J({'bounds': live['bounds'], 'zmin': ZMIN, 'zmax': ZMAX, 'tile': TS, 'places': places, 'extras': live['extras'], 'jumps': live.get('jumps') or []}),
             'areanames.json': J({'areas': live['areas'], 'defs': live['defs']}),
             'routes.json': J(routes)}
    for f in ('leaflet.js', 'leaflet.css'):
        shutil.copy(os.path.join('vendor', 'leaflet-1.9.4', f), os.path.join(SITE, 'vendor', f))
    for fam, st, w in FACES:
        shutil.copy(os.path.join('fonts', FONT_FILE(fam, st, w)), os.path.join(SITE, 'fonts'))
    fonts = ''.join('<link rel="preload" href="fonts/%s" as="font" type="font/woff2" crossorigin>\n' % FONT_FILE(*f) for f in FONT_PRELOAD) + '<style>' + FONT_CSS + '</style>'
    page = open('site_template.html', encoding='utf-8').read().replace('__VERSION__', open('VERSION').read().strip()).replace('__FONTS__', fonts)
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
    print('site written:', json.dumps({'tiles_per_level': {z: v[0] for z, v in stats.items()},
          'tiles_total': sum(v[0] for v in stats.values()), 'tiles_mb': round(sum(v[1] for v in stats.values()) / 1024, 2),
          'data_kb': {f: round(len(s.encode()) / 1024, 1) for f, s in files.items()}, 'seconds': round(time.time() - t0, 1)}))

if __name__ == '__main__':
    main()
