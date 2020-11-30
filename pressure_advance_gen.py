#!/usr/local/bin/python

# temps
first_layer_e0_temp = 250
e0_temp = 240
first_layer_bed_temp = 75
bed_temp = 75

# extrusion parameters (mm)
extrusion_width        = 0.4
layer_height           = 0.2
filament_diameter      = 1.75
first_layer_multiplier = 2.0

# print speeds (mm/s)
travel_speed      = 200
first_layer_speed =  15
slow_speed        =   5
fast_speed        = 100

# calibration object dimensions (mm)
layers        =  50
object_width  = 100
num_patterns  =   4
pattern_width =   5

# pressure advance gradient (s)
pressure_advance_min = 0.2
pressure_advance_max = 0.4

# center of print bed (mm)
offset_x = 150
offset_y = 150

layer0_z = layer_height


from math import *


def extrusion_volume_to_length(volume):
    return volume / (filament_diameter * filament_diameter * 3.14159 * 0.25)

def extrusion_for_length(length):
    return extrusion_volume_to_length(length * extrusion_width * layer_height)

curr_x = offset_x
curr_y = offset_y
curr_z = layer0_z
curr_e = 0

# start gcode
print(f"""
G28 X Y U Z
M140 S{first_layer_bed_temp}    ; set bed temp
M190 S{first_layer_bed_temp}    ; wait for bed temp
M104 S{first_layer_e0_temp}     ; set extruder temp
M109 S{first_layer_e0_temp}     ; wait for extruder temp

; Prime nozzle
G90
G1 X10 Y10 Z5 F2000
G92 E0                      ; set e0 position to 0
G1 Z0.35 F1000              ; move to edge of print volume
G91                         ; use relative positioning
G1 Y50 E12 F1000            ; start priming line
G90                         ; use absolute positioning
G92 E0
""")

# goto z height
print("G1 X%.3f Y%.3f Z%.3f F%.0f" % (curr_x, curr_y, curr_z, travel_speed * 60))

def up():
    global curr_z, curr_e
    curr_z += layer_height
    print("G1 Z%.3f" % curr_z)
    print("G92 E0")
    curr_e = 0

def line(x,y,speed,extrusion_multiplier=1.0):
    length = sqrt(x**2 + y**2)
    global curr_x, curr_y, curr_e
    curr_x += x
    curr_y += y
    if speed > 0:
        curr_e += extrusion_for_length(length) * extrusion_multiplier
        print("G1 X%.3f Y%.3f E%.4f F%.0f" % (curr_x, curr_y, curr_e, speed * 60))
    else:
        print("G1 X%.3f Y%.3f F%.0f" % (curr_x, curr_y, travel_speed * 60))

def goto(x,y):
    global curr_x, curr_y
    curr_x = x + offset_x
    curr_y = y + offset_y
    print("G1 X%.3f Y%.3f" %(curr_x, curr_y))

line(-object_width/2,0,0)

for l in range(2):
    for offset_i in range(5):
        offset = offset_i * extrusion_width
        line(object_width+offset,0,first_layer_speed,first_layer_multiplier)
        line(0,extrusion_width+offset*2,first_layer_speed,first_layer_multiplier)
        line(-object_width-offset*2,0,first_layer_speed,first_layer_multiplier)
        line(0,-extrusion_width-offset*2,first_layer_speed,first_layer_multiplier)
        line(offset,0,first_layer_speed,first_layer_multiplier)
        line(0,-extrusion_width,0,first_layer_multiplier)
    first_layer_multiplier = 1.0
    up()
    goto(-object_width/2,0)
print(f"""
M140 S{bed_temp} ; set bed temp
M104 S{e0_temp} ; set extruder temp
""")

segment = (object_width*1.0) / num_patterns
space = segment - pattern_width

for l in range(layers):
    
    pressure_advance = (l / (layers * 1.0)) * (pressure_advance_max-pressure_advance_min) + pressure_advance_min;
    
    print("; layer %d, pressure advance: %.3f" %(l, pressure_advance))
    
    print("M572 D0 S%.3f" % pressure_advance)
    
    for i in range(num_patterns):
        line(space/2, 0, fast_speed)
        line(pattern_width, 0, slow_speed)
        line(space/2, 0, fast_speed)
    
    line(0,extrusion_width,fast_speed)

    for i in range(num_patterns):
        line(-space/2, 0, fast_speed)
        line(-pattern_width, 0, slow_speed)
        line(-space/2, 0, fast_speed)
    
    line(0,-extrusion_width,fast_speed)
    up()
    
print("""
M140 S0
M104 S0
T-1
G91
G1 Z5 F3000
G90
G1 X0 Y0 F3000
G1 Z200 F1000
""")

