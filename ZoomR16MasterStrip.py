#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/ZoomR16Control/ZoomR16Control.py
from consts import *
from log import *
import Live
import MidiRemoteScript

class ZoomR16MasterStrip:

    def __init__(self, controller):
        self.__controller = controller
        self.__alt_is_pressed = False
        self.__track = self.__controller.song().master_track
        self.__strip_index = 8#len(self.__controller.song().tracks)

    def __add_listeners(self):
        pass

    def __remove_listeners(self):
        pass

    def set_alt_pressed(self, pressed):
        self.__alt_is_pressed = pressed;
        
    def is_alt_pressed(self):
        return self.__alt_is_pressed;
        
    def build_midi_map(self, midi_map_handle):

        needs_takeover = False
        volume = self.__track.mixer_device.volume
        feeback_rule = Live.MidiMap.PitchBendFeedbackRule()
        feeback_rule.channel = self.__strip_index
        feeback_rule.value_pair_map = tuple()
        feeback_rule.delay_in_ms = 200.0
        if not self.is_alt_pressed():
            Live.MidiMap.map_midi_pitchbend(midi_map_handle, volume, self.__strip_index, not needs_takeover)
        else:
            # Pan with faders when ALT is pressed
            Live.MidiMap.map_midi_pitchbend(midi_map_handle, self.__track.mixer_device.panning, self.__strip_index, not needs_takeover)
        


