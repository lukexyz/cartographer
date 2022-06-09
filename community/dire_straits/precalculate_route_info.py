from random import shuffle
from math import dist, ceil, floor
from statistics import mean
from pickle import load, dump
from json import dumps
from itertools import combinations, permutations
from collections import defaultdict

dimension = 8
scale = 11

offset = int( (100 - (dimension*scale))/2 + ceil(scale/2) )

lake_radius = 9

f = open('./stencils/players.pickle', 'rb')
all_player_stencils = load(f)
f.close()

all_lake_grids = {}

for n_lakes in range(3, 7):
    f = open('./lake_grids/grids_%d_lakes.pickle' % (n_lakes), 'rb')
    inclusion_grids = load(f)
    for lake_grid, inclusion_grid in inclusion_grids.items():
        all_lake_grids[lake_grid] = inclusion_grid
    f.close()

# for debugging
def draw_compact_grids(grids):
    
    from PIL import Image, ImageDraw
    
    factor = 100
    im = Image.new('RGB', (dimension*factor, dimension*factor))
    
    draw = ImageDraw.Draw(im)
    
    colors = ['blue', 'red', 'green', 'yellow']
    
    for x in range(dimension*factor):
        for y in range(dimension*factor):
            draw.point([x, y], 'white')
    
    for color, grid in zip(colors, grids):
        
        for x in range(dimension*factor):
            for y in range(dimension*factor):
                x2 = int(x/factor)
                y2 = int(y/factor)
                if (1 << (dimension * x2 + y2)) & grid:
                    draw.point([x, y], color)
    
    im.show()


def chessboard_dist(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def count_ones(n):
    return bin(n).count('1')

def get_ones(n):
    
    r = []
    
    idx = 0
    for c in reversed(bin(n)):
        if c == '1':
            r.append( (int(idx/dimension), idx % dimension) )
        idx += 1
    
    return r

def get_ones_i(n):
    
    r = []
    
    idx = 0
    for c in reversed(bin(n)):
        if c == '1':
            r.append( idx )
        idx += 1
    
    return r

def get_info_grid_u(route):
    
    # 0 = good land. suitable for p1-8
    # 1 = good land. suitable for p5-8
    # 2 = not close enough to route for lake. too close to route for players
    # 3 = close to route. unsuitable for lake
    # 4 = suitable for lake
    grid = []
    for x in range(101):
        a = []
        for y in range(101):
            a.append(0)
        grid.append(a)
    
    shuffled_route = route[:]
    shuffle(shuffled_route)
    
    scan_r_good_land = 13
    scan_r_players = 11
    
    #scan_r_lakes = ceil(lake_radius*0.6) # haven't tested multiple sizes
    
    scan_r_lakes = floor(lake_radius/2)
    
    assert( scan_r_good_land > scan_r_players )
    assert( scan_r_players > scan_r_lakes )
    
    for x in range(0, 101):
        for y in range(0, 101):
            
            c = (x, y)
            
            close_to_route = False
            for position in shuffled_route:
                if chessboard_dist(position, c) <= scan_r_good_land:
                    close_to_route = True
                    break
            
            if not close_to_route:
                continue
            
            close_to_route = False
            for position in shuffled_route:
                if chessboard_dist(position, c) <= scan_r_players:
                    close_to_route = True
                    break
            
            if not close_to_route:
                grid[x][y] = 1
                continue
            
            
            close_to_route = False
            for position in shuffled_route:
                if chessboard_dist(position, c) <= scan_r_lakes:
                    close_to_route = True
                    break
            
            if not close_to_route:
                grid[x][y] = 2
                continue
            
            grid[x][y] = 3
            
            is_safe = True
            
            # repeat with increasingly larger radii
            # filters out some scenarios where the route rejoins the lake on smaller maps
            for r in range(scan_r_lakes, lake_radius + scan_r_lakes): # haven't tested multiple sizes
                
                state_changes = 0
                
                prev_state = (chessboard_dist(route[0], c) <= r)
                for position in route[1:] + route[:1]:
                    state = (chessboard_dist(position, c) <= r)
                    if state != prev_state:
                        state_changes += 1
                    prev_state = state
                
                if state_changes != 2:
                    is_safe = False
                    break
                
            if is_safe:
                grid[x][y] = 4
    
    return grid

# 1 = the tile contains part of the route
# for debugging
def get_route_grid(route):
    
    compact_grid = 0
    
    for x in range(dimension):
        for y in range(dimension):
            position = ( offset + scale * x, offset + scale * y )
            
            for position2 in route:
                if chessboard_dist(position, position2) <= 4:
                    compact_grid |= 1<<(dimension*x+y)
                    break
    
    return compact_grid

def get_player_options_grid(info_grid_u):
    
    compact_grid = 0
    
    for x in range(dimension):
        for y in range(dimension):
            
            rx = offset + scale * x
            ry = offset + scale * y
            
            v = info_grid_u[rx][ry]
            if (v == 0) or (v == 1):
                compact_grid |= 1<<(dimension*x+y)
    
    return compact_grid

def get_small_map_player_options_grid(info_grid_u):
    
    compact_grid = 0
    
    for x in range(dimension):
        for y in range(dimension):
            
            rx = offset + scale * x
            ry = offset + scale * y
            
            v = info_grid_u[rx][ry]
            if (v == 0):
                compact_grid |= 1<<(dimension*x+y)
    
    return compact_grid

def get_lake_options_grid(info_grid_u):
    
    compact_grid = 0
    
    for x in range(dimension):
        for y in range(dimension):
            
            rx = offset + scale * x
            ry = offset + scale * y
            
            v = info_grid_u[rx][ry]
            if (v == 4):
                compact_grid |= 1<<(dimension*x+y)
    
    return compact_grid




# check if each "corner" has a player
# this is quick, but it doesn't filter much from the biggest problems
def has_sufficient_coverage(players):
    
    nn = False
    np = False
    pn = False
    pp = False
    
    upper = ceil((dimension-1)*0.6)
    lower = floor((dimension-1)*0.4)
    
    for x, y in players:
        
        if x >= upper:
            if y >= upper:
                pp = True
            elif y <= lower:
                pn = True
        elif x <= lower:
            if y >= upper:
                np = True
            elif y <= lower:
                nn = True
    
    return (nn and np and pn and pp)

def get_average_position_f(positions):
    xs = []
    ys = []
    for x, y in positions:
        xs.append( x )
        ys.append( y )
    return ( mean(xs), mean(ys) )


# first player is always on team a
# this avoids double-counting
combos = []
for ids_b in combinations( range(1, 8), 4 ):
    ids_a = [i for i in range(8) if i not in ids_b]
    combos.append( (ids_a, ids_b) )



def is_near_team(player, allies, enemies):
    
    ally_ds = ( dist(player, ally) for ally in allies )
    enemy_ds = ( dist(player, enemy) for enemy in enemies )
    
    if min( ally_ds ) >= min( enemy_ds ):
        return False
    
    ally_middle = get_average_position_f( allies )
    enemy_middle = get_average_position_f( enemies )
    
    if dist(player, ally_middle) >= dist(player, enemy_middle):
        return False
    
    return True

middle_f = ( (dimension-1)/2, (dimension-1)/2 )

# distances provided should be [0, 100]
# allows players to be closer when they're reflected across the center compared to other spawns
def too_close(a, b, min_sep_crossing_middle, min_sep_elsewhere):
    
    m = get_average_position_f( (a, b) )
    
    if dist( m, middle_f ) <= 7.5/scale:
        
        return dist(a, b) < min_sep_crossing_middle/scale
    
    else:
        
        return dist(a, b) < min_sep_elsewhere/scale
    

def get_small_map_orderings(players_a, players_b):
    
    options = []
    
    for ordered_a in permutations(players_a, 2):
        
        if too_close(ordered_a[0], ordered_a[1], 27, 33):
            continue
        
        for ordered_b in permutations(players_b, 2):
            
            if too_close(ordered_b[0], ordered_b[1], 27, 33):
                continue
            
            if too_close(ordered_a[0], ordered_b[0], 37, 50):
                continue
            
            valid = True
            
            for a in ordered_a:
                for b in ordered_b:
                    if too_close(a, b, 33, 40):
                        valid = False
            
            if valid:
                options.append( (list(ordered_a), list(ordered_b)) )
    
    return options
        

# for each valid combination,
#     this randomly picks a valid permutation for the smaller maps restriction
#     there are up to (24x24=576) possible permutations per combination
def get_team_options(players, small_map_players):
    
    team_options = []
    
    for ids_a, ids_b in combos:
        
        team_a = [players[pid] for pid in ids_a]
        
        if len([p for p in team_a if p in small_map_players]) < 2:
            continue
        
        team_b = [players[pid] for pid in ids_b]
        
        if len([p for p in team_b if p in small_map_players]) < 2:
            continue
        
        acceptable = True
        
        for a in team_a:
            allies = [p for p in team_a if p != a]
            enemies = team_b
            
            if not is_near_team(a, allies, enemies):
                acceptable = False
                break
        
        if not acceptable:
            continue
        
        for b in team_b:
            allies = [p for p in team_b if p != b]
            enemies = team_a
            
            if not is_near_team(b, allies, enemies):
                acceptable = False
                break
        
        if acceptable:
            
            team_a_small = [p for p in team_a if p in small_map_players]
            team_a_big = [p for p in team_a if p not in team_a_small]
            
            team_b_small = [p for p in team_b if p in small_map_players]
            team_b_big = [p for p in team_b if p not in team_b_small]
            
            options = []
            
            for option_a, option_b in get_small_map_orderings(team_a_small, team_b_small):
                
                # mostly does nothing or just chooses a random order for 2 elements
                # can be optimized if needed
                shuffle(team_a_small)
                shuffle(team_a_big)
                shuffle(team_b_small)
                shuffle(team_b_big)
                
                for p in team_a_small + team_a_big:
                    if p not in option_a:
                        option_a.append( p )
                
                for p in team_b_small + team_b_big:
                    if p not in option_b:
                        option_b.append( p )
                
                options.append( (option_a, option_b) )
            
            team_options += options
    
    return team_options

# the final selection favors layouts that are more interesting
# part of that filtering can occur here
# being too picky here will prevent the discovery of certain layouts
def has_sufficient_variance(players, extra_picky=False):
    
    grid = []
    for x in range(dimension):
        a = []
        for y in range(dimension):
            a.append(0)
        grid.append(a)
    
    for x, y in players:
        grid[x][y] = 1
    
    
    for x, y in players:
        
        if extra_picky:
            # remove 3-in-a-row straight lines (x-x-x)
            # if it's (x-x--x), it might be (a-a--b), so leave it
            
            if x < dimension - 4:
                if grid[x+2][y] and grid[x+4][y]:
                    return False
            
            if y < dimension - 4:
                if grid[x][y+2] and grid[x][y+4]:
                    return False
        
        else:
            # remove 4-in-a-row straight lines (x-x-x-x)
            
            if x < dimension - 6:
                if grid[x+2][y] and grid[x+4][y] and grid[x+6][y]:
                    return False
            
            if y < dimension - 6:
                if grid[x][y+2] and grid[x][y+4] and grid[x][y+6]:
                    return False
        
        if extra_picky:
            # remove partial boxes (and therefore also 2x2 boxes)
            # x-x
            # ---
            # x-x
            
            if (x < dimension - 2) and (y < dimension - 2):
                if grid[x+2][y] + grid[x+2][y+2] + grid[x][y+2] > 1:
                    return False
        
        else:
            # remove 2x2 boxes
            # x-x
            # ---
            # x-x
            
            if (x < dimension - 2) and (y < dimension - 2):
                if grid[x+2][y] + grid[x+2][y+2] + grid[x][y+2] == 3:
                    return False
    
    return True

def get_info_for_route(route):
    
    info_grid_u = get_info_grid_u(route)
    
    lake_options_grid = get_lake_options_grid(info_grid_u)
    
    composite_lake_inclusion_grid = 0
    
    # if the route isn't extensive, this will trim the player possibilities
    # if the route is extensive, this is all 1s, but the possibilities will be naturally limited
    for lake_grid, inclusion_grid in all_lake_grids.items():
        intersection = lake_grid & lake_options_grid
        if lake_grid == intersection:
            composite_lake_inclusion_grid |= inclusion_grid
    
    player_options_grid = get_player_options_grid(info_grid_u)
    player_options_grid &= composite_lake_inclusion_grid
    
    small_map_players = get_small_map_player_options_grid(info_grid_u)
    
    filtered_player_stencils = set()
    
    for stencil in all_player_stencils:
        stencil &= player_options_grid
        if count_ones(stencil) >= 8:
            if count_ones(stencil & small_map_players) >= 4:
                filtered_player_stencils.add(stencil)
    
    print("filter from %d player stencils to %d valid ones" % (len(all_player_stencils), len(filtered_player_stencils)))
    
    if not filtered_player_stencils:
        return []
    
    filtered_player_stencils = list(filtered_player_stencils)
    
    combos = []
    
    for stencil_num, stencil in enumerate(filtered_player_stencils):
        combos += list( combinations( get_ones_i(stencil), 8 ) )
        if len(combos) > 1000**2:
            print("over a million combos. breaking at %d%%" % (round(100*stencil_num/len(filtered_player_stencils))))
            #draw_compact_grids([get_route_grid(route), player_options_grid])
            break
    
    # the same 8-player set may appear in multiple stencils
    player_grids = set()
    
    for players in combos:
        player_grid = 0
        for player_c in players:
            player_grid |= 1<<player_c
        
        player_grids.add( player_grid )
    
    player_grids = list(player_grids)
    
    print("found %d sets of 8-player placement possibilities" % (len(player_grids)))
    
    if len(player_grids) > 33000:
        shuffle(player_grids)
        print("picking 33000 at random")
        player_grids = player_grids[:33000]
    
    valid_player_layouts = {}
    for player_grid_num, player_grid in enumerate(player_grids):
        if player_grid_num % 777 == 0:
            print("\tprogress: %d%%" % (round(100*player_grid_num/len(player_grids))))
        
        intersection = player_grid & small_map_players
        
        if count_ones(intersection) >= 4:
            
            players = get_ones(player_grid)
            
            shuffle(players)
            
            if len(player_grids) > 250:
                
                if not has_sufficient_coverage(players):
                    continue
                
                if not has_sufficient_variance(players, len(player_grids) > 1000):
                    continue
            
            team_options = get_team_options(players, get_ones(intersection))
            
            if team_options:
                shuffle(team_options)
                valid_player_layouts[player_grid] = team_options
    
    print("of these, only %d were valid (with %d possible teams)" % (
        len(valid_player_layouts.keys()),
        sum(len(o) for o in valid_player_layouts.values())
    ) )
    
    return [route, lake_options_grid, valid_player_layouts]

def get_all_routes():
    from os import listdir
    
    fnames = listdir('./routes/')
    
    for fname in fnames:
        f = open("./routes/%s" % (fname), 'rb')
        for route in load(f):
            yield route
        f.close()

# quick way to enable parallelism
def get_shard_for_route_str(route_str):
    from hashlib import sha256
    return ascii(sha256(bytes(route_str, 'ascii')).hexdigest())[1:3]

def calculate_route_info_for_shards(shards):
    
    routes_per_shard = defaultdict(list)
    
    for route in get_all_routes():
        route_str = dumps(route)
        shard = get_shard_for_route_str(route_str)
        if (shard in shards):
            routes_per_shard[shard].append(route)
    
    for shard, routes in routes_per_shard.items():
        print("found %d routes for shard %s" % (len(routes), shard) )
        
        infos = []
        
        for idx, route in enumerate(routes[:]):
            print("finding info for route %d of %d" % (idx, len(routes)) )
            info = get_info_for_route(route)
            if info:
                infos.append( info )
        
        f = open( './route_info/shard%s.pickle' % (shard), 'wb' )
        dump( infos, f )
        f.close()

from sys import argv
chunk_num = int(argv[1])
chunk_size = round( 256 / int(argv[2]) )

start = chunk_size * chunk_num
stop = min(256, start + chunk_size)

shards = set()

for n in range(start, stop):
    shards.add( format(n, '02x') )

calculate_route_info_for_shards(shards)
