from pickle import dump, load
from itertools import combinations
from math import dist

f = open('./stencils/lakes.pickle', 'rb')
all_lake_stencils = load(f)
f.close()

dimension = 8
scale = 11

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

def get_lake_inclusion_grid(lake):
    
    close = 21/scale
    far = 32/scale
    
    compact_grid = 0
    
    for x in range(dimension):
        for y in range(dimension):
            d = dist( (x, y), lake )
            if d >= close and d <= far:
                compact_grid |= 1<<(dimension*x+y)
    
    return compact_grid

def get_lake_exclusion_grid(lake):
    
    close = 21/scale
    
    compact_grid = 0
    
    for x in range(dimension):
        for y in range(dimension):
            d = dist( (x, y), lake )
            if d < close:
                compact_grid |= 1<<(dimension*x+y)
    
    return compact_grid

lake_inclusion_grids = []
for x in range(dimension):
    a = []
    for y in range(dimension):
        a.append(None)
    lake_inclusion_grids.append(a)

for x in range(1, dimension-1):
    for y in range(1, dimension-1):
        lake_inclusion_grids[x][y] = get_lake_inclusion_grid((x, y))

lake_exclusion_grids = []
for x in range(dimension):
    a = []
    for y in range(dimension):
        a.append(None)
    lake_exclusion_grids.append(a)

for x in range(1, dimension-1):
    for y in range(1, dimension-1):
        lake_exclusion_grids[x][y] = get_lake_exclusion_grid((x, y))


def get_lake_infos(n_lakes):
    
    combos = []
    
    for stencil in all_lake_stencils:
        lakes = get_ones(stencil)
        if len(lakes) >= n_lakes:
            combos += list( combinations(lakes, n_lakes) )
    
    print( "%d %d-lake combos" % (len(combos), n_lakes) )
    
    grids = {}
    
    for combo_num, lakes in enumerate(combos):
        
        lake_grid = 0
        for x, y in lakes:
            lake_grid |= 1<<(dimension*x+y)
        
        if lake_grid in grids:
            continue
        
        if combo_num % 1000 == 0:
            print("progress %d%%" % (round(100*combo_num/len(combos))))
        
        inclusion_grid = 0
        for lake in lakes:
            inclusion_grid |= get_lake_inclusion_grid(lake)
        
        exclusion_grid = 0
        for lake in lakes:
            exclusion_grid |= get_lake_exclusion_grid(lake)
        
        inclusion_grid &= ~ exclusion_grid
        
        grids[lake_grid] = inclusion_grid
    
    return grids

for n_lakes in range(3, 7):
    
    grids = get_lake_infos(n_lakes)
    
    print( "unique lakes: %d" % (len(grids.keys())) )
    
    f = open('./lake_grids/grids_%d_lakes.pickle' % (n_lakes), 'wb')
    dump(grids, f)
    f.close()
