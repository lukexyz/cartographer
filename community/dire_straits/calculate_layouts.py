from random import shuffle
from math import dist, ceil, floor
from statistics import mean
from pickle import load
from json import dump, dumps
from collections import defaultdict
from functools import reduce

dimension = 8
scale = 11

offset = int( (100 - (dimension*scale))/2 + ceil(scale/2) )

lake_radius = 9

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

def is_loop(route):
    return dist(route[0], route[-1]) < 2

def get_average_position(positions):
    xs = []
    ys = []
    for x, y in positions:
        xs.append( x )
        ys.append( y )
    return ( round(mean(xs)), round(mean(ys)) )

def get_average_position_f(positions):
    xs = []
    ys = []
    for x, y in positions:
        xs.append( x )
        ys.append( y )
    return ( mean(xs), mean(ys) )

def get_split_route(route, lakes):
    
    lake_route_intersects = []
    for lake in lakes:
        
        intersects = []
        for position in route:
            if chessboard_dist(position, lake) <= lake_radius:
                intersects.append(position)
        
        if not intersects:
            raise("lake doesn't intersect route")
        
        middlemost = intersects[0]
        center = get_average_position(intersects)
        for position in intersects:
            if (dist(position, center) + dist(position, lake)) < (dist(middlemost, center) + dist(middlemost, lake)):
                middlemost = position
        
        lake_route_intersects.append( middlemost )
    
    split_route = []
    
    split_a = []
    split_b = []
    current_segment = []
    seen_lakes = set()
    for position in route:
        if position in lake_route_intersects:
            seen_lakes.add(position)
            split_route.append(current_segment)
            current_segment = []
            continue
        if len(seen_lakes) == 0:
            split_a.append(position)
        elif len(seen_lakes) == len(lakes):
            split_b.append(position)
        else:
            current_segment.append(position)
    
    if split_b and split_a and (dist(split_b[-1], split_a[0]) < 2):
        split_route.append( split_b + split_a )
    elif is_loop(route):
        split_route = [split_a] + split_route + [split_b]
    
    return [segment for segment in split_route if segment]

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


all_lake_grids = {}

for n_lakes in range(3, 7):
    f = open('./lake_grids/grids_%d_lakes.pickle' % (n_lakes), 'rb')
    all_lake_grids[n_lakes] = load(f)
    f.close()

def get_positions_u(positions_c):
    return [(offset + scale*x, offset + scale*y) for x, y in positions_c]

def get_water_u(split_route, lakes_c):
    
    grid = []
    
    for x in range(101):
        a = []
        for y in range(101):
            a.append(0)
        grid.append(a)
    
    r = lake_radius
    for x, y in get_positions_u(lakes_c):
        for x2 in range( max(0, x-r), min(101, x+r+1) ):
            for y2 in range( max(0, y-r), min(101, y+r+1) ):
                grid[x2][y2] = 1
    
    r = 3
    for segment in split_route:
        for x, y in segment:
            for x2 in range( max(0, x-r), min(101, x+r+1) ):
                for y2 in range( max(0, y-r), min(101, y+r+1) ):
                    grid[x2][y2] = 1
    
    return grid

# 8x8
def are_teams_together(team_a, team_b):
    
    for teamsize in range(2,5):
        
        a = team_a[:teamsize]
        b = team_b[:teamsize]
        
        for p in a:
            
            is_separated = True
            
            enemy_min_d = min( dist(p, enemy) for enemy in b )
            
            for ally in a:
                if p == ally:
                    continue
                
                if dist(p, ally) < enemy_min_d:
                    is_separated = False
                    break
            
            if is_separated:
                return False
        
        for p in b:
            
            is_separated = True
            
            enemy_min_d = min( dist(p, enemy) for enemy in a )
            
            for ally in b:
                if p == ally:
                    continue
                
                if dist(p, ally) < enemy_min_d:
                    is_separated = False
                    break
            
            if is_separated:
                return False
    
    return True



map_dimensions = [None, 120, 168, 200, 220]

def to_tiles(d_u, teamsize):
    return d_u * map_dimensions[teamsize] / 100

# returns [0, 180]
def angle(a, b):
    from math import atan2, degrees
    dy = a[1]-b[1]
    dx = a[0]-b[0]
    return degrees(atan2(dy, dx))

# returns [2/3, 1)
def flanking(a, b):
    from math import sqrt
    
    c = (360 + a - b) % 180
    
    return (2/3) + sqrt(c)/40.3

# returns [0.01, 0.9]
def water_influence(lake, player, teamsize):
    d = to_tiles( scale * dist(lake, player), teamsize)
    if d < 30:
        return 0.9
    return max( 0.01, 0.9 - ((d-30)/70) )

def land_influence(land, player, teamsize):
    d = to_tiles( scale * dist(land, player), teamsize)
    if d < 15:
        return 999
    if d < 30:
        return 200 - (10*(d-15))
    if d < 60:
        return 50-(d-30)
    return max( 0.01, 20 - (d-60) )

def wmean(values, weights):
    n = 0
    d = 0
    for v, w in zip(values, weights):
        n += v * w
        d += w
    return n/d

def get_lake_imbalance( team_a, team_b, lakes ):
    
    teamsize = len(team_a)
    
    lake_dominations = []
    
    for lake in lakes:
        
        team_influences = []
        
        for team in [team_a, team_b]:
            
            if len(team) == 1:
                team_influences.append( water_influence(lake, team[0], teamsize) )
                continue
            
            # boost contribution for teams that can access the lake from different directions
            
            player_influences = []
            player_angles = []
                        
            for player in team:
                
                player_influences.append( water_influence(lake, player, teamsize) )
                player_angles.append( angle(lake, player) )
            
            flanking_multipliers = []
            
            for i1 in range(len(team)):
                weights = []
                flankings = []
                for i2 in range(len(team)):
                    if i1 != i2:
                        flankings.append( flanking(player_angles[i1], player_angles[i2]) )
                        weights.append( player_influences[i2] )
                
                flanking_multipliers.append( wmean(flankings, weights) )
            
            team_influences.append( wmean(player_influences, flanking_multipliers) )
        
        lake_dominations.append( (team_influences[0] - team_influences[1]) / (team_influences[0] + team_influences[1]) )
    
    lake_imbalance = mean(lake_dominations)
    
    return lake_imbalance

summary_ranges = []
start, stop = None, None
for i in range(dimension):
    if i == 0:
        start = 0
    else:
        start = stop+1
    
    if i == dimension-1:
        stop = 100
    else:
        stop = floor(offset + i * scale + scale/2)
    
    summary_ranges.append( range(start, stop+1) )

def get_land_summaries( water_u ):
    
    summaries = [None]
    for teamsize in range(1, 5):
        
        summary = []
        for x in range(dimension):
            a = []
            for y in range(dimension):
                
                middle = (offset + x*scale, offset + y*scale)
                
                water_ds = []
                nonwater_tiles = 0
                
                rx = summary_ranges[x]
                ry = summary_ranges[y]
                
                for x2 in rx:
                    for y2 in ry:
                        if water_u[x2][y2] == 0:
                            nonwater_tiles += 1
                        else:
                            water_ds.append( dist( (x2, y2), middle ) )
                
                if water_ds:
                    safety = min(1, 0.05 * to_tiles( mean(water_ds), teamsize ) )
                else:
                    safety = 1
                
                land_value = nonwater_tiles * safety
                        
                a.append( land_value )
            summary.append(a)
        
        summaries.append(summary)
    
    return summaries

def get_land_imbalance( team_a, team_b, land_summary ):
    
    teamsize = len(team_a)
    
    land_dominations = []
    land_weights = []
    
    for x in range(dimension):
        for y in range(dimension):
            
            land = (x, y)
            land_weights.append( land_summary[x][y] )
            
            team_influences = []
            
            for team in [team_a, team_b]:
                team_influence = 0
                for player in team:
                    team_influence += land_influence( land, player, teamsize )
                team_influences.append( team_influence )
            
            land_dominations.append( (team_influences[0] - team_influences[1]) / (team_influences[0] + team_influences[1]) )
    
    land_imbalance = wmean(land_dominations, land_weights)
    
    return land_imbalance

def get_imbalance( team_a, team_b, land_summary, lakes ):
    
    teamsize = len(team_a)
    
    lake_imbalance = get_lake_imbalance(team_a, team_b, lakes)
    
    if abs(lake_imbalance) > 0.15 + teamsize/50:
        return 999
    
    land_imbalance = get_land_imbalance(team_a, team_b, land_summary)
    
    if abs(land_imbalance) > 0.15 + teamsize/50:
        return 999
    
    weights = [1, 1]
    combined_imbalance = wmean( [lake_imbalance, land_imbalance], weights )
    
    if abs(combined_imbalance) > 0.07 + teamsize/100:
        return 999
    
    return abs(combined_imbalance)

imbalance_partial_cache = {}

def get_score( team_a, team_b, land_summaries, lakes ):
    
    swap_cache_lookup = (team_a[0][0] * dimension + team_a[0][1] > team_b[0][0] * dimension + team_b[0][1])
    
    balance_scores = []
    weights = [10, 7, 4, 3]
    
    for teamsize in range(1,5):
        
        sub_a = team_a[:teamsize]
        sub_b = team_b[:teamsize]
        land_summary = land_summaries[teamsize]
        
        if teamsize < 3:
            if swap_cache_lookup:
                cache_key = dumps( sub_b + sub_a )
            else:
                cache_key = dumps( sub_a + sub_b )
            if cache_key not in imbalance_partial_cache:
                imbalance_partial_cache[cache_key] = get_imbalance( sub_a, sub_b, land_summary, lakes )
            imbalance = imbalance_partial_cache[cache_key]
        else:
            imbalance = get_imbalance( sub_a, sub_b, land_summary, lakes )
        
        if imbalance == 999:
            return 0
        
        balance_scores.append( 1 - imbalance )
    
    return wmean(balance_scores, weights)

def get_valid_layouts(info, n_lakes):
    route, lake_options_grid, player_grids_and_teams = info
    
    inclusion_grids = all_lake_grids[n_lakes]
    
    lakes_options = []
    
    for lake_grid in inclusion_grids.keys():
        intersection = lake_grid & lake_options_grid
        if lake_grid == intersection:
            lakes_options.append(lake_grid)
    
    print("\t\tfound %d lakes options" % (len(lakes_options)))
    
    if not lakes_options:
        return []
    
    valid_lakes = {}
    n_team_options = 0
    
    for lake_grid in lakes_options:
        
        inclusion_grid = inclusion_grids[lake_grid]
        
        valid_team_options = []
        
        for player_grid, team_options in player_grids_and_teams.items():
            intersection = player_grid & inclusion_grid
            if intersection == player_grid:
                n_team_options += len(team_options)
                valid_team_options.append(team_options)
        
        if valid_team_options:
            valid_lakes[lake_grid] = valid_team_options
    
    lake_team_options = defaultdict(list)
    max_samples = 10000
    
    if n_team_options < max_samples:
        
        for lake_grid, grouped_team_options in valid_lakes.items():
            lake_team_options[lake_grid] = reduce(lambda a, b: a+b, grouped_team_options)
        
        
    else:
        
        sample_rate = max_samples / n_team_options
        
        for lake_grid, valid_team_options in valid_lakes.items():
            
            for team_options in valid_team_options:
                shuffle(team_options)
                lake_team_options[lake_grid] += team_options[:round(sample_rate*len(team_options))]
    
    print("\t\tfound %d team combos across %d lakes. %s" % (
        n_team_options,
        len(lake_team_options.keys()),
        "" if n_team_options < max_samples else "sampled down to %d" % (sum(len(v) for v in lake_team_options.values()))
    ))
    
    if not lake_team_options:
        return []
    
    valid_layouts = defaultdict(list)
    
    for lake_grid, team_options in lake_team_options.items():
        
        imbalance_partial_cache.clear()
        
        lakes_c = get_ones(lake_grid)
        lakes_u = get_positions_u(lakes_c)
        
        # dangling portions of the route get truncated, so each lakeset might have a different one
        split_route = get_split_route( route, lakes_u )
        
        land_summaries = get_land_summaries( get_water_u(split_route, lakes_c) )
        
        for team_a_c, team_b_c in team_options:
            
            score = get_score(team_a_c, team_b_c, land_summaries, lakes_c )
            
            if score > 0:
                valid_layouts[lake_grid].append( (
                    split_route,
                    lakes_u,
                    get_positions_u(team_a_c),
                    get_positions_u(team_b_c),
                    score
                ) )
    
    for lake_grid, layouts in valid_layouts.items():
        valid_layouts[lake_grid] = sorted(layouts, key=lambda x: -x[4])[:25]
    
    return valid_layouts

def get_layouts_for_route(info):
    
    all_layouts = {}
    for n_lakes in [3, 4, 5, 6]:
        layouts = get_valid_layouts(info, n_lakes)
        print("\tfound %d layouts with %d lakes\n" % (len(layouts), n_lakes))
        if layouts:
            all_layouts[n_lakes] = layouts
    
    return all_layouts

def calculate_layouts_for_shard(shard):
    
    f = open( './route_info/shard%s.pickle' % (shard), 'rb' )
    infos = load(f)
    f.close()
    
    print("found information for %d routes for shard %s" % (len(infos), shard) )
    
    for idx, info in enumerate(infos):
        #print("finding layout for route %d of %d" % (idx, len(infos)) )
        layouts = get_layouts_for_route(info)
        if layouts:
            f = open( './layouts/shard_%s_route_%d.json' % (shard, idx), 'w' )
            dump( layouts, f )
            f.close()

from sys import argv

chunk_num = int(argv[1])
chunk_size = round( 256 / int(argv[2]) )

start = chunk_size * chunk_num
stop = min(256, start + chunk_size)

shards = set()

for n in range(start, stop):
    shard = format(n, '02x')
    calculate_layouts_for_shard(shard)
