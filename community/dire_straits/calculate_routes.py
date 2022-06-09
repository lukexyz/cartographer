from random import randint
from math import dist
from statistics import mean
from pickle import dump

def is_within_rect( c, lower_left, upper_right ):
    cx, cy = c
    x1, y1 = lower_left
    x2, y2 = upper_right
    if cx >= x1 and cx <= x2:
        if cy >= y1 and cy <= y2:
            return True
    return False

# randomly decide how much to turn
# after each step, either don't turn or turn by that amount
# take 10 - 100 steps
# may retry if it gets too close to itself
def get_random_flow( position, direction ):
    from turtle import TNavigator
    
    turn_amount = randint(5,25)
    if randint(0,1) == 0:
        turn_amount *= -1
    
    pen = TNavigator()
    pen.setheading(direction)
    
    tiles_visited = []
    
    for _ in range( randint(10, 100) ):
        pen.forward(1)
        if randint(1, 100) > 85:
            pen.right(turn_amount)
        x, y = pen.position()
        x = round(x) + position[0]
        y = round(y) + position[1]
        
        tiles_visited.append( (round(x), round(y)) )
        
    tiles_visited_deduped = []
    previous = (None, None)
    for tile in tiles_visited:
        if ( tile != previous ):
            tiles_visited_deduped.append( tile )
            previous = tile
    
    return ( tiles_visited_deduped, pen.heading() )

def get_loop(route):
    if len(route) < 200:
        return False
    
    loop = None
    for idx1, a in enumerate(route[200:]):
        if loop:
            break
        for idx2, b in enumerate(route[:200]):
            if a == b:
                loop = route[idx2:200+idx1]
                break
    
    if not loop:
        return False
    
    route = loop
    
    route2 = [(x*2, y*2) for x, y in route]
    route3 = []
    prev = route2[0]
    for current in route2[1:]:
        route3.append(prev)
        route3.append( ( mean([prev[0], current[0]]), mean([prev[1], current[1]]) ) )
        prev = current
    route3.append(prev)
    
    collision = False
    for idx1, pos1 in enumerate(route3):
        for idx2, pos2 in enumerate(route3[idx1+1:]):
            if pos1 == pos2:
                collision = True
    
    if not collision:
        return route
    
    return False

def is_loop(route):
    return dist(route[0], route[-1]) < 2

def calculate_random_route(looking_for_loop=True):
    
    start = ( randint(10, 90), randint(10, 90) )
    
    route = [start]
    
    direction = randint(0, 359)
    
    flows_completed = 0
    
    flows_desired = 10 # very easy to make it shorter after the fact
    
    fail_to_find_count = 0
    
    while flows_completed < flows_desired:
        
        if fail_to_find_count > 12:
            break
        
        current_position = route[-1]
        
        found_flow = False
        
        attempts_allowed = 100
        if flows_completed > 2:
            attempts_allowed = 20
        attempts_allowed /= (fail_to_find_count+1)
        
        for _ in range(round(attempts_allowed)):
            
            flow, new_direction = get_random_flow(current_position, direction)
            
            flow_is_valid = True
            
            # invalidate flows that are too close to themselves
            # invalidate flows that are too close to edges
            for idx1, position in enumerate(flow):
                
                # invalidate flows that are too close to edges
                if not is_within_rect( position, (10, 10), (90, 90) ):
                    flow_is_valid = False
                    break
                
                for idx3, idx2 in enumerate(range(idx1-5,-1,-1)):
                    visited = flow[idx2]
                    visited_x, visited_y = visited
                    
                    if idx3 < 15:
                        # just check if the flow doesn't overlap with recent positions
                        if is_within_rect( position, (visited_x - 1, visited_y - 1), (visited_x + 1, visited_y + 1) ):
                            flow_is_valid = False
                            break
                    elif idx3 < 30:
                        # make sure there's enough space in between segments
                        if is_within_rect( position, (visited_x - 5, visited_y - 5), (visited_x + 5, visited_y + 5) ):
                            flow_is_valid = False
                            break
                    else:
                        # make sure there's enough space in between segments
                        if is_within_rect( position, (visited_x - 10, visited_y - 10), (visited_x + 10, visited_y + 10) ):
                            flow_is_valid = False
                            break
                
                if not flow_is_valid:
                    break
            
            if flow_is_valid:
                
                # invalidate flows that are too close to the existing route
                
                for idx1, position in enumerate(flow):
                    
                    for idx2, visited in enumerate(route):
                        
                        if len(route) - idx2 < 5 and idx1 < 5:
                            # it's okay if the flow starts close to where it started
                            continue
                        
                        visited_x, visited_y = visited
                        
                        if len(route) - idx2 < 15:
                            # just check if the flow doesn't overlap with recent positions
                            if is_within_rect( position, (visited_x - 1, visited_y - 1), (visited_x + 1, visited_y + 1) ):
                                flow_is_valid = False
                                break
                        elif len(route) - idx2 < 100:
                            # make sure there's enough space in between segments
                            if is_within_rect( position, (visited_x - 10, visited_y - 10), (visited_x + 10, visited_y + 10) ):
                                flow_is_valid = False
                                break
                        elif len(route) - idx2 < 200:
                            # make sure the flow has some momentum away from visited places
                            if dist( position, visited ) < 15:
                                flow_is_valid = False
                                break
                        else:
                            if not looking_for_loop:
                                # make sure the flow has some momentum away from visited places
                                if dist( position, visited ) < 20:
                                    flow_is_valid = False
                                    break
                    
                    if not flow_is_valid:
                        break
                
            
            if flow_is_valid:
                flows_completed += 1
                fail_to_find_count = 0
                route += flow
                direction = new_direction
                found_flow = True
                break
            
        if not found_flow:
            
            fail_to_find_count += 1
            
            # should be between 5 and 30
            # higher numbers allow for more sharp turns when necessary
            # lower numbers only return smooth routes
            # at 15 degrees, 12 attempts will allow a maximum turn of about 105 degrees 
            turn_amount = 10
            
            if fail_to_find_count % 2 == 0:
                direction += turn_amount * fail_to_find_count
            else:
                direction -= turn_amount * fail_to_find_count
    
    if looking_for_loop:
        route = get_loop(route)
        if not route:
            route = calculate_random_route(looking_for_loop)
    
    return route


from random import seed
from time import time

rseed = randint(0, int(time()))
seed(rseed)

print("random seed is %d" % (rseed))

routes = []
n = 1
t = 4000

while len(routes) < t:
    print("calculating route %d of %d" % (n, t))
    route = calculate_random_route( n % 10 == 0 )
    if len(route) > 100:
        routes.append(route)
        n += 1

f = open('./routes/seed_%d.pickle' % (rseed), 'wb')
dump(routes, f)
f.close()

"""
def draw(grid_101_x_101):
    from PIL import Image, ImageDraw
    
    im = Image.new('RGB', (101, 101))
    
    draw = ImageDraw.Draw(im)
    
    for x in range(101):
        for y in range(101):
            draw.point([x, y], grid_101_x_101[x][y])
    
    im = im.resize((1000, 1000))
    
    im.show()


for route in routes:
    
    grid = []
    for x in range(101):
        a = []
        for y in range(101):
            a.append('white')
        grid.append(a)
    
    for x, y in route:
        grid[x][y] = 'black'
    
    draw(grid)
"""
