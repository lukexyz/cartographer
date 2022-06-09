from collections import defaultdict
from math import dist
from statistics import pvariance
from json import dump

def wmean(values, weights):
    n = 0
    d = 0
    for v, w in zip(values, weights):
        n += v * w
        d += w
    return n/d

def get_best_layouts():
    from pickle import load
    
    best_layout_per_lake_count_and_route = defaultdict(dict)
    
    for n in range(256):
        shard = format(n, '02x')
        
        f = open('./best_layouts/shard_%s.pickle' % (shard), 'rb')
        for k, v in load(f).items():
            for k2, v2 in v.items():
                best_layout_per_lake_count_and_route[k][k2] = v2
        f.close()
    
    return best_layout_per_lake_count_and_route

def get_compressed_route(route):
    
    compressed_route = [route[0]]
    for position in route[1:-1]:
        if dist(compressed_route[-1], position) >= 3.5:
            compressed_route.append(position)
    compressed_route.append(route[-1])
    
    return compressed_route

def get_route_score(split_route):
    
    scores = []
    weights = []
    
    for segment in split_route:
        compressed_route = get_compressed_route(segment)
        if len(compressed_route) < 12:
            scores.append(0)
            weights.append(8)
        else:
            visible_route = compressed_route[2:-2]
            px = [p[0] for p in visible_route]
            py = [p[1] for p in visible_route]
            score = (max(px) - min(px)) + (max(py) - min(py))
            score /= pow( len(visible_route), 2 )
            #score = pvariance(px) + pvariance(py)
            scores.append( score )
            weights.append( min(20, len(visible_route)) )
    
    # print( sum(len(s) for s in split_route), pow( wmean(scores, weights), 0.25) )
    
    return min( 1, pow( wmean(scores, weights), 0.25) )

def too_similar(layout, chosen_layouts):
    
    def n_overlap(a_items, b_items):
        n = 0
        for a in a_items:
            if a in b_items:
                n += 1
        return n
    
    lakes = layout[1]
    team_a = layout[2]
    team_b = layout[3]
    
    if len(lakes) == 3:
        cutoff = 2
    elif len(lakes) == 6:
        cutoff = 4
    else:
        cutoff = 3
    
    for chosen_layout in chosen_layouts:
        
        if n_overlap( chosen_layout[1], lakes ) >= cutoff:
            
            if n_overlap( chosen_layout[2], team_a ) > 2 and n_overlap( chosen_layout[3], team_b ) > 2:
                return True
            
            if n_overlap( chosen_layout[2], team_b ) > 2 and n_overlap( chosen_layout[3], team_a ) > 2:
                return True
    
    return False

lake_radius_pct = 9

def chessboard_dist(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

map_dimensions = [None, 120, 168, 200, 220]

def to_tiles(d_u, teamsize):
    return d_u * map_dimensions[teamsize] / 100

def get_min_route_d(split_route, team1_positions, team2_positions):
    
    lowest = 999
    
    for teamsize in range(2, 5):
        
        for player in team1_positions[:teamsize] + team2_positions[:teamsize]:
            
            for segment in split_route:
                for position in segment:
                    d = to_tiles( chessboard_dist(player, position), teamsize ) - 4
                    if d < lowest:
                        lowest = d
    
    return lowest

def get_hill_space(split_route, lakes, players):
    
    grid = []
    
    for x in range(101):
        
        a = []
        
        for y in range(101):
            
            c = (x, y)
            
            lowest = 999
            
            for segment in split_route:
                for position in segment:
                    d = chessboard_dist(c, position) - 2
                    if d < lowest:
                        lowest = d
            
            for lake in lakes:
                d = chessboard_dist(c, lake) - lake_radius_pct
                if d < lowest:
                    lowest = d
            
            a.append(lowest)
        
        grid.append(a)
    
    def can_have_hill(x, y):
        
        r = 7
        
        for x2 in range( max(0, x-r), min(101,x+r+1) ):
            for y2 in range( max(0, y-r), min(101,y+r+1) ):
                if grid[x2][y2] < 5:
                    return False
                for player in players:
                    if chessboard_dist(player, (x2, y2)) < 5:
                        return False
        
        return True
    
    space = 0
    
    for x in range(0, 101):
        for y in range(0, 101):
            if can_have_hill(x, y):
                space += 1
    
    return space

def get_water_amount(split_route, lakes):
    
    grid = []
    for x in range(101):
        a = []
        for y in range(101):
            a.append(False)
        grid.append(a)
    
    r = 2
    for segment in split_route:
        for x, y in segment:
            for x2 in range( max(0, x-r), min(101,x+r+1) ):
                for y2 in range( max(0, y-r), min(101,y+r+1) ):
                    grid[x2][y2] = True
    
    r = lake_radius_pct - 2
    for x, y in lakes:
        for x2 in range( max(0, x-r), min(101,x+r+1) ):
            for y2 in range( max(0, y-r), min(101,y+r+1) ):
                grid[x2][y2] = True
    
    amount = 0
    
    for x in range(101):
        for y in range(101):
            if grid[x][y]:
                amount += 1
    
    return amount

def get_layout_info(layout, score):
    
    info_dict = {
        'balance': layout[4],
        'score': score,
        'min_route_d': get_min_route_d(layout[0], layout[2], layout[3]),
        'hill_space': get_hill_space(layout[0], layout[1], layout[2] + layout[3]),
        'water_amount': get_water_amount(layout[0], layout[1]),
    }
    
    return (
        layout[0],
        layout[1],
        layout[2],
        layout[3],
        info_dict,
    )

# layout output schema
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

best_layout_per_lake_count_and_route = get_best_layouts()

used_route_ids = set()

desired_counts = {
    6: 100,
    5: 150,
    4: 225,
    3: 150,
}

for lake_count, desired_count in desired_counts.items():
    
    best_layouts = []
    
    for route_id, layout_info in best_layout_per_lake_count_and_route[lake_count].items():
        if route_id in used_route_ids:
            continue
        
        score = wmean( [layout_info[1], get_route_score(layout_info[0][0])], [3, 1] )
        
        best_layouts.append( (route_id, layout_info[0], score) )
    
    print("choosing best %d layouts (out of %d) for lake count %d" % (desired_count, len(best_layouts), lake_count))
    
    chosen_layouts = []
    
    for route_id, layout, score in sorted(best_layouts, key=lambda x: -x[2]):
        if not too_similar(layout, chosen_layouts):
            used_route_ids.add(route_id)
            chosen_layouts.append( get_layout_info(layout, score) )
            print("chosen", route_id, score)
        else:
            print("too similar", len(chosen_layouts))
        if len(chosen_layouts) == desired_count:
            break
        
    print(lake_count, len(chosen_layouts), "\n\n\n\n")
    
    f = open('./chosen_layouts/lake_count_%d' % (lake_count), 'w')
    dump(chosen_layouts, f)
    f.close()
