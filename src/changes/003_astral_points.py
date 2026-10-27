"""Owner, Oct 27: an 'Astral Points:' line on area cards (the points a portal can be opened to), in the owner's words. Areas marked
LOCAL can't be reached by astral from other regions, nor left by it: their card adds 'No astral travel to or from other regions.'
(owner's wording choice). Dylan's Area's points go on Redferne's Residence (its card line names it). New place Shadow Grove (#8 n):
a marker, no name (the big Shadow Grove area name is beside it)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
ASTRAL = {   # map place name: the owner's list
    'Dragon Cult': "Kylara, Belesdan, G'narish, Wyrmling",
    'Galaxy': 'Aries, Andromeda, Libra, Nebula',
    'Warehouse': 'Elven baby, Paulie, Prestl',
    'Southern Mountain Range': 'Grinwold',
    'Elemental Canyon': 'Fire/Earth/Water/Air/Lightning ruler, Eddie, Pebble',
    'Emerald Hills': "Johral, Qu'uilmarh",
    "Miden'nir": 'Jacob, Goblin spy, Doom goblin',
    'Mithril Hall': 'Mithril cleric, Battlerager, Mithril sentry',
    'Transylvania': 'Initiate vampire',
    'Desert of Despair': 'Nomadic man',
    'Blasted Lands': 'Fabric',
    'Dwarven Catacombs': 'Darkenbeast, Templar page, Mist',
    'Great Eastern Desert': 'Myconoid',
    'The Dungeon': 'Stinky guard',
    "Thul Ab'hara": "Fealla, M'aneer, Haszid, Sabata",
    'The Mire': 'Mosquito',
    "Dragon's Pass": 'Fingers, Lasselaure',
    'High Tower of Sorcery': 'Ezmerelda, Black apprentice',
    'Machine Dreams': 'Raven',
    'Old Marsh': 'Slaad, Green troll, Shambling mound',
    "Redferne's Residence": 'Naris guard, Neophyte lich, Harpy, Air elemental, VanHalen, Whiner',   # + Dylan's Area (owner)
    'Wastelands': 'Alsandra',
    'Thalos': 'Beholder, Horned lizard',
    'City of Aurora': 'Aurora guard, Aurora mayor, Juel, Agrivarian',
    'Forest of Tears': 'Black hawk, Wandering pine',
    'Bartok Grove': 'Appleby, Tourist, Harvester',
    "Lake of Tich'Pyga": 'Paddy, Osprey',
    'Kontaur': 'Panda, Otter',
    'Old Thalos': 'Baby beholder, Gordon, George',
    'Shattered Refuge': 'Hobgoblin miner, Traitor, Chief gnome',
    'The Graveyard': 'Graverobber, Gravedigger',
    'The Shire': 'Thain, Shiriff',
    'Tree of Life': 'Large butterfly, 2.hornet',
    'Treetops and Canopy': 'Spider monkey, Tree frog, Raccoon',
    'Ashen Forest': 'Shadow demon (aggro), Skeleton warrior (aggro)',
    'Land of the Fire Newts': 'Newt matriarch, Newt hatchling, Newt cleric',
    'Moria': 'Centipede, Guardian snake (aggro), Blue bat (aggro), Green bat (aggro), Red bat (aggro), Sly thief',
    'Mountains of Desolation': 'Leala, Revenant (aggro)',
    "King's Castle": 'Theoderic',
    'Forgotten Woods': 'Rock crab, Silver maple',
    'Green Forest': 'Weasel, Brown stag',
    'New Ofcol': 'Jacklyn, Diana, Jim, Luxan, Innkeeper',   # + Ofcol's (the same place, owner)
    'Pixie Forest': 'Air sprite, Water pixie',
    'Raven Tor': 'Magistrate, Highland piper, Scoundrel',
    'Shadow Grove': "Aruncus, Shudde-M'ell(aggro)",
    'The Keep of Mahn-Tor (The Keep)': 'Amyrok, Sumaron, Belrak',
    'The Keep of Mahn-Tor (Ogre Village)': 'Weeping willow',
    'The Tower of Zenothir': 'Juneo, Pavle',
    'Tullfuhrzky Manor': 'Collie, Cockroach, Grandpa',
    "Wyvern's Tower": 'Centaur, Fhaile',
    'Barren Peaks': 'Pikeman',
    "Barrik's Keep": 'Torlynn, Lebrand',
    'Drow City': 'Matron mother, Drow commoner',
    'Kingdom of Juargan': 'Grimdale, Juargan',
    'Morgul Vale': 'Easterling, Southron',
    'Revelation City': 'City thief, Giant snake, Giant serpent, Fire troll',
    'Northern Plains': 'Eltor, Inahir child, Eltor kid',
    'Crystalmir Lake': 'White stag, Pooh',
    'The Dunhill Demesnes': 'Faun, Brownie, Piper, Kyle',
    'Town of Solace': 'Matt, Mcbaker, Cookie, Solace citizen',
    'Unholy Grounds': 'Anastacia, Arabella, Preacher',
    'Valley of the Elves': 'Antelope, Valley elf, Octavius',
    # no astral travel to or from other regions:
    'Cursed Lands': 'Raider, Haenish',
    'Coral Depths': 'Jeremiah, seaweed',
    'Ocean Keep': 'Lingon, Crewman, Deckhand, Goat',
    'Knights of the Round': 'Cadbury',
    'Shadowport': 'Grak, Boatmaster',
    'Tower of Enlightenment': 'Hanged, Jackal, Anubis, Wands',
    'The Astral Plane': 'Nightmare, Githyanki, Invisible stalker',
}
LOCAL = {'Cursed Lands', 'Coral Depths', 'Ocean Keep', 'Knights of the Round', 'Shadowport', 'Tower of Enlightenment', 'The Astral Plane'}


def apply(town, wild, pos):
    walk, at = maplib.tracer(pos, wild)
    path = []
    for v in walk('#8 n'):
        if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
    rooms, _ = maplib.world()
    MK = [0, -14.4]                                                  # just south of the big 'Shadow Grove' name (its baseline at x 0: -14.9; owner, Oct 27)
    wild['places'].append(dict(name='Shadow Grove', route='#8 n', room=rooms[walk('#8 n')[-1]]['name'], dir='here', path=path, segs=[path + [MK]],
                               group='af', where='in the Shadow Grove', nolabel=True, at=MK))
    P = {p['name']: p for p in wild['places'] + town['places']}
    P["Redferne's Residence"]['card'] = "Area in the Mire · reached at Damp Trail. Contains Dylan's Area"
    for name, pts in ASTRAL.items():
        P[name]['astral'] = pts
        if name in LOCAL: P[name]['astrallocal'] = True
    return {'areas': len(ASTRAL), 'local only': len(LOCAL), 'Shadow Grove marker': MK}
