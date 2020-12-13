from consts import *
from log import *
import Live
import MidiRemoteScript

class ZoomR16Strip:

    def __init__(self, controller, track, index, offset):
        self.__controller = controller
        self.__alt_is_pressed = False
        self.__track = track
        self.__strip_index = index
        self.__channel_offset = offset
        self.__sid_status = None
        self.__alt_button_down = False
        self.__add_listeners()
        self.refresh_state()

    def build_midi_map(self, midi_map_handle):

        needs_takeover = False
        volume = self.__track.mixer_device.volume
        if not self.is_alt_pressed():
            Live.MidiMap.map_midi_pitchbend(midi_map_handle, volume, self.__channel_offset, not needs_takeover)
        else:
            # Pan with faders when ALT is pressed
            Live.MidiMap.map_midi_pitchbend(midi_map_handle, self.__track.mixer_device.panning, self.__channel_offset, not needs_takeover)

    def __add_listeners(self):
        if self.__track.can_be_armed:
            self.__track.add_arm_listener(self.__update_arm_led)
        self.__track.add_mute_listener(self.__update_mute_led)
        self.__track.add_solo_listener(self.__update_solo_led)
        if not self.song().view.selected_track_has_listener(self.__update_track_is_selected_led):
            self.song().view.add_selected_track_listener(self.__update_track_is_selected_led)

    def __remove_listeners(self):
        if self.__track.can_be_armed:
            self.__track.remove_arm_listener(self.__update_arm_led)
        self.__track.remove_mute_listener(self.__update_mute_led)
        self.__track.remove_solo_listener(self.__update_solo_led)
        self.song().view.remove_selected_track_listener(self.__update_track_is_selected_led)

    def handle_channel_strip_switch_ids(self, sw_id, value):
        log('strip ' + str(sw_id) + ' ' + str(value) + ' ALT:' + str(self.is_alt_pressed()) + ' ' + str(self.__channel_offset))
        if self.is_alt_pressed():
            if sw_id in range(SID_RECORD_ARM_BASE, SID_RECORD_ARM_BASE + NUM_CHANNEL_STRIPS) and sw_id - SID_RECORD_ARM_BASE is self.__channel_offset:
                self.__toggle_monitor_track()
            elif sw_id in range(SID_MUTE_BASE, SID_MUTE_BASE + NUM_CHANNEL_STRIPS) and sw_id - SID_MUTE_BASE is self.__channel_offset:
                self.__toggle_monitor_track()
            elif sw_id in range(SID_SOLO_BASE, SID_SOLO_BASE + NUM_CHANNEL_STRIPS) and sw_id - SID_SOLO_BASE is self.__channel_offset:
                self.__toggle_monitor_track()
            return

        if sw_id in range(SID_RECORD_ARM_BASE, SID_RECORD_ARM_BASE + NUM_CHANNEL_STRIPS):
            if sw_id - SID_RECORD_ARM_BASE is self.__channel_offset:
                if value == BUTTON_STATE_ON:
                    if self.song().exclusive_arm:
                        exclusive = not self.control_is_pressed()
                    else:
                        exclusive = self.control_is_pressed()
                    self.__toggle_arm_track(False)

        elif sw_id in range(SID_SOLO_BASE, SID_SOLO_BASE + NUM_CHANNEL_STRIPS):
            if sw_id - SID_SOLO_BASE is self.__channel_offset:
                if value == BUTTON_STATE_ON:
                    if self.song().exclusive_solo:
                        exclusive = not self.control_is_pressed()
                    else:
                        exclusive = self.control_is_pressed()
                    self.__toggle_solo_track(False)

        elif sw_id in range(SID_MUTE_BASE, SID_MUTE_BASE + NUM_CHANNEL_STRIPS):
            if sw_id - SID_MUTE_BASE is self.__channel_offset:
                if value == BUTTON_STATE_ON:
                    self.__toggle_mute_track()
        elif sw_id in range(SID_SELECT_BASE, SID_SELECT_BASE + NUM_CHANNEL_STRIPS):
            if sw_id - SID_SELECT_BASE is self.__channel_offset:
                if value == BUTTON_STATE_ON:
                    self.__select_track()
        elif sw_id in range(SID_VPOD_PUSH_BASE, SID_VPOD_PUSH_BASE + NUM_CHANNEL_STRIPS):
            if sw_id - SID_VPOD_PUSH_BASE is self.__channel_offset:
                if value == BUTTON_STATE_ON and self.__channel_strip_controller != None:
                    self.__controller.handle_pressed_v_pot(self.__channel_offset, self.__stack_offset)
        elif sw_id in fader_touch_switch_ids:
            if sw_id - SID_FADER_TOUCH_SENSE_BASE is self.__channel_offset:
                if value == BUTTON_STATE_ON or value == BUTTON_RELEASED:
                    if self.__channel_strip_controller != None:
                        touched = value == BUTTON_PRESSED
                        #self.set_is_touched(touched)
                        self.__controller.handle_fader_touch(self.__channel_offset, self.__stack_offset, touched)

    def __toggle_monitor_track(self):
        log('toggle monitor')
        if not self.__track:
            return
        
        if self.__track.current_monitoring_state == Live.Track.Track.monitoring_states.IN:
            self.__track.current_monitoring_state = Live.Track.Track.monitoring_states.OFF
        elif self.__track.current_monitoring_state == Live.Track.Track.monitoring_states.OFF:
            self.__track.current_monitoring_state = Live.Track.Track.monitoring_states.IN        
        elif self.__track.current_monitoring_state == Live.Track.Track.monitoring_states.AUTO:
            self.__track.current_monitoring_state = Live.Track.Track.monitoring_states.IN

        self.refresh_state()

    def __toggle_arm_track(self, exclusive):
        if self.__track and self.__track.can_be_armed:
            self.__track.arm = not self.__track.arm
            if exclusive:
                for t in self.song().tracks:
                    if t != self.__track:
                        t.arm = False

    def __toggle_mute_track(self):
        if self.__track:
            self.__track.mute = not self.__track.mute

    def __toggle_solo_track(self, exclusive):
        if self.__track:
            self.__track.solo = not self.__track.solo
            if exclusive:
                for t in self.song().tracks:
                    if t != self.__track:
                        t.solo = False

    def __update_monitor_led(self):
        
        if not self.is_alt_pressed() or not self.__track:
            return

        monitor_state = self.__track.current_monitoring_state

        if monitor_state == Live.Track.Track.monitoring_states.IN:
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + self.__channel_offset, BUTTON_STATE_ON))
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + self.__channel_offset, BUTTON_STATE_ON))
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + self.__channel_offset, BUTTON_STATE_ON))
        elif monitor_state == Live.Track.Track.monitoring_states.AUTO:
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + self.__channel_offset, BUTTON_PRESSED))
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + self.__channel_offset, BUTTON_PRESSED))
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + self.__channel_offset, BUTTON_PRESSED))
        elif monitor_state == Live.Track.Track.monitoring_states.OFF:
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + self.__channel_offset, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + self.__channel_offset, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + self.__channel_offset, BUTTON_STATE_OFF))

    def __update_arm_led(self):
        if self.__track and self.__track.can_be_armed and self.__track.arm:
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + self.__channel_offset, BUTTON_STATE_ON))
        else:
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + self.__channel_offset, BUTTON_STATE_OFF))

    def __update_mute_led(self):
        if self.__track and self.__track.mute:
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + self.__channel_offset, BUTTON_STATE_ON))
        else:
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + self.__channel_offset, BUTTON_STATE_OFF))

    def __update_solo_led(self):
        if self.__track and self.__track.solo:
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + self.__channel_offset, BUTTON_STATE_ON))
        else:
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + self.__channel_offset, BUTTON_STATE_OFF))

    def __update_track_is_selected_led(self):
        if self.song().view.selected_track == self.__track:
            self.send_midi((NOTE_ON_STATUS, SID_SELECT_BASE + self.__channel_offset, BUTTON_STATE_ON))
        else:
            self.send_midi((NOTE_ON_STATUS, SID_SELECT_BASE + self.__channel_offset, BUTTON_STATE_OFF))

    def refresh_state(self):
        self.__update_arm_led()
        self.__update_mute_led()
        self.__update_solo_led()
        self.__update_track_is_selected_led()
        self.__update_monitor_led()

    def destroy(self):
        self.__remove_listeners()

    def send_midi(self, bytes):
        self.__controller.send_midi(bytes)

    def song(self):
        return self.__controller.song()

    def set_alt_pressed(self, pressed):
        self.__alt_is_pressed = pressed 

    def is_alt_pressed(self):
        return self.__alt_is_pressed
    
    def control_is_pressed(self):
        return False

    def __select_track(self):
        return False
