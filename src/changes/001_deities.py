"""Owner, Oct 26: deities. No pin on the map for a deity; the site shows its locations (purple markers, site_template DEITY) only
while the deity is selected, and its card lists them; picking one draws its route. Each location: who (the deity itself, or its Naos),
the sub-area it is in, the owner's directions (numbered form, never edited; notes inside them kept word for word, skipped when tracing).
A line is traced from Darkhaven Square over the drawn rooms, as far as the map goes (owner, Oct 26); spacer rooms are followed by their one
other exit (as applied v2.9/019). Where two drawn rooms in a row are over 100 apart (a sea crossing) the line breaks into two pieces, unless
they are one of the route jumps (dashed arc). The location's marker is the line's end, unless the owner named a spot (MARK):
  ('sub', place)  on that place's marker: the line stops at its room nearest the marker and is joined to it
  ('room', id)    on that room: the line stops there
  ('place', name) on that place's marker, no line (the card shows `text` or the directions)
Tirebaen (a mob before) keeps its old directions, line and marker spot for its own location (owner)."""
import math, re
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
D, N = 'deity', 'naos'
DEITIES = [   # deity, [(who, sub-area, owner's directions, marker spot or None, card text or None)]
    ("A'enari", [
        (D, 'Pixie Forest', '#8 e;ne;ne;ne;#3 e;ne;e;ne;#2 e;#5 n;sw;nw;w;#4 n;enter;ne;w', None, None),
        (D, "King's Castle", '#8 e;se;se;s;se;se;se;se;ne;ne;e;ne;ne;e;#2 s;sw;s;se;s;se;#2 e;ne;ne;e;open nw;nw;w;ne;w', ('sub', "King's Castle"), None),
        (N, 'Emerald Hills', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#5 sw;nw;n;ne;nw;#2 n;ne;n;e;#3 ne;#5 e;ne;e;n;ne;', None, None),
        (N, 'Town of Solace', 'nw;#2 w;#4 n;e;look painting;open n;n;nw;#2 n;nw;w;nw;nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;ne;#4 n;#4 e;n', None, None)]),
    ("Vl'aresch", [
        (D, "Forest of Tears (Sesuadra's Rift)", '#9 w;nw;#2 w;nw;w;#2 n;#3 nw;w;#4 sw;w;#2 nw;w;sw;#13 w;n;cauldron;s;w', None, None),
        (N, 'Dragon Cult', '#4 s;e;n;say idolizer of dragons;#2 n;d;#2 w;n;open e;e', None, None),
        (N, 'Tower of Despair', '', ('place', 'Tower of Despair'), "Teleport. Haven't found how to open the door from the tower")]),
    ("Bron'Trel", [
        (D, 'Scourge of Time', '#8 u;n;unlock n;open n;n; (track Malsangre);say back in time; #3 e;open n;#2 n;#2 e', None, None),
        (N, 'Forgotten Woods', '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;e;#2 se;#4 e;n;#2 e;se;e;ne;e;se;ne;#4 n;nw;n;nw;#2 n;nw;ne;n;#2 ne;#3 n;u;nw;#2 w;nw;w;#2 nw;#2 w;nw;sw;d;e;d;#2 sw;d;e;se;e;se;ne', None, None),
        (N, 'The Keep of Mahn-Tor', '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;#2 sw;#2 s;#2 ne;n;nw;w;#2 nw;w;#3 nw;#3 w;se;w;sw;w;u;nw;#3 w;#3 nw;#3 w;sw;#2 s;se;s;w', None, None)]),
    ('LaChte', [
        (D, 'The Ancient City of Aurora', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#4 sw;#4 s;#2 sw;s;#2 sw;s;sw;#5 s;#3 e;#2 s;enter;n;#2 w;s;d;u;enter;scry for "The Unimaginable", scry for "The Unthinkable".', None, None),
        (D, "Barrik's Keep", '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;s;s;sw;sw;s;s;ne;ne;n;nw;w;nw;nw;w;#3 nw;#3 w;nw;nw;#3 w;s;e;#3 ne;se;#4 e;se;se;#3 e;n;#5 ne;#4 nw;ne;e;#3 ne;#4 e;#4 n;#3 e;n;nw;nw;w;w;#4 sw;#3 w;nw;w;w;#4 sw;#4 n;e;open rug;d;#3 n;open u;u;open n;#6 n;sw;open n;#2 n;scry for "The Unimaginable", scry for "The Unthinkable"', None, None),
        (N, 'Shadowport', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#4 sw;#4 s;#5 se;#2 s;d;s;se;s;#3 sw;u;#2 w;n;nw;#2 n;sw;s;sw;se;e;ne;open wall;#3 n;w;open w;#2 w;n;w;#2 n;open d;#2 d;#6 s;w;s;#3 w', None, None),
        (N, 'Otherland', 'nw;#2 w;#4 n;e;look painting;n;nw;#2 n;nw;w;#2 nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;ne;#3 w;ne;nw;n;nw;w;nw;n;d;se;e;se;s;#2 u', None, None)]),   # ends on Out in the Cold
    ("Mak'kor", [
        (D, 'Realm of Worship', '#8 s;#2 w;say story;#2 s;#2 w;#2 n;#2 w;#2 n;e;ne;#4 se;#2 s;se;d;ne;n;ne;#5 n; open n; (DANGER! DANGER!) #2 n;e;#2 n;e;se', None, None),
        (N, 'Unholy Grounds', 'nw;#2 w;#4 n;e;look painting;s;#4 e;#3 s;#2 se;sw;s;e;s;w;#4 s', ('graves', 'Unholy Grounds'), None)]),
    ('Bael', [
        (D, 'Underworld', '#9 w;sw;#4 w;s;sw;#5 w;sw;#4 w;#3 s;e;s;e;s;d;s;give 50k coin wicorith;#2 s (into maze, scan/scry for The Bone Chamber)', None, None),
        (N, "Thul Ab'hara", '#13 s;#2 e;#2 u;e;#3 se;d;s;#2 se;#4 s;#3 se;sw;s;#2 sw;w;#2 sw;nw;#2 d;sw;d;s;#3 se;s;sw;se;s;#3 w;#3 s;e', None, None)]),
    ('Sarane', [   # Tower of Enlightenment: two ways (owner, Oct 26 later)
        (D, 'Tower of Enlightenment (Portal)', '#52 w;c portal hanged;enter;#3 e;u;portal;u;n', ('jump', 'Tower of Enlightenment', '#52 w'), None),
        (D, 'Tower of Enlightenment (Walking)', '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;e;#2 se;#4 e;n;nw;#2 n;sw;e;ne;#2 s;se;s;se;s;#4 w;#2 sw;s;#2 w;s;sw;s;w;s;sw;s;se;#2 e;ne;se;#2 e;se;d;w;sw;#3 n;open n;n;open n;n;#4 n;kill anubis for key;unlock n;open n;#2 n;e;#4 u;portal;u;enter', ('sub', 'Tower of Enlightenment'), None),
        (N, 'The Shire', '#9 w;nw;#2 w;nw;#3 n;#2 w;#4 n;ne', None, None),
        (N, 'Ashen Forest/Forgotten Woods', '#6 n;#2 e;n;#3 ne;se;e;se;e;nw;#2 n;#2 ne;w;#2 nw;e;n;se', None, None)]),
    ('Wirawyth', [
        (D, 'Morgul Vale', '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;#2 sw;#2 s;#2 ne;n;nw;w;#2 nw;w;#3 nw;#3 w;#2 nw;#3 w;#6 nw;n;#2 nw;n;ne;s;se;sw;n;u; (doorbash e) ;e;enter;ne;e', None, None),
        (N, 'Dwarven Catacombs', '#8 e;se;se;s;#3 se;e;ne;ne;n;ne;ne;n;nw;n;ne;w;push leaves;pull leaves;e;e;n;n;u;open u;u;open u;u;e;d;d;#4 n;open n;n;open n;n;d;#4 s;#2 e;s;w', ('sub', 'Dwarven Catacombs'), None)]),
    ('Estathius', [
        (D, 'Crystalmir Lake', 'nw;w;w;n;n;n;n;e;look painting;open n;n;#28 w;#2 s;w;sw;#2 s;#4 w;#2 nw;#3 w;#5 sw;n;d;#3 w;d; (NAVIGATE MAZE); #2u;ne;se;w', None, None),
        (N, 'Coral Depths', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#2 e;u;#3 e;ne;#3 e;s;se;open n;n', None, None)]),
    ('Kardis', [
        (D, 'Sea of Sorrows', '#6 s;ne;#2 s;se;#2 e;s;#2 sw; s;#2 e;u;#3 e;#3 s;se;#3 e;s;#2 se;s;sw;#2 s;w;sw;d;e;se;d;u;sw;s;w;d;se;d;e', ('room', 6650), None),
        (N, 'Thalos', '#6 s;ne;#2 s;se;#2 e;s;#2 sw; s;#4 sw;#4 s;#5 se;#2 s;d;s;se;s;#3 se;#4 e;#6 s;sw;#5 w;n;e', None, None)]),
    ('Adendra', [
        (D, 'Astral Plane', '#8 u;n;unlock n;n -> Exploring -> Roaming -> Wandering -> Lost -> Travelling -> Traversing -> Deep Within -> up to "The Mist Alliance"', None, None),
        (N, 'Old Marsh', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#4 sw;#4 s;#5 se;#2 s;d;s;se;s;#3 sw;u;#3 w;s;sw;d;#3 w;#3 n;w;#2 s;#2 sw;#2 w;sw;#2 nw;sw;w;sw;#2 s;sw;tree;#2 e;#3 se;#4 s;e;s', None, None)]),
    ('Shivvan', [
        (D, "Shai'Ghool", '#8 e;#3 ne;#3 e;ne;e;ne;#2 e;#2 n;e;ne; (n; Navigate Maze - DANGER) ; e;ne;w', None, None),
        (N, 'Abattoir Asylum', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#2 e;u;#3 e;#2 s;se;#6 e;#3 se;#3 s;sw;#2 s; scry for "Afloat on the ocean";e;steal key/kill glasswalker;unlock n;open n;n;#4 w;se', None, None)]),
    ('Ghordohl', [
        (D, 'Blasted Lands', '#8 e;se;se;s;#4 se;s;s;sw;w;sw;s;s;#3 se;sw;w;w;sw;s;s;e; scan for "Entrance to the Blasted Lands" & go there, track feris until “The Oasis”, n;ne;e;u', ('sub', 'Blasted Lands'), None),
        (N, 'Revelation City', '#6 n;#6 e;se;e;#2 ne;e;nw;#2 n;#2 ne;w;#2 nw;#3 n;ne;n;nw;#3 n;#2 ne;n;nw;w;#2 nw;w;#3 nw;#3 w;#2 nw;#3 w;#5 nw;w;#2 n;open n;n;w;#2 n;e;open s;s', None, None)]),
    ('Keltas', [
        (D, 'Moria', '#8 e;#2 se;s;#2 se;#2 w;s;#3 w;nw;u;#2 w;sw;#2 w;u;n;d;w;#2 sw;d;n;sw', None, None),
        (N, 'Cursed Lands', 'nw;w;w;#4 n;e;look painting;open n;n;#26 w;n;n;ne;nw;n;nw;w;w;#5 n;d;nw;nw;ne;e;nw;n;e;n;open n;#2 n;#2 w;nw', None, None)]),
    ('Kalerd', [
        (D, 'Great Eastern Desert', '#8 e;se;se;s;#4 se;s;s;sw;w;sw;s;s;#3 se;sw;w;w;sw;s;s;e; scan for "The wind-swept ledge" ; open crevice; s;sw;w;#3 n;e;s', None, None),
        (N, 'The Azure Sea', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#2 e;u;#3 e;#3 s;u', ('room', 6288), None),
        (N, 'Kontaur', '#26 w;#9 s;d;s;e;open trapdoor;d;#2 w;#2 s;e;s;#2 e;s;e;s;w', None, None)]),
    ('Tirebaen', [
        (D, 'Otherland', None, None, None),   # its old directions, line and marker (owner, Oct 26)
        (N, 'Ockwater Fens', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#3 sw;s;#2 sw;s;se;#2 sw;s;#2 sw;s;sw;#2 s;w;sw;s;sw;s;sw;#5 w;sw;s;sw;#2 w;sw;w;nw;#2 ne;n;ne;nw;#5 n;#2 u;n;u;rowboat;pull chain;pull oar;push oar; (repeat until you reach short) ; north;e;n;n;ne', None, None),
        (N, 'Otherland', 'nw;#2 w;#4 n;e;look painting;n;nw;#2 n;nw;w;#2 nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;ne;#3 w;ne;nw;n;nw;w;nw;#4 n;d;nw;se;#2 nw;w;u;ne;#2 u;sw;#2 n (DANGER - Ledge of Life rooms may force kill you)', None, None)]),   # ends on Mouth of the Blizzard
    ('Cawyn', [
        (D, 'Olympus', '#8 u;n;unlock north;open north;track juna;say Will you take me to Olympus?;#7 n;u;open u;u;open u;#3 u', None, None),
        (N, "Lake Tich'Pyga", '#7 w;nw;n;#3 nw;n;#2 nw;ne;n;e;#2 n;#2 ne;n;#2 ne;s', ('xy', (-25.5, -23.5)), None)]),   # the rough centre of the lake (owner, Oct 26 later: centre of its water rooms)
    ('Sil-Galith', [
        (D, 'Moria', '#8 e;#2 se;s;#2 se;#2 w;s;#3 w;nw;u;ne;u;ne;se;sw;se;u;nw;u;enter;nw;n', None, None),
        (N, 'Mithril Hall', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;u;ne;nw;#2 w;sw;#3 s;#2 se;sw;#2 u;w;nw;#4 w;#2 n;e;#2 n;w;d;#2 e;open mountain;#4 n;e;#3 n;#2 e;n;#2 w;d;e;#2 s;#2 e;d;e', None, None)]),
    ('Masefi', [
        (D, 'Blood Sea (Hurricane Island)', '#53 w;se;d;u;d;u;#3 u;ne', ('copy', 'Hurricane Island'), None),   # Hurricane Island's own line and marker (owner, Oct 26 later)
        (N, 'Treetops & Canopy', '#9 w;sw;#4 w;s;sw;#13 w;u;#5 w;n;#2 w;#6 n;e;#2 n;w;u;e;s;e;#8 s;#3 e;u', ('sub', 'Treetops and Canopy'), None)]),
    ('Tempus', [
        ('likeness', 'Northern Plains', 'nw;#2 w;#4 n;e;look painting;op n;n;#28 w;#2 s;#4 e;ne;n', None, None),
        (N, "The Village of Tar'pa Cithm (Barb only)", 'From Barb Recall: w;#2 n;nw;w;n;nw;#4 n', ('place', "Village of Tar'pa Cithm"), None)]),
    ("Sh'Vath", [   # (owner, Oct 27)
        (D, 'The Warehouse', '#4 w;n;n;open sw;sw;open s;s;open s;#2 s;#5 w;#4 s;#2 u;e;enter;nw;n;u;se', None, None),
        (N, 'Tullfuhrzky Manor', 'nw;w;w;#4 n;w;look painting;open n;n;open n;#3 n;open n;#2 n;e;#2 n;e;ne', None, None)]),
    ("Z'hyal", [   # times of day in the title; the always-open one first (owner, Oct 27)
        (D, 'Barren Peaks', '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;#2 sw;#2 s;#2 ne;n;nw;w;#2 nw;w;#3 nw;#3 w;#2 nw;#3 w;#6 nw;n;#2 nw;#2 n;ne;w;n;ne;s;ne;ne;u**;sw;e', None, None),
        (D, 'Northern Plains (6am - 7pm)', 'nw;#2 w;#4 n;e;look painting;open n;n;nw;#2 n;nw;w;#2 nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#8 w;s;u;sw;e', None, None),
        (D, 'Valley of the Elves (6am - 7pm)', 'nw;#2 w;#4 n;e;look painting;open n;n;nw;#2 n;nw;w;#2 nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;#2 sw;#3 w;#2 nw;#2 sw;#3 w;#2 sw;#2 nw;#2 w;#2 sw;nw;w;n;#2 e;n;e;#2 ne;nw;d;#2 nw;#5 n;e;#2 n;u**;sw;e', None, None),
        (D, 'Treetop & Canopy (6am - 7pm)', '#9 w;#2 nw;#18 w;u;#4 n;#3 u;nw;sw;e', None, None),
        (D, 'Shattered Refuge (6am - 7pm)', '#11 s;w;s;w;#2 s;u;n;give 500 coin troll;s;ne;u**;sw;e', None, None),
        (D, 'The Mire (6am - 7pm)', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#5 sw;nw;n;ne;nw;#2 n;ne;n;e;#2 se;e;s;se;sw;#2 s;sw;#2 s;sw;s;se;#3 e;u**;sw;e', None, None),
        (N, 'Dunhill (6am - 7pm)', 'nw;#2 w;#4 n;e;look painting;open n;n;nw;#2 n;nw;w;#2 nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;ne;#16 w;n;w;n;sw;#4 w;#2 s;#2 w;s;#4 w;ne;n;ne;#2 se;e;n', None, None),
        (N, 'Dragon Tower (6am - 7pm)', '', ('place', 'Dragon Tower'), "Play the entire Dragon Tower area up to outside Tiamat's room. Go east.")]),
    ("Gre'Vos", [
        (D, 'Ashen Forest', '#8 e;#3 ne;#3 e;ne;e;ne;#2 e;#4 n;u;n;u', None, None),
        (D, 'Shadow Grove (8pm - 4am)', '#8 n;nw;w;ne;leave;#2 n', None, None),
        (D, 'The Graveyard (8pm - 1pm)', '#9 w;sw;#4 w;s;sw;#2 w;#2 s;sw;s;#3 w;leave;#2 n', None, None),
        (D, 'Mountains of Desolation (8pm - 4am)', '#8 e;#2 se;s;#3 se;e;ne;e;leave;#2 n', None, None),
        (D, 'SMR (8pm - 4am)', '#13 s;#2 e;#2 u;w;s;leave;#2 n', None, None),
        (D, 'Revelation City (8pm - 4am)', '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;#2 sw;#2 s;#2 ne;n;nw;w;#2 nw;w;#3 nw;#3 w;#2 nw;#3 w;#5 nw;w;#3 n;w;#2 n;w;w (see notes)', None, None),
        (N, "Wyvern's Tower (8pm - 4am)", '#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;sw;#3 w;ne;e;ne;n;nw;#3 n', None, None),
        (N, 'Dragon Tower (8pm - 4am)', '', ('place', 'Dragon Tower'), "Play the entire Dragon Tower area up to outside Tiamat's room. Go west.")]),
]
PRIESTS = {"A'enari": 'The Divini Priest', "Vl'aresch": 'The Moze Priest', "Bron'Trel": 'The Brotherhood (Brother Lopyn)', 'LaChte': 'The Harum-Scarum',
           "Z'hyal": 'The Listra', "Gre'Vos": 'The Moondog', "Mak'kor": 'The Diabolist', 'Bael': "Death's Black Cloak", 'Sarane': 'The Matrons',
           'Wirawyth': 'The Dragoons', 'Estathius': 'The Brume', 'Kardis': 'The Revisionist (Priest of Sorrow)', 'Adendra': "The Sul'Gali Priest",
           'Shivvan': 'The Enlightened Ones', 'Ghordohl': 'The Aristocrats', 'Keltas': 'The Brigands', 'Kalerd': 'The Priest of Summer',
           'Tirebaen': 'The Priest of Winter', 'Cawyn': 'The Storm Bringers', 'Sil-Galith': 'The Stone Golem', 'Masefi': 'Tumbling Whirlwinds',
           "Sh'Vath": "The Cu'rina (A small child)"}   # the card's 'Priests:' line (owner, Oct 27; Tempus and Grishnakh have none)


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    _, at = maplib.tracer(pos, wild)
    isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    def walk(route):                                                 # maplib.tracer's walk, + spacers followed by their one other exit
        v = 764; trail = [v]
        for tok in [x.strip() for x in re.sub(r'\([^)]*\)', ';', route).split(';') if x.strip()]:
            tok = re.sub(r'^l ', 'look ', tok).replace('*', '')   # ('u**': a way open only at times; traced as u)
            m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2).strip()) if m else (1, tok)
            for _ in range(n):
                nx = [e for e in exits.get(v, []) if e['name'] == dd or e['cmd'].split(';')[-1] == dd or e['cmd'] == tok]
                if not nx and dd not in maplib.DIRS: break
                if not nx: return trail
                prev, v = v, nx[0]['to']; trail.append(v); k = 0
                while isspacer(v) and k < 40:
                    c = [x['to'] for x in exits.get(v, []) if x['name'] == dd] or [x['to'] for x in exits.get(v, []) if x['to'] != prev]
                    if len(c) != 1: break
                    prev, v = v, c[0]; trail.append(v); k += 1
        return trail
    jumps = [((j[0], j[1]), (j[2], j[3])) for j in wild.get('jumps') or []]
    isjump = lambda a, b: any((math.dist(a, x) < .03 and math.dist(b, y) < .03) or (math.dist(b, x) < .03 and math.dist(a, y) < .03) for x, y in jumps)
    def segs_of(pts):                                                # one piece per unbroken stretch (sea crossings over 100 break it)
        out = [[pts[0]]]
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) > 100 and not isjump(a, b): out.append([b])
            else: out[-1].append(b)
        return out
    gfx = {g.get('k'): g for g in wild['gfx'] if isinstance(g, dict)}
    P = {p['name']: p for p in wild['places']}
    mark_of = lambda p: R(p['at'] if p.get('at') else p['path'][-1])
    rep = {}
    for name, locs in DEITIES:
        opts = []
        for who, sub, raw, spot, text in locs:
            title = ('Naos' if who == N else 'Tempus (Likeness)' if who == 'likeness' else name) + ' · ' + sub
            if raw is None:                                          # Tirebaen: its old route, line and marker
                old = P[name]
                opts.append(dict(dir=title, who=D, sub=sub, route=old['route'], segs=old['segs'], at=mark_of(old)))
                rep[title] = {'old route kept, marker': mark_of(old)}; continue
            route = maplib.condense(raw) if raw else ''
            if spot and spot[0] == 'place':                          # no line: the marker on that place's marker
                m = mark_of(P[spot[1]])
                opts.append(dict(dir=title, who=who, sub=sub, route=route, segs=[], at=m, text=text, noline=True))
                rep[title] = {'no line, marker on': (spot[1], m)}; continue
            if spot and spot[0] == 'copy':                           # another place's line and marker
                q = P[spot[1]]; m = mark_of(q); sg = [[list(c) for c in seg] for seg in q['segs']]
                if sg[-1][-1] != m: sg[-1].append(m)
                opts.append(dict(dir=title, who=who, sub=sub, route=route, segs=sg, at=m))
                rep[title] = {'line and marker of': (spot[1], m)}; continue
            t = walk(route)
            idx = [i for i, v in enumerate(t) if at(v)]
            if spot and spot[0] == 'room': last = max(i for i in idx if t[i] == spot[1])
            elif spot and spot[0] == 'sub':
                m = mark_of(P[spot[1]]); last = min(idx, key=lambda i: math.dist(at(t[i]), m))
            elif spot and spot[0] == 'xy':
                m = R(spot[1]); last = min(idx, key=lambda i: math.dist(at(t[i]), m))
            elif spot and spot[0] == 'jump':                         # the line up to the jump (its first steps), then a jump to that place's marker
                m = mark_of(P[spot[1]]); last = len(walk(maplib.condense(spot[2]))) - 1
            else: last = max(idx)
            pts = []
            for v in t[:last + 1]:
                if at(v) and (not pts or pts[-1] != R(at(v))): pts.append(R(at(v)))
            if spot and spot[0] in ('sub', 'xy') and pts[-1] != m: pts.append(m)
            if spot and spot[0] == 'jump':
                wild['jumps'].append([pts[-1][0], pts[-1][1], m[0], m[1], f'{name}: {sub}']); jumps.append((tuple(pts[-1]), tuple(m))); pts.append(m)
            if spot and spot[0] == 'graves':                         # Mak'kor (owner, Oct 26): over the painting's jump to the Unholy Grounds marker,
                m = mark_of(P[spot[1]]); g = gfx['graves']           # then a short stretch south toward the graveyard drawing (route line only)
                if pts[-1] != m: pts.append(m)
                pts.append(R((g['x'], g['y'] - 1.0)))
            opts.append(dict(dir=title, who=D if who == 'likeness' else who, sub=sub, route=route, segs=segs_of(pts), at=pts[-1]))
            rep[title] = {'walked': len(t) - 1, 'ends at': rooms[t[-1]]['name'], 'line stops at': (t[last], rooms[t[last]]['name']),
                          'marker': pts[-1], 'pieces': len(opts[-1]['segs']), 'points': len(pts)}
        p = P.get(name) or P.get({"Vl'aresch": "V'laresch"}.get(name, ''))
        if p is None:
            p = dict(name=name, dir='here', group='af'); wild['places'].append(p)
        o0 = next(o for o in opts if o['segs'])
        p.update(name=name, route=o0['route'], segs=o0['segs'], path=o0['segs'][-1], opts=opts, deity=True, nopin=True, note=None, kind='mob')
        if name in PRIESTS: p['priests'] = PRIESTS[name]
        for k in ('at', 'more', 'optsegs', 'card', 'where'): p.pop(k, None)
        p.setdefault('room', name)
    return rep
