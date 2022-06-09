from math import dist
from random import randint, shuffle, seed
from collections import defaultdict
from statistics import mean

def draw(grid, fname=None, show=False):
    from PIL import Image, ImageDraw
    
    w = len(grid)
    
    im = Image.new('RGB', (w, w))
    
    draw = ImageDraw.Draw(im)
    
    for x in range(w):
        for y in range(w):
            color = grid[x][y]
            draw.point([x, y], color)
    
    im = im.resize((1000, 1000))
    
    if show:
        im.show()
    
    if fname != None:
        im.save('./pictures/%s.png' % (fname))
        
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        
        im = im.rotate(360-90-45,expand=True)
        
        im = im.resize((1000, 1000))
        
        im.save('./pictures/minimap_%s.png' % (fname))

def draw_layout(layout, fname=None):
    
    grid = []
    for x in range(101):
        a = []
        for y in range(101):
            a.append('white')
        grid.append(a)
    
    for segment in layout[0]:
        for x, y in get_compressed_route(segment):
            grid[x][y] = '#77AAFF'
    
    for x, y in layout[1]:
        for x2 in range( max(0, x-7), min(101, x+8) ):
            for y2 in range( max(0, y-7), min(101, y+8) ):
                grid[x2][y2] = '#3377FF'
    
    colors_a = ['blue', 'green', 'cyan', 'gray']
    colors_b = ['red', 'yellow', 'fuchsia', 'orange']
    
    for c, p in zip(colors_a, layout[2]):
        x, y = p
        grid[x][y] = c
    
    for c, p in zip(colors_b, layout[3]):
        x, y = p
        grid[x][y] = c
    
    draw(grid, fname)

def append_rms_piece(f, name):
    f2 = open("./rms_pieces/%s.txt" % (name), 'r')
    f.write("\n")
    f.write("\n/* begin %s.txt */\n\n" % (name))
    f.write(f2.read())
    f.write("\n/* end %s.txt */\n\n" % (name))
    f.write("\n")
    f2.close()

lake_base_size_tiles = 10

def is_loop(split_route):
    return chessboard_dist(split_route[0][0], split_route[-1][-1]) < 4

def chessboard_dist(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def sign(n):
    if n < 0:
        return -1
    if n > 0:
        return 1
    return 0

def get_compressed_route(route):
    
    compressed_route = [route[0]]
    for position in route[1:-1]:
        d = dist(compressed_route[-1], position)
        if d >= 3.5:
            compressed_route.append(position)
    compressed_route.append(route[-1])
    
    return compressed_route

# layout schema
# 0: list of route segments
# 1: list of lakes (center of lake)
# 2: ordered list of players on team A
# 3: ordered list of players on team B
# 4: dictionary
#     balance: a balance score (ranges from 0-1. 1 = best balance)
#     score: 0-1. higher numbers are supposed to be more interesting maps
#     min_route_d: lowest chessboard distance between any player and any part of the route
#         measured in tiles by looking at all teamsizes
#     hill_space: higher numbers mean there's more space for hills (probably because of less total water)
def get_layouts(lake_count):
    from json import load
    f = open('./chosen_layouts/lake_count_%d' % (lake_count), 'r')
    layouts = load(f)
    f.close()
    
    def get_average_position_f(positions):
        xs = []
        ys = []
        for x, y in positions:
            xs.append( x )
            ys.append( y )
        return ( mean(xs), mean(ys) )
    
    def is_near_team(player, allies, enemies):
        
        closest_enemy = enemies[0]
        for enemy in enemies[1:]:
            if dist(player, enemy) < dist(player, closest_enemy):
                closest_enemy = enemy
        
        enemies = [p for p in enemies if p != closest_enemy]
        
        ally_ds = sorted( dist(player, ally) for ally in allies )
        enemy_ds = sorted( dist(player, enemy) for enemy in enemies )
        
        if min( ally_ds ) >= min( enemy_ds ):
            return False
        
        ally_middle = get_average_position_f( allies )
        enemy_middle = get_average_position_f( enemies )
        
        if dist(player, ally_middle) >= dist(player, enemy_middle):
            return False
        
        return True
    
    valid_layouts = []
    
    for layout in layouts:
        
        valid = True
        
        for teamsize in range(2,5):
            a_nearness = 0
            b_nearness = 0
            team_a = layout[2][:teamsize]
            team_b = layout[3][:teamsize]
            for player in team_a:
                allies = [p for p in team_a if player != p]
                if is_near_team(player, allies, team_b):
                    a_nearness += 1
            for player in team_b:
                allies = [p for p in team_b if player != p]
                if is_near_team(player, allies, team_a):
                    b_nearness += 1
            if a_nearness != b_nearness:
                valid = False
        
        if valid:
            valid_layouts.append(layout)
    
    return valid_layouts

editor_mode = False
stats = defaultdict(lambda: defaultdict(int))

def get_land_creation_strs(split_route, lakes, team1_positions, team2_positions, info_dict):
    
    create_land_calls = 0
    
    # shouldn't be necessary
    if randint(1,100) > 50:
        team1_positions, team2_positions = team2_positions, team1_positions
    
    #player positions define where the bottom of the TC is placed instead of the center of it
    #this should make things a little fairer
    team1_positions = [(x-1, y+1) for x, y in team1_positions]
    team2_positions = [(x-1, y+1) for x, y in team2_positions]
    
    # the hill fairness terrain generation sometimes fails and overrides terrain in the center
    # fallback to normal elevation generation when there's water near the middle 
    passes_through_mid = False
    
    strs = []
    
    stats['is_loop'][is_loop(split_route)] += 1
    
    for rsn, route_segment in enumerate( split_route ):
        
        for lake in lakes:
            safe = False
            while not safe:
                safe = True
                r = route_segment[0]
                d = chessboard_dist(lake, r)
                if d < lake_base_size_tiles and d > lake_base_size_tiles/2:
                    safe = False
                    dx = sign(lake[0]-r[0])
                    dy = sign(lake[1]-r[1])
                    p = [ r[0]+dx, r[1]+dy ]
                    route_segment = [p] + route_segment
                    #print('extended route segment', p)
                r = route_segment[-1]
                d = chessboard_dist(lake, r)
                if d < lake_base_size_tiles and d > lake_base_size_tiles/2:
                    safe = False
                    dx = sign(lake[0]-r[0])
                    dy = sign(lake[1]-r[1])
                    p = [ r[0]+dx, r[1]+dy ]
                    route_segment = route_segment + [p]
                    #print('extended route segment', p)
        
        route_land_strs = []
        for x, y in get_compressed_route(route_segment):
            # compress this string as much as possible
            route_land_strs.append( "create_land { number_of_tiles 20 land_position %d %d }" % (x, y) )
            create_land_calls += 1
            if chessboard_dist((x, y), (50, 50)) < 7:
                passes_through_mid = True
        
        if is_loop(split_route):
            strs.append( "if DS_R_S%d_%d" % (rsn, len(lakes)) )
            
            for route_land_str in route_land_strs:
                strs.append( "\t" + route_land_str )
            
            strs.append( "endif" )
        else:
            
            for route_land_str in route_land_strs:
                strs.append( route_land_str )
    
    route_len = sum( len(s) for s in split_route )
    approx = round( route_len * 0.05 )
    stats['route_length']['~ %d' % (approx*20)] += 1
    
    terrain = "DS_T_DEFAULT" if passes_through_mid else "DS_T_BASE"
    strs.append("create_land { terrain_type %s land_position 50 50 base_size 0 number_of_tiles 1 land_id 9 }" % (terrain))
    create_land_calls += 1
    
    
    for x, y in lakes:
        border_str = " "
        if y < 15:
            border_str += "top_border 3 "
        elif y  > 85:
            border_str += "bottom_border 3 "
        if x < 15:
            border_str += "left_border 3 "
        elif x > 85:
            border_str += "right_border 3 "
        strs.append("create_land { terrain_type DS_T_L number_of_tiles 111 base_size %d land_position %d %d%szone 3 other_zone_avoidance_distance 3 }" %
                        (lake_base_size_tiles, x, y, border_str) )
        create_land_calls += 1
        if chessboard_dist((x, y), (50, 50)) <= lake_base_size_tiles:
            passes_through_mid = True
    
    
    if info_dict['min_route_d'] > 21:
        high = 4
        low = 2
        strs.append("#define DS_E_HIGH_4")
        stats['elevated']['DS_E_HIGH_4'] += 1
    else:
        high = 2
        low = 0
        strs.append("#define DS_E_HIGH_2")
        stats['elevated']['DS_E_HIGH_2'] += 1
    
    for n, c in enumerate(team1_positions):
        player_id = (2*n)+1
        
        strs.append("create_land { terrain_type DS_T_BASE base_size 10 land_percent 0 land_position %d %d" % (c[0], c[1]))
        
        if editor_mode:
            strs.append("\tassign_to_player %d" % (player_id))
        else:
            if n == 0:
                strs.append("\tif 2_PLAYER_GAME")
                strs.append("\t\tassign_to AT_TEAM 0 0 0")
                strs.append("\telse")
                strs.append("\t\tassign_to AT_TEAM 1 0 0")
                strs.append("\tendif")
            else:
                strs.append("\tassign_to AT_TEAM 1 0 0")
        
        strs.append("\tif DS_E_MAX")
        
        strs.append("\t\tbase_elevation %d" % high)
        
        if low == 0:
            strs.append("\tendif")
        else:
            strs.append("\telseif DS_E_MED")
            
            strs.append("\t\tbase_elevation %d" % low)
            
            strs.append("\tendif")
        
        strs.append("}")
        
        create_land_calls += 1
    
    for n, c in enumerate(team2_positions):
        player_id = (2*n)+2

        
        strs.append("create_land { terrain_type DS_T_BASE base_size 10 land_percent 0 land_position %d %d" % (c[0], c[1]))
        
        if editor_mode:
            strs.append("\tassign_to_player %d" % (player_id))
        else:
            if n == 0:
                strs.append("\tif 2_PLAYER_GAME")
                strs.append("\t\tassign_to AT_TEAM 0 0 0")
                strs.append("\telse")
                strs.append("\t\tassign_to AT_TEAM 2 0 0")
                strs.append("\tendif")
            else:
                strs.append("\tassign_to AT_TEAM 2 0 0")
        
        strs.append("\tif DS_E_MAX")
        
        strs.append("\t\tbase_elevation %d" % high)
        
        if low == 0:
            strs.append("\tendif")
        else:
            strs.append("\telseif DS_E_MED")
            
            strs.append("\t\tbase_elevation %d" % low)
            
            strs.append("\tendif")
        
        strs.append("}")
        
        create_land_calls += 1
    
    if passes_through_mid:
        strs.append("#define DS_HILLS_NONE")
        stats['hill_space']['DS_HILLS_NONE'] += 1
    elif info_dict['hill_space'] > 1000:
        strs.append("#define DS_HILLS_HIGH")
        stats['hill_space']['DS_HILLS_HIGH'] += 1
    elif info_dict['hill_space'] > 650:
        strs.append("#define DS_HILLS_MED")
        stats['hill_space']['DS_HILLS_MED'] += 1
    else:
        strs.append("#define DS_HILLS_LOW")
        stats['hill_space']['DS_HILLS_LOW'] += 1
    
    """
    ended up not being too useful with the parameters chosen
    3 & 4 lakes almost always = false. 5 & 6 lakes almost always = true
    
    water_pct = round(100 * info_dict['water_amount'] / (101**2))
    
    stats['water_pct']['%d' % (water_pct)] += 1
    

    if water_pct > 18:
        strs.append("#define DS_MUCH_WATER")
    """
    
    #print(create_land_calls)
    assert(create_land_calls < 80)
    
    return strs

# This avoids results where some maps have percent_chance 2
#     and others have percent_chance 1. Instead, it should end up
#     either being equal or a few ending up with smaller differences
#     such as 5 vs 6 or 9 vs 10.
# Doesn't have enough layering to work for huge item sizes (eg. over 10000).
def get_chunks(items):
    
    if not items:
        return []
    
    if len(items) in [20, 25, 50, 100]:
        return [items]
    
    if len(items) >= 120:
        return [items[:100]] + get_chunks(items[100:])
    
    if len(items) >= 70:
        return [items[:50]] + get_chunks(items[50:])
    
    if len(items) >= 45:
        return [items[:25]] + get_chunks(items[25:])
    
    if len(items) >= 30:
        return [items[:20]] + get_chunks(items[20:])
    
    if len(items) > 20:
        return [items[:10]] + get_chunks(items[10:])
    
    return [items]

chosen_layouts = {
    3: get_layouts(3)[:108],
    4: get_layouts(4)[:144],
    5: get_layouts(5)[:93],
    6: get_layouts(6)[:15],
}

fname = r'C:\Program Files (x86)\Steam\SteamApps\common\Phoenix\resources\_common\random-map-scripts\(current2).rms'

f = open(fname, 'w')

append_rms_piece(f, 'terrain_defs')
append_rms_piece(f, 'game_settings_defs')
append_rms_piece(f, 'lake_count_selector')
append_rms_piece(f, 'loop_segment_selector')
append_rms_piece(f, 'canyons_selector')

layout_strs = {}
for lake_count, layouts in chosen_layouts.items():
    
    print("lake count %d: using %d layouts" % (lake_count, len(layouts)))
    
    shuffle(layouts)
    
    stats = defaultdict(lambda: defaultdict(int))
    
    f.write("if DS_%d_LAKES\n" % (lake_count))
    
    chunks = get_chunks(layouts)
    
    f.write("\tstart_random\n")
    
    remaining_pct = 100
    layout_num = 0
    
    for chunk_num, chunk in enumerate(chunks):
        
        chunk = chunks[chunk_num]
        portion = len(chunk)/sum(len(c) for c in chunks[chunk_num:])
        
        chance =  round( remaining_pct * portion )
        assert(chance > 0)
        remaining_pct -= chance
        
        f.write("\t\tpercent_chance %d #define DS_CHUNK_%d_%d\n" % (chance, lake_count, chunk_num+1))
        
    f.write("\tend_random\n")
    
    for chunk_num, chunk in enumerate(chunks):
        
        f.write("\tif DS_CHUNK_%d_%d\n" % (lake_count, chunk_num+1))
        
        f.write("\t\tstart_random\n")
        
        remaining_pct = 100
        
        while chunk:
            
            chance =  round( remaining_pct / len(chunk) )
            assert(chance > 0)
            remaining_pct -= chance
            
            layout_num += 1
            layout = chunk.pop(0)
            
            layout_id = "DS_LAYOUT_%d_%d" % (lake_count, layout_num)
            draw_layout(layout, layout_id)
            split_route, lakes, team1_positions, team2_positions, info_dict = layout
            layout_strs[layout_id] = get_land_creation_strs(split_route, lakes, team1_positions, team2_positions, info_dict)
            
            f.write("\t\t\tpercent_chance %d #define %s\n" % (chance, layout_id))
        
        f.write("\t\tend_random\n")
        
        f.write("\tendif\n")
    
    
    f.write("endif\n")
    
    print("\n\nlake count: %d" % (lake_count))
    for metric, counts in stats.items():
        t = sum(counts.values())
        print("\n\t%s" % (metric))
        for val, count in sorted( counts.items(), key=lambda x: x[0] ):
            print("\t\t%s\t%d%%\t(%d)" % (val, round(100*count/t), count))
            

append_rms_piece(f, 'player_setup')

for layout_id, layout_strs in layout_strs.items():
    f.write("if %s\n" % (layout_id))
    for layout_str in layout_strs:
        f.write("\t%s\n" % (layout_str))
    f.write("endif\n")

append_rms_piece(f, 'resources_randomizer')

import write_elevation_rms  # @UnresolvedImport @UnusedImport

append_rms_piece(f, 'elevation')

append_rms_piece(f, 'terrain_generation')
append_rms_piece(f, 'terrain_generation_dec')

append_rms_piece(f, 'objects_generation_0')
append_rms_piece(f, 'objects_generation_1')
append_rms_piece(f, 'objects_generation_2')
append_rms_piece(f, 'objects_generation_3')
append_rms_piece(f, 'objects_generation_dec')

f.close()

f = open(fname, 'r')

contents = f.read()

print( "create_terrain calls: %d" % (contents.count('create_terrain')) )
print( "create_object calls: %d" % (contents.count('create_object')) )

f.close()

