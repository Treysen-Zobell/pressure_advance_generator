import math
from tkinter import ttk
import tkinter as tk
import json


settings_reference = {
    'printer_settings': {
        'bed_min_x': (0, 'Bed minimum x in mm, usually 0'),
        'bed_max_x': (300, 'Bed maximum x in mm, usually width of bed'),
        'bed_min_y': (0, 'Bed minimum y in mm, usually 0'),
        'bed_max_y': (300, 'Bed maximum x in mm, usually depth of bed'),
        'bed_max_z': (300, 'Bed maximum z in mm'),
        'homing_axes': ('X Y Z U', 'Axes to home'),
        'tool_index': (-1, '-1 If not a tool changer, otherwise tool number to use'),
        'nozzle_diameter': (0.4, 'Diameter of nozzle in mm')
    },
    'filament_settings': {
        'first_layer_extruder_temp': (220, 'Extruder temperature in C for first layer'),
        'other_layer_extruder_temp': (210, 'Extruder temperature'),
        'first_layer_bed_temp': (60, 'Bed temperature in C for first layer'),
        'other_layer_bed_temp': (60, 'Bed temperature in C'),
        'filament_diameter': (1.75, 'Diameter of filament in mm')
    },
    'extrusion_settings': {
        'first_layer_extrusion_multiplier': (2.0, 'Extrusion multiplier for first layer'),
        'other_layer_extrusion_multiplier': (1.0, 'Extrusion multiplier'),
        'first_layer_height': (0.35, 'First layer height in mm'),
        'other_layer_height': (0.2, 'Layer height in mm')
    },
    'speed_settings': {
        'travel_speed': (200, 'Travel speed in mm/s'),
        'first_layer_speed': (15, 'First layer speed in mm/s'),
        'slow_speed': (15, 'Slowest print move during calibration in mm/s'),
        'fast_speed': (100, 'Fastest print move during calibration in mm/s')
    },
    'object_settings': {
        'width': (100, 'Object width in mm'),
        'height': (15, 'Object height in mm')
    },
    'pressure_advance_settings': {
        'start': (0.0, 'Pressure advance starting value'),
        'finish': (0.3, 'Pressure advance final value')
    },
    'start_gcode_default':
        'G90 ; set absolute coordinates\n'
        'M82 ; set absolute extruder moves\n'
        'M106 S0 ; turn off part cooling fan\n'
        'M140 S[filament_settings.first_layer_bed_temp] ; set bed temp\n'
        'M190 S[filament_settings.first_layer_bed_temp] ; wait for bed temp\n'
        'M104 S[filament_settings.first_layer_extruder_temp] ; set extruder temp\n'
        'M109 S[filament_settings.first_layer_extruder_temp] ; wait for extruder temp\n'
        'G28 [printer_settings.homing_axes]\n'
        'T[tool_index] ; omitted if tool_index = -1\n',
    'end_gcode_default':
        'M140 S0 ; turn off bed\n'
        'M104 S0 ; turn off extruder\n'
        'T-1 ; omitted if tool_index = -1\n'
        'G91 G1 Z5 F3000 ; move extruder up 5\n'
        'G1 X0 Y0 F3000\n'
}


# https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
class CreateToolTip(object):
    def __init__(self, widget, text='default_text'):
        self.widget = widget
        self.text = text
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.close)
        self.top_window = None

    # noinspection PyUnusedLocal
    def enter(self, event=None):
        x, y, cx, cy = self.widget.bbox('insert')
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.top_window = tk.Toplevel(self.widget)
        self.top_window.wm_overrideredirect(True)
        self.top_window.wm_geometry(f'+{x}+{y}')
        label = tk.Label(self.top_window, text=self.text, justify='left', background='white smoke', relief='solid',
                         borderwidth=1, font=('times', '10', 'normal'))
        label.pack(ipadx=1)

    # noinspection PyUnusedLocal
    def close(self, event=None):
        if self.top_window:
            self.top_window.destroy()


class Window:
    def __init__(self, width, height, title):
        # load settings
        self.settings = self.load_settings()
        self.settings_entries = {}

        # create window
        self.root = tk.Tk()
        self.root.geometry(f'{width}x{height}')
        self.root.title(title)

        self.root.rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # create settings panel
        self.settings_frame = tk.Frame(self.root, highlightthickness=1, highlightcolor='black',
                                       highlightbackground='black')
        i = 0
        for setting_group in self.settings.keys():
            if setting_group not in ('start_gcode_default', 'end_gcode_default'):
                ttk.Separator(self.settings_frame, orient='horizontal').grid(
                    row=i, column=0, columnspan=2, sticky=tk.NSEW)
                tk.Label(self.settings_frame, text=setting_group.replace('_', ' ').title()).grid(
                    row=i+1, column=0, columnspan=2)
                ttk.Separator(self.settings_frame, orient='horizontal').grid(
                    row=i+2, column=0, columnspan=2, sticky=tk.NSEW)
                i += 3

                self.settings_entries[setting_group] = {}
                for setting in self.settings[setting_group].keys():
                    self.settings_entries[setting_group][setting] = (
                        tk.Label(self.settings_frame, text=setting.replace('_', ' ').title()),
                        tk.Entry(self.settings_frame)
                    )
                    label = self.settings_entries[setting_group][setting][0]
                    label.grid(row=i, column=0)
                    entry = self.settings_entries[setting_group][setting][1]
                    entry.insert(tk.END, str(self.settings[setting_group][setting][0]))
                    entry.grid(row=i, column=1)
                    CreateToolTip(label, text=f'{setting_group}.{setting}')
                    CreateToolTip(entry, text=self.settings[setting_group][setting][1])
                    i += 1

        self.settings_frame.grid_rowconfigure(0, weight=1)
        self.settings_frame.grid(row=0, column=0, sticky=tk.N, padx=10, pady=10)

        # gcode panel
        self.gcode_frame = tk.Frame(self.root, highlightthickness=1, highlightcolor='black',
                                    highlightbackground='black')

        ttk.Separator(self.gcode_frame, orient='horizontal').grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        tk.Label(self.gcode_frame, text='Start GCode').grid(row=1, column=0)
        ttk.Separator(self.gcode_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)
        self.start_gcode_text = tk.Text(self.gcode_frame)
        self.start_gcode_text.insert(tk.END, self.settings['start_gcode_default'])
        self.start_gcode_text.grid(row=3, column=0, sticky=tk.NSEW)
        self.settings_entries['start_gcode_default'] = self.start_gcode_text

        ttk.Separator(self.gcode_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)
        tk.Label(self.gcode_frame, text='End GCode').grid(row=6, column=0)
        ttk.Separator(self.gcode_frame, orient='horizontal').grid(row=7, column=0, columnspan=2, sticky=tk.NSEW)
        self.end_gcode_text = tk.Text(self.gcode_frame)
        self.end_gcode_text.insert(tk.END, self.settings['end_gcode_default'])
        self.end_gcode_text.grid(row=8, column=0, sticky=tk.NSEW)
        self.settings_entries['end_gcode_default'] = self.end_gcode_text

        self.gcode_frame.grid_rowconfigure((3, 8), weight=1)
        self.gcode_frame.grid_columnconfigure(0, weight=1)
        self.gcode_frame.grid(row=0, column=1, rowspan=2, sticky=tk.NSEW, padx=10, pady=10)

        # pa calculator
        self.pressure_advance_assist = tk.Frame(self.root, highlightthickness=1, highlightcolor='black',
                                                highlightbackground='black')
        tk.Label(self.pressure_advance_assist, text='PA Calculator').grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        ttk.Separator(self.pressure_advance_assist, orient='horizontal')\
            .grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

        tk.Label(self.pressure_advance_assist, text='Height From Top:').grid(row=2, column=0, sticky=tk.NSEW)
        self.height_entry = tk.Entry(self.pressure_advance_assist)
        self.height_entry.grid(row=2, column=1, sticky=tk.NSEW)

        tk.Label(self.pressure_advance_assist, text='PA Value: ').grid(row=3, column=0, sticky=tk.NSEW)
        self.pa_entry = tk.Entry(self.pressure_advance_assist)
        self.pa_entry.grid(row=3, column=1, sticky=tk.NSEW)

        tk.Button(self.pressure_advance_assist, text='Calculate', command=self.calculate_pa_from_height)\
            .grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)

        self.pressure_advance_assist.grid_rowconfigure(4, weight=1)
        self.pressure_advance_assist.grid_columnconfigure(0, weight=1)
        self.pressure_advance_assist.grid(row=1, column=0, stick=tk.NSEW, padx=10, pady=10)

        # create actions
        self.actions_frame = tk.Frame(self.root, highlightthickness=1, highlightcolor='black',
                                      highlightbackground='black')
        self.save_settings_button = tk.Button(self.actions_frame, text='Save Settings', command=self.save_settings)
        self.save_settings_button.grid(row=0, column=0, sticky=tk.NSEW)

        self.generate_gcode_button = tk.Button(self.actions_frame, text='Generate GCode',
                                               command=lambda: GCodeGenerator.generate(self))
        self.generate_gcode_button.grid(row=0, column=1, sticky=tk.NSEW)

        self.actions_frame.grid_columnconfigure((0, 1), weight=1)
        self.actions_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)

        # show window
        self.root.mainloop()

    @staticmethod
    def load_settings():
        with open('settings.json', 'r') as json_file:
            settings = json.load(json_file)
        return settings

    def update_settings(self):
        for setting_group in self.settings.keys():
            if setting_group not in ('start_gcode_default', 'end_gcode_default'):
                for setting in self.settings[setting_group].keys():
                    try:
                        self.settings[setting_group][setting][0] = int(
                            self.settings_entries[setting_group][setting][1].get())
                    except ValueError:
                        try:
                            self.settings[setting_group][setting][0] = float(
                                self.settings_entries[setting_group][setting][1].get())
                        except ValueError:
                            self.settings[setting_group][setting][0] = \
                                self.settings_entries[setting_group][setting][1].get()
            else:
                self.settings[setting_group] = str(self.settings_entries[setting_group].get('1.0', 'end-1c'))

    def save_settings(self):
        self.update_settings()
        with open('settings.json', 'w') as json_file:
            json.dump(self.settings, json_file, indent=4)

    def calculate_pa_from_height(self):
        height = self.height_entry.get()
        try:
            height = float(height)
        except ValueError:
            height = -1
        pa = self.settings['pressure_advance_settings']['start'][0] + \
            (self.settings['pressure_advance_settings']['finish'][0] -
             self.settings['pressure_advance_settings']['start'][0]) * \
            (height / self.settings['object_settings']['height'][0])
        pa = round(pa, 4)
        self.pa_entry.delete(0, tk.END)
        self.pa_entry.insert(tk.END, pa)


class GCodeGenerator:
    x = y = z = e = 0.0
    current_layer_height = 0.0
    current_layer_nr = 0

    @staticmethod
    def generate(window):
        window.update_settings()
        settings = window.settings

        file = open('pa_test.gcode', 'w')

        # write start gcode to file
        file.write('; --------------------\n')
        file.write(';     gcode header    \n')
        file.write('; --------------------\n')
        for line in settings['start_gcode_default'].split('\n'):
            new_line = GCodeGenerator.process_line(line, settings)
            file.write(new_line)
        file.write('\n')

        # generate model footer
        file.write('; --------------------\n')
        file.write(';    gcode generated  \n')
        file.write(';      model base     \n')
        file.write('; --------------------\n')

        object_width = settings['object_settings']['width'][0]
        extrusion_width = settings['printer_settings']['nozzle_diameter'][0]

        for z in range(3):
            file.write(f'\n; -> layer nr={z+1}\n')
            file.write(GCodeGenerator.next_layer(window.settings))
            file.write(GCodeGenerator.move(-object_width / 2, 0, 'travel_speed', window.settings))
            file.write(GCodeGenerator.move(object_width / 2, 0, 'first_layer_speed', window.settings, extrude=True))
            for i in range(1, 10):
                file.write(GCodeGenerator.move(object_width / 2 + extrusion_width * i, -extrusion_width * i,
                                               'first_layer_speed', window.settings, extrude=True))
                file.write(GCodeGenerator.move(object_width / 2 + extrusion_width * i, extrusion_width * i,
                                               'first_layer_speed', window.settings, extrude=True))
                file.write(GCodeGenerator.move(-object_width / 2 - extrusion_width * i, extrusion_width * i,
                                               'first_layer_speed', window.settings, extrude=True))
                file.write(GCodeGenerator.move(-object_width / 2 - extrusion_width * i, -extrusion_width * i,
                                               'first_layer_speed', window.settings, extrude=True))
        file.write('\n')

        # generate model test area
        file.write('; --------------------\n')
        file.write(';    gcode generated  \n')
        file.write(';       model top     \n')
        file.write('; --------------------\n')

        layer_count = int(settings['object_settings']['height'][0] /
                          settings['extrusion_settings']['other_layer_height'][0])
        for z in range(layer_count):
            file.write(f'\n; -> layer nr={z+4}\n')
            file.write(GCodeGenerator.next_layer(settings))
            pa_value = (settings['pressure_advance_settings']['finish'][0] -
                        settings['pressure_advance_settings']['start'][0]) * z / (layer_count - 1)
            file.write(f'M572 D{settings["printer_settings"]["tool_index"][0]} S{round(pa_value, 4)}\n')
            file.write(
                GCodeGenerator.move(object_width / 2, extrusion_width / 2, 'slow_speed', window.settings, extrude=True))
            file.write(
                GCodeGenerator.move(object_width / 4, extrusion_width / 2, 'fast_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(0, extrusion_width / 2, 'slow_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(
                -object_width / 4, extrusion_width / 2, 'fast_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(
                -object_width / 2, extrusion_width / 2, 'slow_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(
                -object_width / 2, -extrusion_width / 2, 'slow_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(
                -object_width / 4, -extrusion_width / 2, 'fast_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(0, -extrusion_width / 2, 'slow_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(
                object_width / 4, -extrusion_width / 2, 'fast_speed', window.settings, extrude=True))
            file.write(GCodeGenerator.move(
                object_width / 2, -extrusion_width / 2, 'slow_speed', window.settings, extrude=True))

        file.write('\n')

        # write end gcode to file
        file.write('; --------------------\n')
        file.write(';     gcode footer    \n')
        file.write('; --------------------\n')
        for line in settings['end_gcode_default'].split('\n'):
            new_line = GCodeGenerator.process_line(line, settings)
            file.write(new_line)

        file.close()

    @staticmethod
    def process_line(line, settings):
        new_line = ''
        for word in line.split(' '):
            if word.find('[') != -1 and word.find(']') != -1:
                settings_key = word[word.find('[')+1:word.find(']')]
                setting_value = settings
                for level in settings_key.split('.'):
                    setting_value = setting_value[level]
                setting_value = setting_value[0]

                new_line += f'{word[:word.find("[")]}{setting_value}{word[word.find("]")+1:]} '
            else:
                new_line += f'{word} '
        new_line = f'{new_line}\n'
        return new_line

    @staticmethod
    def move(x, y, feedrate, settings, extrude=False):
        x += (settings['printer_settings']['bed_max_x'][0] - settings['printer_settings']['bed_min_x'][0]) / 2
        y += (settings['printer_settings']['bed_max_y'][0] - settings['printer_settings']['bed_min_y'][0]) / 2
        if type(feedrate) is str:
            feedrate = settings['speed_settings'][feedrate][0]
        if extrude:
            extrusion_length = (math.sqrt(math.pow(GCodeGenerator.x - x, 2) + math.pow(GCodeGenerator.y - y, 2)) *
                                settings['printer_settings']['nozzle_diameter'][0] *
                                GCodeGenerator.current_layer_height) / \
                               (math.pow(settings['filament_settings']['filament_diameter'][0], 2) *
                                math.pi * 0.25)
            extrusion_length *= settings['extrusion_settings']['first_layer_extrusion_multiplier'][0] if \
                GCodeGenerator.current_layer_nr == 1 else \
                settings['extrusion_settings']['other_layer_extrusion_multiplier'][0]
            GCodeGenerator.x = x
            GCodeGenerator.y = y
            GCodeGenerator.e += extrusion_length
            return f'G1 X{round(x, 4)} Y{round(y, 4)} E{round(GCodeGenerator.e, 4)} F{feedrate*60}\n'
        else:
            GCodeGenerator.x = x
            GCodeGenerator.y = y
            return f'G1 X{round(x, 4)} Y{round(y, 4)} F{feedrate*60}\n'

    @staticmethod
    def next_layer(settings):
        GCodeGenerator.e = 0
        GCodeGenerator.current_layer_nr += 1
        GCodeGenerator.current_layer_height = settings['extrusion_settings']['first_layer_height'][0] if \
            GCodeGenerator.current_layer_nr == 1 else settings['extrusion_settings']['other_layer_height'][0]
        GCodeGenerator.z += GCodeGenerator.current_layer_height
        return f'G92 E0\nG1 Z{round(GCodeGenerator.z, 4)} F{6000}\n'


if __name__ == '__main__':
    Window(985, 925, 'PA Generator')
