from random import shuffle
from math import dist, ceil
from pickle import dump

def calculate_stencil( dimension, separation, euclidean ):
    
    stencil = []
    
    available = []
    
    grid = []
    for x in range(dimension):
        a = []
        for y in range(dimension):
            a.append(False)
            available.append( (x, y) )
        grid.append(a)
    
    shuffle(available)
    
    for x, y in available:
        
        if grid[x][y]:
            continue
        
        stencil.append( (x, y) )
        r = ceil(separation) - 1
        for x2 in range( max(0, x-r), min(dimension, x+r+1) ):
            for y2 in range( max(0, y-r), min(dimension, y+r+1) ):
                if euclidean:
                    if dist( (x, y), (x2, y2) ) < separation:
                        grid[x2][y2] = True
                else:
                    grid[x2][y2] = True
    
    return stencil

def calculate_stencils( dimension, separation, euclidean, border=0 ):
    
    stencil = calculate_stencil(dimension - (2*border), separation, euclidean)
    
    if border:
        stencil = [(x+border, y+border) for x, y in stencil]
    
    stencils = [stencil]
    
    stencils.append( [(dimension-x-1, y) for x, y in stencil] )
    
    stencils.append( [(x, dimension-y-1) for x, y in stencil] )
    
    stencils.append( [(dimension-x-1, dimension-y-1) for x, y in stencil] )
    
    return stencils

def get_stencil_as_number(dimension, stencil):
    
    n = 0
    
    for x, y in stencil:
        n |= 1<<(dimension*x+y)
    
    return n

dimension = 8
separation = 2
euclidean = False

n_stencils = 1000**2
player_stencils = []

for stencil_num in range(ceil(n_stencils/4)):
    if (4*stencil_num) % 1000 == 0:
        print("progress %d%%" % (round(400*stencil_num/n_stencils)))
    for stencil in calculate_stencils(dimension, separation, euclidean):
        player_stencils.append( get_stencil_as_number(dimension, stencil) )

for n in range(7, 20):
    s = set()
    c = 0
    for stencil in player_stencils:
        if (bin(stencil).count('1') == n):
            c += 1
            s.add( stencil )
    
    print("%d players. calculated %d stencils. unique count %d" % (n, c, len(s)))

player_stencils = list(set(player_stencils))

f = open('./stencils/players.pickle', 'wb')
dump( player_stencils, f)
f.close()



dimension = 8
separation = 3
euclidean = False
border = 0

n_stencils = 1000**2 # can be reduced. there's a hard limit to how many of these exist
lake_stencils = []

lake_counts = [0 for _ in range(20)]

for stencil_num in range(ceil(n_stencils/4)):
    if (4*stencil_num) % 1000 == 0:
        print("progress %d%%" % (round(400*stencil_num/n_stencils)))
    for stencil in calculate_stencils(dimension, separation, euclidean, border):
        lake_counts[len(stencil)] += 1
        lake_stencils.append( get_stencil_as_number(dimension, stencil) )

for n in range(3, 11):
    s = set()
    c = 0
    for stencil in lake_stencils:
        if (bin(stencil).count('1') == n):
            c += 1
            s.add( stencil )
    
    print("%d lakes. calculated %d stencils. unique count %d" % (n, c, len(s)))

lake_stencils = list(set(lake_stencils))

f = open('./stencils/lakes.pickle', 'wb')
dump(lake_stencils, f)
f.close()

