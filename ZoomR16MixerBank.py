#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/ZoomR16Control/ZoomR16Control.py
from consts import *
from log import *
import Live
import MidiRemoteScript
from ZoomR16Strip import ZoomR16Strip

class ZoomR16MixerBank:

    def __init__(self, controller):
        self.__controller = controller
        self.__alt_is_pressed = False
        self.__tracks = []
        self.__offsets = []
        self.__strips = []
        self.__build_strips()

    def __build_strips(self):

        self.__strips = []
        offset = 0
        for x in range(0, len(self.__controller.song().tracks)):
            t = self.__controller.song().tracks[x]
            if t.is_foldable:
                self.__strips.append(ZoomR16Strip(self.__controller, t, x, offset))
                offset += 1

    def build_midi_map(self, midi_map_handle):

        for s in self.__strips:
            s.build_midi_map(midi_map_handle)

    def reset_strip_leds(self):
        for x in range(0, NUM_CHANNEL_STRIPS):
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + x, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + x, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + x, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_SELECT_BASE + x, BUTTON_STATE_OFF))

    def send_midi(self, midi_bytes):
        self.__controller.send_midi(midi_bytes)

    def set_alt_pressed(self, pressed):
        self.__alt_is_pressed = pressed
        
    def is_alt_pressed(self):
        return self.__alt_is_pressed
