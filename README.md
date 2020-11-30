# Pressure Advance Generator

**Origional Script and Author: https://forum.duet3d.com/topic/6698/pressure-advance-calibration/2**

## Changes

  - Added first layer settings (temp and extrusion multiplier)
  - Added start gcode
  - Added end gcode
  - Use absolute e every layer instead of relative
  
## How To Use

- Change settings to match filament and printer
  - Filament temps (default PETG)
  - Extrusion parameters (default 0.4mm nozzle, 1.75mm filament, 200% first layer extrusion)
  - Print speeds (default max move speed 200mm/s, max print speed 100mm/s)
  - Pressure advance range (default 0.0 - 0.3)
  - Printer bed center (default x150,y150)
  - Inspect start and end gcode (suggest copying from slicer for better compatibility)
- Run script and output gcode with
``` 
python3 pressure_advance_gen.py > pressure_advance.gcode
```
