#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/ZoomR16Control/ZoomR16Control.py
from consts import *
from log import *
import Live
import MidiRemoteScript
from ZoomR16Strip import ZoomR16Strip

class ZoomR16Bank:

    def __init__(self, controller, tracks, offset):
        self.__controller = controller
        self.__alt_is_pressed = False
        self.__tracks = tracks
        self.__offset = offset
        self.__strips = []
        self.__build_strips()

    def __build_strips(self):
        for x in range(0, len(self.__tracks)):
            self.__strips.append(ZoomR16Strip(self.__controller, self.__tracks[x], self.__offset+x, x))

    def build_midi_map(self, midi_map_handle):

        for s in self.__strips:
            s.build_midi_map(midi_map_handle)

    def update_strip_leds(self):
        log('update strip leds')
        for x in range(0, NUM_CHANNEL_STRIPS):
            if len(self.__strips) > x:
                self.__strips[x].refresh_state()
            else:
                self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + x, BUTTON_STATE_OFF))
                self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + x, BUTTON_STATE_OFF))
                self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + x, BUTTON_STATE_OFF))
                self.send_midi((NOTE_ON_STATUS, SID_SELECT_BASE + x, BUTTON_STATE_OFF))

    def handle_channel_strip_switch_ids(self, sw_id, value):

        for s in self.__strips:
            s.handle_channel_strip_switch_ids(sw_id, value)

    def send_midi(self, midi_bytes):
        self.__controller.send_midi(midi_bytes)

    def tracks(self):
        return self.__tracks

    def set_alt_pressed(self, pressed):
        for s in self.__strips:
            s.set_alt_pressed(pressed)
        self.__alt_is_pressed = pressed
        self.update_strip_leds()
        self.__controller.request_rebuild_midi_map()


    def is_alt_pressed(self):
        return self.__alt_is_pressed;
    
    def destroy(self):
        for s in self.__strips:
            s.destroy()
