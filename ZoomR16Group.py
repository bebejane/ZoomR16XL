#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/ZoomR16Control/ZoomR16Control.py
from consts import *
from log import *
from ZoomR16Bank import ZoomR16Bank
import Live
import MidiRemoteScript

class ZoomR16Group:

    def __init__(self, controller, tracks, offset):
        self.__controller = controller
        self.__alt_is_pressed = False
        self.__tracks = tracks
        self.__offset = offset
        self.__track_offset = 0
        self.__group_track = None
        self.__banks = []
        self.__bank_index = 0
        self.__track_colors = []

        if tracks[0].is_foldable:
            self.__group_track = tracks[0]
            self.__track_offset = 1

        for t in self.__tracks:
            self.__track_colors.append(t.color)

        self.__build_banks()

    def __add_listeners(self):

        for t in self.__tracks:
            t.add_color_listener(self.__on_track_color_changed)


    def __on_track_color_changed(self):
        for t in self.__tracks:
            self.__track_colors.append(t.color)

    def __build_banks(self):

        banks = []
        bank = []

        for t in self.__tracks:
            if t.is_foldable:
                continue

            if len(bank) == NUM_CHANNEL_STRIPS:
                banks.append(bank)
                bank = []

            bank.append(t)

        if len(bank) > 0:
            banks.append(bank)

        for b in banks:
            self.__banks.append(ZoomR16Bank(self.__controller, b, self.__offset))

    def select_bank(self, index):
        self.__bank_index = index
        self.__banks[index].update_strip_leds()
        return

        tracks = self.__banks[index].tracks()
        for t in tracks:
            if t is not self.__group_track:
                t.color = 16777215

    def unselect_bank(self, index):
        return
        log('uselect bank: ' + str(index))
        tracks = self.__banks[index].tracks()
        for x in range(0, len(tracks)):
            tracks[x].color = self.__track_colors[x]

    def unselect(self):
        for x in range(0, len(self.__banks)):
            self.unselect_bank(x)

    def build_midi_map(self, midi_map_handle):
        self.__banks[self.__bank_index].build_midi_map(midi_map_handle)

    def tracks(self):
        return self.__tracks

    def group_track(self):
        return self.__group_track

    def banks(self):
        return self.__banks

    def num_banks(self):
        return len(self.__banks)

    def offset(self):
        return self.__offset

    def unfold(self):
        if self.__group_track:
            self.__group_track.fold_state = False

    def fold(self):
        if self.__group_track:
            self.__group_track.fold_state = True

    def destroy(self):
        for b in self.__banks:
            b.destroy()
    def set_alt_pressed(self, pressed):
        for x in range(0,len(self.__banks)):
            self.__banks[x].set_alt_pressed(pressed)
        self.__alt_is_pressed = pressed
          
    def is_alt_pressed(self):
        return self.__alt_is_pressed
