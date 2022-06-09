from collections import defaultdict
from math import dist
from functools import reduce
from statistics import pvariance
from pickle import dump

def wmean(values, weights):
    n = 0
    d = 0
    for v, w in zip(values, weights):
        n += v * w
        d += w
    return n/d

def get_all_layouts(shard):
    from glob import glob
    from json import load
    
    fnames = glob('./layouts/shard_%s_*' % (shard))
    
    for fname in fnames:
        f = open(fname, 'r')
        yield fname[10:-5], load(f)
        f.close()

lake_radius_pct = 9

def chessboard_dist(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def get_compressed_route(route):
    
    compressed_route = [route[0]]
    for position in route[1:-1]:
        d = dist(compressed_route[-1], position)
        if d >= 3.5:
            compressed_route.append(position)
    compressed_route.append(route[-1])
    
    return compressed_route

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


def draw_layout(layout, water_grid):
    
    grid = []
    for x in range(101):
        a = []
        for y in range(101):
            if water_grid[x][y]:
                a.append('black')
            else:
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
    
    draw(grid, None, True)

def is_valid(layout):
    
    compressed_route = []
    for segment in layout[0]:
        compressed_route += get_compressed_route(segment)
    
    lakes = layout[1]
    
    if len(compressed_route) + len(lakes) + 8 > 79:
        return False
    
    # make sure both players have decent land on tiny
    # looking like 6-lakes might be too many for 1v1
    
    land_min = 850
    players = [layout[2][0], layout[3][0]]
    scan_r = 17
    
    if len(lakes) == 6:
        players = [layout[2][0], layout[3][0], layout[2][1], layout[3][1]]
        land_min = 550
        scan_r = 14
    
    water_grid = []
    for x in range(101):
        a = []
        for y in range(101):
            a.append(False)
        water_grid.append(a)
    
    for player in players:
        
        for water in compressed_route:
            
            r = 5
            
            if chessboard_dist(player, water) > scan_r + r:
                continue
            
            wx, wy = water
            for x in range( max(0, wx - r), min(101, wx + r + 1) ):
                for y in range( max(0, wy - r), min(101, wy + r + 1) ):
                    water_grid[x][y] = True
        
        for lake in lakes:
            
            r = lake_radius_pct + 3
            
            if chessboard_dist(player, lake) > scan_r + r:
                continue
            
            wx, wy = lake
            for x in range( max(0, wx - r), min(101, wx + r + 1) ):
                for y in range( max(0, wy - r), min(101, wy + r + 1) ):
                    water_grid[x][y] = True
        
        px, py = player
        land = 0
        for x in range( max(0, px - scan_r), min(101, px + scan_r + 1) ):
            for y in range( max(0, py - scan_r), min(101, py + scan_r + 1) ):
                if not water_grid[x][y]:
                    land += 1
        
        #print(len(lakes), player, land)
        
        if land < land_min:
            return False
    
    #draw_layout(layout, water_grid)
    
    return True

def get_geometry_score(team_a, team_b):
    
    players = team_a + team_b
    
    px = [p[0] for p in players]
    py = [p[1] for p in players]
    
    score = pvariance(px) + pvariance(py)
    
    # seems to range from 1200-2500
    # return something between 0 and 1
    return score/3000

# picks the best layout for a given route + lake_count combo
def choose_best_layout(layouts):
    
    valid_layouts = []
    for layout in layouts:
        if is_valid(layout):
            valid_layouts.append(layout)
    
    if not valid_layouts:
        return False
    
    best_layout = None
    best_score = 0
    
    for layout in valid_layouts:
        balance_score = pow(layout[4], 4)
        geometry_score = get_geometry_score(layout[2], layout[3])
        score = wmean( [balance_score, geometry_score], [3, 1] )
        
        if score > best_score:
            best_score = score
            best_layout = layout
    
    return (best_layout, best_score)

# layout input schema
# 0: list of route segments
# 1: list of lakes (center of lake)
# 2: ordered list of players on team A
# 3: ordered list of players on team B
# 4: a balance score (ranges from 0-1. 1 = best balance)

from sys import argv

chunk_size = round( 256 / int(argv[2]) )
chunk_num = int(argv[1])

start = chunk_size * chunk_num
stop = min(256, start + chunk_size)

shards = set()

for n in range(start, stop):
    shards.add( format(n, '02x') )

for shard in shards:
    
    print("getting best layouts for shard %s" % (shard))
    
    best_layout_per_lake_count_and_route = defaultdict(dict)
    
    for route_id, layouts in get_all_layouts(shard):
        for lake_count, layouts2 in layouts.items():
            lake_count = int(lake_count) # json sucks
            flat_layouts = reduce(lambda a, b: a+b, layouts2.values())
            best_layout = choose_best_layout( flat_layouts )
            if best_layout:
                best_layout_per_lake_count_and_route[lake_count][route_id] = best_layout
    
    f = open('./best_layouts/shard_%s.pickle' % (shard), 'wb')
    dump(best_layout_per_lake_count_and_route, f)
    f.close()
