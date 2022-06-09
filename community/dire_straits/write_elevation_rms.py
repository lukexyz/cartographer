from math import ceil

def e_none(pct_controlled):
    
    target = 1500
    
    size_targets = {
        'if TINY_MAP': target,
        'elseif MEDIUM_MAP': target*2,
        'elseif LARGE_MAP': target*3,
        'else': target*3.5,
    }
    
    strs = []
    
    for _ in range( round( 20 * pct_controlled ) ):
            
        strs.append("create_land { terrain_type DS_T_HILL land_percent 1 zone 1 \
other_zone_avoidance_distance 7 border_fuzziness 99 clumping_factor 99 }")
    
    strs.append("")
    strs.append("<ELEVATION_GENERATION>")
    strs.append("")
    
    for size_check, tiles_total in size_targets.items():
        
        strs.append(size_check)
        
        for t, p in [('DS_T_HILL', pct_controlled), ('DS_T_BASE', (1-pct_controlled)*0.67)]:
            
            if p == 0:
                continue
            
            tiles = round(tiles_total * 0.35 * p)
            clumps = ceil(tiles / 40)
            strs.append("\tcreate_elevation 2 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
            
            tiles = round(tiles_total * 0.45 * p)
            clumps = ceil(tiles / 70)
            strs.append("\tcreate_elevation 3 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
            
            tiles = round(tiles_total * 0.2 * p)
            clumps = ceil(tiles / 100)
            strs.append("\tcreate_elevation 4 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
    
    strs.append("endif")
    
    return strs

def e_2(pct_controlled):
    
    target = 800
    
    size_targets = {
        'if TINY_MAP': target,
        'elseif MEDIUM_MAP': target*2,
        'elseif LARGE_MAP': target*3,
        'else': target*3.5,
    }
    
    strs = []
    
    for n in range( round( 18 * pct_controlled ) ):
        
        if n % 5 in [1, 3]:
            
            # valleys at 0 (-2 relative to everything else)
            strs.append("create_land { terrain_type DS_T_VALLEY land_percent 1 zone 2 \
other_zone_avoidance_distance 10 border_fuzziness 3 clumping_factor 3 }")
            
        else:
            
            strs.append("create_land { terrain_type DS_T_HILL land_percent 1 zone 1 \
other_zone_avoidance_distance 7 border_fuzziness 99 clumping_factor 99 base_elevation 2 }")
    
    strs.append("")
    strs.append("<ELEVATION_GENERATION>")
    strs.append("")
    
    for _ in range(10):
        strs.append("create_elevation 2 { base_terrain DS_T_BASE number_of_tiles 9999 number_of_clumps 99 set_scale_by_size }")
    
    for size_check, tiles_total in size_targets.items():
        
        strs.append(size_check)
        
        for t, p in [('DS_T_HILL', pct_controlled), ('DS_T_BASE', (1-pct_controlled)*0.67)]:
            
            if p == 0:
                continue
            
            tiles = round(tiles_total * 0.35 * p)
            clumps = ceil(tiles / 40)
            strs.append("\tcreate_elevation 4 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
            
            tiles = round(tiles_total * 0.45 * p)
            clumps = ceil(tiles / 70)
            strs.append("\tcreate_elevation 5 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
            
            tiles = round(tiles_total * 0.2 * p)
            clumps = ceil(tiles / 100)
            strs.append("\tcreate_elevation 6 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
    
    strs.append("endif")
    
    return strs

def e_4(pct_controlled):
    
    target = 700
    
    size_targets = {
        'if TINY_MAP': target,
        'elseif MEDIUM_MAP': target*2,
        'elseif LARGE_MAP': target*3,
        'else': target*3.5,
    }
    
    strs = []
    
    from itertools import cycle
    valleys = cycle([1, 2, 0, 1])
    
    # valleys at 0-2 ([-4, -2] relative to everything else)
    for n in range( round( 16 * pct_controlled ) ):
        
        if n % 5 in [1, 3]:
            
            strs.append("create_land { terrain_type DS_T_VALLEY land_percent 1 zone 2 \
other_zone_avoidance_distance 13 border_fuzziness 3 clumping_factor 3 base_elevation %d }" % next(valleys))
        
        else:
            
            strs.append("create_land { terrain_type DS_T_HILL land_percent 1 zone 1 \
other_zone_avoidance_distance 7 border_fuzziness 99 clumping_factor 99 base_elevation 4 }")
    
    strs.append("")
    strs.append("<ELEVATION_GENERATION>")
    strs.append("")
    
    for _ in range(10):
        strs.append("create_elevation 4 { base_terrain DS_T_BASE number_of_tiles 9999 number_of_clumps 99 set_scale_by_size }")
    
    for size_check, tiles_total in size_targets.items():
        
        strs.append(size_check)
        
        for t, p in [('DS_T_HILL', pct_controlled), ('DS_T_BASE', (1-pct_controlled)*0.67)]:
            
            if p == 0:
                continue
            
            tiles = round(tiles_total * 0.15 * p)
            clumps = ceil(tiles / 15)
            strs.append("\tcreate_elevation 5 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
            
            tiles = round(tiles_total * 0.35 * p)
            clumps = ceil(tiles / 40)
            strs.append("\tcreate_elevation 6 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
            
            tiles = round(tiles_total * 0.5 * p)
            clumps = ceil(tiles / 70)
            strs.append("\tcreate_elevation 7 { base_terrain %s number_of_tiles %d number_of_clumps %d }" % (t, tiles, clumps))
    
    strs.append("endif")
    
    return strs

base_elevations = [
    'DS_E_NONE',
    'DS_E_2',
    'DS_E_4',
]

pct_controlled = {
    'DS_HILLS_HIGH': 0.8,
    'DS_HILLS_MED': 0.6,
    'DS_HILLS_LOW': 0.4,
    'DS_HILLS_NONE': 0,
}

def get_strs( e, pct_controlled ):
    
    if e == 'DS_E_NONE':
        return e_none(pct_controlled)
    
    if e == 'DS_E_2':
        return e_2(pct_controlled)
    
    if e == 'DS_E_4':
        return e_4(pct_controlled)

f = open("./rms_pieces/elevation.txt", 'w')

f.write("""
/*
	The default elevation generation seemed pretty unbalanced.
	This partially addresses that by generating terrains in land_generation,
		and then placing portions of the elevation there.
	It doesn't fix the problem entirely, but the technique also
		allows for the creation of valleys when the entire map is elevated.
*/
""")

f.write("""
if DS_E_MAX
	if DS_E_HIGH_4
		#define DS_E_4
	else
		#define DS_E_2
	endif
elseif DS_E_MED
	if DS_E_HIGH_4
		#define DS_E_2
	else
		#define DS_E_NONE
	endif
else
	#define DS_E_NONE
endif
""")



for e in base_elevations:
    for k, v in pct_controlled.items():
        
        block = "\n\t\t".join( get_strs(e, v) )
        
        f.write("""\
if %s
	if %s
		%s
	endif
endif
""" % (e, k, block) )

f.close()
