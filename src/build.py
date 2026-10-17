# Rebuild the map: python3 build.py  ->  writes ../realm_map.html
import subprocess, sys, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '.')
subprocess.run([sys.executable, 'extract2.py'], check=True, stdout=subprocess.DEVNULL)      # the town (writes nd2.json)
subprocess.run([sys.executable, 'fot_extract.py'], check=True, stdout=subprocess.DEVNULL)   # everything outside the town (writes fot.json)
label = open('VERSION').read().strip()
h=open('template.html').read()
nd=json.load(open('nd2.json')); w=json.load(open('fot.json')); w['trails']=[]
# town cards take the directions you gave, by where they lead (this also puts the three guilds' names on the right markers)
import apply_directions as _ad, importlib.util
sys.path.insert(0,'.')
import data as _data
print('renamed to match your directions:',_ad.apply_town(nd['places'],_ad.parse(_data.MORE_DIRECTIONS)))
for p in nd['places']:
    if p['name']=='Castle Darkhawk': p['route']=None; p['noroute']=True      # no directions from you yet
for p in w['places']:
    if p['name']=='Ofcol': p['kind']='town'                   # drawn with a walled-town emblem
from scale_regions import scale_regions
w,_st=scale_regions(w)
print('scaled the Forgotten Woods x0.8 and the Forest of Tears x1.2; trees, tufts, reeds, peaks (before, after, added):',_st)
# keep the ground around Ofcol's emblem clear of trees
import math
_o=next(p for p in w['places'] if p['name']=='Ofcol'); assert _o['dir']=='n'
_ox,_oy=_o['path'][-1][0]-0.85,_o['path'][-1][1]-0.62-0.45      # (the emblem sits 0.85 west of its room, clear of the Northern Trade Route)
for k in ('trees','tufts','hills','thorns'):
    w[k]=[q for q in w[k] if math.hypot(q[0]-_ox,q[1]-_oy)>2.1]
w['gallows']=None                                              # Gallow Hill is no longer on the map
from lake_reshape import reshape_lake
w,_lk=reshape_lake(w)
print('lake tich reshaped:',_lk)
# the arrangement you made in the map arranger (pieces moved and resized)
import glob
from arrange_apply import apply_arrangement
for _arrf in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),'arrangement_*.json'))):
    w,_ar=apply_arrangement(w,json.load(open(_arrf)))
    print('arrangement applied:',os.path.basename(_arrf),_ar['moved'])
    if os.path.basename(_arrf)=='arrangement_1.json':                # the gaps that round of moves left behind
        from gap_fill import fill_gaps
        w,_gf=fill_gaps(w)
        print('gaps filled:',_gf)
        from gap_fill import trim_lake_from_road
        w,_tr=trim_lake_from_road(w)
        print('lake pulled back from the trade route:',_tr)
        from gap_fill import smooth_lake_sw_shore
        w,_sw=smooth_lake_sw_shore(w)
        print('lake south-west shore straightened:',_sw)
        from gap_fill import bulge_lake_toward_tull
        w,_tu=bulge_lake_toward_tull(w)
        print('lake bulged toward Tullfuhrzky Manor:',_tu)
        from gap_fill import remove_village_buildings, round_tavern_bend
        w,_vb=remove_village_buildings(w,("The Falcon's Talon","Jelarid's Track Shoppe"))
        w,_tb=round_tavern_bend(w)
        print('village buildings removed:',_vb,'| tavern bend rounded:',_tb)
from west_coast import smooth_west_coast
w,_wc=smooth_west_coast(w)
print('new west coast, Forgotten Woods to the Forest of Tears:',_wc)
if os.environ.get('ASHEN_DUMP'):                                 # (used to build the layout editor)
    json.dump(w, open(os.environ['ASHEN_DUMP'], 'w'))
import json as _json
from ashen_forest import merge_saved_layout
_here=os.path.dirname(os.path.abspath(__file__))
def _ASHL():                                                       # the Ashen Forest layout as the owner saved it (room 670's move is applied by smr_merge, not here: moving it inside the Ashen merge re-rolled ~2,300 random trees)
    import json as _j
    return _j.load(open(os.path.join(_here,'ashen_layout_final.json')))
from visual_nudges import NUDGES
w,_ash=merge_saved_layout(w,_ASHL(),_json.load(open(os.path.join(_here,'ashen_editor_edges.json'))),nudges=NUDGES)
print('Ashen Forest, Eastern Trade Route and the added rooms merged from your layout:',_ash)
from af_markers import add_af_markers
w,_afm=add_af_markers(w,_ASHL(),_json.load(open(os.path.join(_here,'af_marker_routes.json'))))
print('Ashen Forest sub-area markers:',_afm)
def _ntr_layout():                                              # the Northern Trade Route layout, with the long bridge (4133-4135) where the Barren Peaks layout put it
    L=_json.load(open(os.path.join(_here,'ntr_layout_final.json'))); B=_json.load(open(os.path.join(_here,'bp_layout_final.json')))
    bp=dict(zip(B['ids'],zip(B['xs'],B['ys'])))
    for i,v in enumerate(L['ids']):
        if v in (4133,4134,4135): L['xs'][i],L['ys'][i]=bp[v]
    return L
from ntr_merge import merge_ntr
w,_ntr=merge_ntr(w,_ntr_layout(),_json.load(open(os.path.join(_here,'ntr_editor_edges.json'))))
print('Northern Trade Route merged:',_ntr)
from ntr_markers import add_ntr_subareas
w,_nsa=add_ntr_subareas(w,_ntr_layout(),_json.load(open(os.path.join(_here,'ntr_marker_routes.json'))))
print('Northern Trade Route sub-areas:',_nsa)
from dh_paths import add_darkhaven_paths
w,_dp=add_darkhaven_paths(w)
print('Darkhaven paths drawn:',_dp)
from east_shore import add_east_beach
w,_eb=add_east_beach(w,_ASHL(),_json.load(open(os.path.join(_here,'ashen_editor_edges.json'))))
print('east beach and ocean:',_eb)
from scenery import add_drawings, add_north_coast, add_dread, remove_retired_buildings, add_ashen_label
w,_rb=remove_retired_buildings(w)
print('buildings removed:',_rb)
w,_nc=add_north_coast(w)
print('ocean keep headland and north coast water:',_nc)
w,_dr=add_dread(w,_ASHL())
print('darker, denser ground:',_dr)
w,_sc=add_drawings(w,_ASHL())
print('drawings added:',_sc)
w,_al=add_ashen_label(w)
print('Ashen Forest label:',_al)
def _bp_layout():                                               # the Barren Peaks layout, with the road rooms in the Plains where the Northern Plains layout put them
    B=_json.load(open(os.path.join(_here,'bp_layout_final.json'))); N=_json.load(open(os.path.join(_here,'np_layout_final.json')))
    ER=_json.load(open(os.path.join(_here,'np_editor_edges.json')))['rooms']
    nf={r['id'] for r in ER if r.get('area')=='RD'}; pk={r['id'] for r in ER if r.get('area')=='PK'}   # road rooms, and Peaks rooms unlocked in the Plains editor
    npos={v:(x,y) for v,x,y in zip(N['ids'],N['xs'],N['ys']) if v in nf or v in pk}; old={}
    for i,v in enumerate(B['ids']):
        if v in npos:
            if v in nf and v not in (4152,4153,4154,4155): old[v]=(B['xs'][i],B['ys'][i])   # the canyon's road rooms keep the Peaks' land
            B['xs'][i],B['ys'][i]=npos[v]
    return B,old
from bp_merge import merge_bp
_B,_plains_road=_bp_layout()
from np_merge import dirt_road
_NPL=_json.load(open(os.path.join(_here,'np_layout_final.json'))); _NPE=_json.load(open(os.path.join(_here,'np_editor_edges.json')))
_dr=dirt_road(_NPL,_NPE)                                        # the Plains' wide dirt road stands for the trails of the Peaks rooms beside it
w,_bp=merge_bp(w,_B,_json.load(open(os.path.join(_here,'bp_editor_edges.json'))),plains_road=_plains_road,absorb=(_dr[0],_dr[1]))
print('Barren Peaks merged:',_bp)
from bp_markers import add_bp_subareas
w,_bsa=add_bp_subareas(w,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'bp_marker_routes.json'))),np_layout=_NPL)
print('Barren Peaks sub-areas:',_bsa)
from np_merge import merge_np
w,_np=merge_np(w,_NPL,_NPE)
print('Northern Plains merged:',_np)
from np_markers import add_np_subareas
w,_nsa=add_np_subareas(w,_NPL,_json.load(open(os.path.join(_here,'np_marker_routes.json'))))
print('Northern Plains sub-areas:',_nsa)
from az_merge import merge_az                                    # the Azure Sea Coast: now the LAST land change
w,_az=merge_az(w,_json.load(open(os.path.join(_here,'az_layout_final.json'))),_json.load(open(os.path.join(_here,'az_editor_edges.json'))),_NPL)
print('Azure Sea Coast merged:',_az)
from ft_merge import merge_ft                                    # the Forest of Tears, Lake of Tich'Pyga and Western Trade Route from the owner's layout (Oct 13)
import json as _jft
_FTL=_jft.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ft_layout_final.json'))); _FTE=_jft.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'fot_editor_edges.json')))
_SML=_jft.load(open(os.path.join(_here,'smr_layout_final.json'))); _SME=_jft.load(open(os.path.join(_here,'smr_editor_edges.json')))   # the Southern Mountain Range layout (Oct 14)
_sp=dict(zip(_SML['ids'],zip(_SML['xs'],_SML['ys']))); _ftx=dict(zip(_FTL['ids'],range(len(_FTL['ids']))))
for _r in _SME['rooms']:                                          # the Sparse Woodlands trail (Forest of Tears rooms) was moved in that editor: the forest is drawn from its new positions
    if _r.get('grp')=='ft' and _r['id'] in _ftx and _r['id'] in _sp: _FTL['xs'][_ftx[_r['id']]],_FTL['ys'][_ftx[_r['id']]]=_sp[_r['id']]
w,_ft=merge_ft(w,_FTL,_FTE)
_CDL=_json.load(open(os.path.join(_here,'cd_layout_final.json'))); _CDE=_json.load(open(os.path.join(_here,'cd_editor_edges.json')))   # the Coral Depths layout (Oct 16)
import cd_merge as _cdm
_cdp=dict(zip(_CDL['ids'],zip(_CDL['xs'],_CDL['ys'])))
for _i,_v in enumerate(_SML['ids']):                              # the Southern Mountain Range rooms the owner moved in the Coral Depths editor
    if _v in _cdm.SM_DRAWN: _SML['xs'][_i],_SML['ys'][_i]=_cdp[_v]
_WLL=_json.load(open(os.path.join(_here,'wl_layout_final.json'))); _WLE=_json.load(open(os.path.join(_here,'wl_editor_edges.json')))   # the Wastelands layout (Oct 17)
import wl_merge as _wlm
for _v,(_x,_y) in _wlm.EXTRA_HIDDEN.items():                      # rooms kept for routes, not drawn (owner, Oct 17)
    if _v not in _WLL['ids']: _WLL['ids'].append(_v); _WLL['xs'].append(_x); _WLL['ys'].append(_y); _WLL['hidden'].append(_v)
_wlp=dict(zip(_WLL['ids'],zip(_WLL['xs'],_WLL['ys'])))
_smr_win={_v:(_SML['xs'][_i],_SML['ys'][_i]) for _i,_v in enumerate(_SML['ids']) if _v in _wlm.UN}
for _i,_v in enumerate(_SML['ids']):                              # the Southern Mountain Trade Route rooms the owner moved in the Wastelands editor
    if _v in _wlm.UN: _SML['xs'][_i],_SML['ys'][_i]=_wlp[_v]
_wls={}
_cdr={}
from smr_merge import merge_smr                                    # the Southern Mountain Range, its Trade Route and links to the moved trail (Oct 14)
_cdle=_cdm.land_edit(_CDL,_CDE,_SML,_cdr); _wlle=_wlm.wl_land(_WLL,_WLE,_wls)
w,_sm=merge_smr(w,_SML,_SME,land_edit=lambda L,W,x,y:_wlle(_cdle(L,W,x,y),W,x,y),window_pos=_smr_win)
print('Southern Mountain Range merged:',_sm)
w,_cd=_cdm.merge_cd(w,_CDL,_CDE,_SML)                              # the Coral Depths: its paths, the cliff, the sea, the ground (Oct 16)
print('Coral Depths merged:',{**_cdr,**_cd})
w,_wl=_wlm.merge_wl(w,_WLL,_WLE,_wls)                            # the Wastelands, from the owner's save (Oct 17)
print('Wastelands merged:',_wl)
_cdm_ids={r['id'] for r in _CDE['rooms'] if r.get('area')=='CD'}   # (only the rooms moved in that editor: they come first for the route tracers)
_CDLm={k:[v for v,i in zip(_CDL[k],_CDL['ids']) if i in _cdm_ids] if k in ('ids','xs','ys') else _CDL[k] for k in _CDL}
from smr_markers import add_smr_subareas                          # markers + traced routes for the areas that open off the range and its trade route (Oct 14)
w,_ssa=add_smr_subareas(w,_SML,_json.load(open(os.path.join(_here,'smr_marker_routes.json'))),extra_layout=_ASHL())
print('Southern Mountain Range sub-areas:',_ssa)
print('Forest of Tears, Lake of Tich\'Pyga and Western Trade Route merged:',{k:v for k,v in _ft.items() if not k.startswith('_')})
from west_sea import add_west_sea                                # the sea along the whole west coast + the small marina on it (Oct 13)
w,_wsea=add_west_sea(w)
print('west sea and marina:',_wsea)
from pf_merge import merge_pf                                     # the Pixie Forest rooms and the moved Woods rooms 4017-4019, from the owner's save (Oct 15)
_PFL=_json.load(open(os.path.join(_here,'pf_layout_final.json')))
_pfm={r['id'] for r in _json.load(open(os.path.join(_here,'pf_editor_edges.json')))['rooms'] if r.get('area')=='PF'}   # (only the rooms moved in that editor: they come first for the route tracers)
_PFL={k:[v for v,i in zip(_PFL[k],_PFL['ids']) if i in _pfm] if k in ('ids','xs','ys') else _PFL[k] for k in _PFL}
w,_pf=merge_pf(w,_PFL,_json.load(open(os.path.join(_here,'pf_editor_edges.json'))))
print('Pixie Forest:',_pf)
from na_merge import merge_na, add_na_places                     # Angel's Landing, the Village of Edo, The Grimdog Port Authority, from the owner's save (Oct 16)
_NAL=_json.load(open(os.path.join(_here,'na_layout_final.json'))); _NAE=_json.load(open(os.path.join(_here,'na_editor_edges.json')))
w,_na=merge_na(w,_NAL,_NAE)
print('Angel\'s Landing, Edo, Grimdog:',_na)
_nam={r['id'] for r in _NAE['rooms'] if r.get('area')=='NA'}        # (only the rooms of that editor, hidden ones included: routes run through them)
_NALm={k:[v for v,i in zip(_NAL[k],_NAL['ids']) if i in _nam] if k in ('ids','xs','ys') else _NAL[k] for k in _NAL}
w,_napl=add_na_places(w,[_CDLm,_PFL,_FTL,_NPL,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'az_layout_final.json'))),_ASHL(),_SML,_NALm])   # Angel's Landing (owner, Oct 16)
print('Angel\'s Landing place:',_napl)
from route_fix import fix_routes                                 # routes along the trade routes drawn unbroken; the Ofcol Shortcut portal (owner, Oct 13)
w,_rf=fix_routes(w,[_CDLm,_PFL,_FTL,_NPL,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'az_layout_final.json'))),_ASHL(),_NALm])
print('routes traced again:',_rf)
from route_options import add_route_options                       # places with a default and alternate routes you gave (Oct 15)
w,_ro=add_route_options(w,[_CDLm,_PFL,_FTL,_NPL,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'az_layout_final.json'))),_ASHL(),_SML],_data.ROUTE_OPTIONS)
print('route options:',_ro)
from extra_places import add_extra_places                       # Suds 'n Stones, V'laresch under Mobs, A'enari (owner, Oct 15)
w,_ep=add_extra_places(w,[_CDLm,_PFL,_FTL,_NPL,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'az_layout_final.json'))),_ASHL(),_SML])
print('extra places:',_ep)
w,_cdpl=_cdm.add_cd_places(w,[_CDLm,_PFL,_FTL,_NPL,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'az_layout_final.json'))),_ASHL(),_SML])   # Coral Depths, Octopus Garden (owner, Oct 16)
print('Coral Depths places:',_cdpl)
from na_merge import grimdog_route
w,_ngr=grimdog_route(w,[_CDLm,_PFL,_FTL,_NPL,_bp_layout()[0],_ntr_layout(),_json.load(open(os.path.join(_here,'az_layout_final.json'))),_ASHL(),_SML,_NALm])   # Grimdog's route on to 21076, through the hidden port rooms (owner, Oct 16)
print('Grimdog route:',_ngr)
from md_merge import merge_md                                     # Miden'nir rooms on the painting, from the owner's save (Oct 15)
w,_md=merge_md(w,_json.load(open(os.path.join(_here,'md_layout_final.json'))),_json.load(open(os.path.join(_here,'md_editor_edges.json'))))
print('Miden\'nir rooms:',_md)
from owner_edits import apply_edits                              # lines and places the owner asked to take out (Oct 14)
w,_oe=apply_edits(w)
print('owner edits:',_oe)
for _p in w['places']:                                          # owner's renames: the place keeps its old name as its key for the label tweaks
    if _p['name']=='Ofcol': _p['key']='Ofcol'; _p['name']='New Ofcol'
w['places']=[_p for _p in w['places'] if not (_p['name']=='New Ofcol' and _p.get('key')!='Ofcol')]   # the Woods' own New Ofcol marker removed (owner, Oct 10)
from label_tweaks import place_labels
from label_tweaks import place_lake_label
w,_lb=place_labels(w)
print('labels placed:',_lb)
w,_ll=place_lake_label(w)
print('lake name placed:',_ll)
if os.environ.get('FINAL_DUMP'):                                 # (used to build the layout editors)
    json.dump(w, open(os.environ['FINAL_DUMP'], 'w'))
w['track']={k:v for k,v in w['track'].items() if not k.startswith(('ft','wt'))}    # (the Forest of Tears editor's room positions: in the FINAL_DUMP only, so realm_map.html stays as it was)
nd['wild']=w
open('../realm_map.html','w').write(h.replace('__DATA__',json.dumps(nd,separators=(',',':'))).replace('__VERSION__',label))

print('wrote realm_map.html')

# final stage: bake the terrain into image tiles and write the tiled site (../site/) and the one-file preview
if not os.environ.get('NO_TILES'):
    subprocess.run([sys.executable, 'site_build.py'], check=True)
