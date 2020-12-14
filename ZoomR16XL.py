# Zoom R16 Control Surface script
# Version 1.0.0
# Author: Bebe Jane
# https://github.com/bebejane/ZoomR16XL

from __future__ import division
from consts import *
from log import *
from ZoomR16Group import ZoomR16Group
from ZoomR16MasterStrip import ZoomR16MasterStrip
from ZoomR16MixerBank import ZoomR16MixerBank
from ZoomR16Transport import ZoomR16Transport

import Live
import MidiRemoteScript
import time
import inspect
import logging
import threading

class ZoomR16XL:

    def __init__(self, c_instance):
        log('ZoomR16XL Version: ' + VERSION)
        self.__c_instance = c_instance
        self.__shift_pressed = False
        self.__alt_pressed = False
        self.__rwd_pressed = False
        self.__ffwd_pressed = False
        self.__stop_pressed = False
        self.__play_pressed = False
        self.__jog_dial_map_mode = Live.MidiMap.MapMode.absolute
        self.__groups = []
        self.__bank_map = []
        self.__bank_map_index = 0
        self.__group_index = 0
        self.__bank_index = 0
        self.__selected_track = None
        self.__selected_group = None
        self.__selected_bank = None
        self.__mixer_mode = False
        self.__loop_start = None
        self.__loop_end = None
        self.__loop_length = None
        self.__master_strip = ZoomR16MasterStrip(self)
        self.__mixer_bank = ZoomR16MixerBank(self)
        self.__transport = ZoomR16Transport(self)

        self.__init_groups()
        self.__add_listeners()

    def build_midi_map(self, midi_map_handle):

        for i in range(SID_FIRST, SID_LAST + 1):
            Live.MidiMap.forward_midi_note(self.handle(), midi_map_handle, 0, i)

        Live.MidiMap.forward_midi_cc(self.handle(), midi_map_handle, 0, JOG_WHEEL_CC_NO)

        if self.__mixer_mode:
            self.__mixer_bank.build_midi_map(midi_map_handle)
        elif self.__selected_group:
            self.__selected_group.build_midi_map(midi_map_handle)
            #for g in self.__groups:
            #    g.unselect()
            # self.__selected_group.select_bank(self.__bank_index)

        self.__master_strip.build_midi_map(midi_map_handle)

    def receive_midi(self, midi_bytes):

        cc = midi_bytes[1]
        val = midi_bytes[2]
        note_on = val == NOTE_ON_STATUS
        button_on = val == BUTTON_STATE_ON

        if cc == SID_BANK_PREV and button_on:
            self.__prev_bank()
        elif cc == SID_BANK_NEXT and button_on:
            self.__next_bank()
        elif cc in channel_strip_control_switch_ids and button_on:
            self.__selected_bank.handle_channel_strip_switch_ids(cc, val)
        elif cc in function_key_control_switch_ids:
            self.__handle_function_key_switch_ids(cc, val)
        elif midi_bytes[0] & 240 == NOTE_ON_STATUS or midi_bytes[0] & 240 == NOTE_OFF_STATUS:
            note = midi_bytes[1]
            value = BUTTON_PRESSED if midi_bytes[2] > 0 else BUTTON_RELEASED
            if note in range(SID_FIRST, SID_LAST + 1):
                ##if note in function_key_control_switch_ids:
                #    self.__software_controller.handle_function_key_switch_ids(note, value)
                #if note in software_controls_switch_ids:
                #    self.__software_controller.handle_software_controls_switch_ids(note, value)
                if note in transport_control_switch_ids:
                    self.__transport.handle_transport_switch_ids(note, value)
                if note in marker_control_switch_ids:
                    self.__transport.handle_marker_switch_ids(note, value)

                if note in jog_wheel_switch_ids:
                    self.__transport.handle_jog_wheel_switch_ids(note, value)
        elif midi_bytes[0] & 240 == CC_STATUS:
            cc_no = midi_bytes[1]
            cc_value = midi_bytes[2]
            if cc_no == JOG_WHEEL_CC_NO:
                self.__transport.handle_jog_wheel_rotation(cc_value)
            #elif cc_no in range(FID_PANNING_BASE, FID_PANNING_BASE + NUM_CHANNEL_STRIPS):
            #    for s in self.__channel_strips:
            #        s.handle_vpot_rotation(cc_no - FID_PANNING_BASE, cc_value)

        #log('recieve midi: ' + str(cc) + ' = ' + str(val))

    def __handle_function_key_switch_ids(self, cc, val):
        #log(str(cc) + ' ' + str(val))
        if cc == SID_SOFTWARE_F1:
            self.__set_alt_pressed(val == BUTTON_STATE_ON)
            return
        if val != BUTTON_STATE_ON:
            return

        if cc == SID_SOFTWARE_F2:
            if not self.__alt_pressed:
                self.__toggle_loop()
            else:
                self.song().view.follow_song = not self.song().view.follow_song

        elif cc == SID_SOFTWARE_F3:
            if not self.__alt_pressed:
                self.song().jump_by(-4)
            else:
                self.__edit_loop_length(False)
        elif cc == SID_SOFTWARE_F4:
            if not self.__alt_pressed:
                self.song().jump_by(4)
            else:
                self.__edit_loop_length(True)
        elif cc == SID_SOFTWARE_F5:
            if not self.__alt_pressed:
                self.toggle_view()
            else:
                self.__toggle_all_views()

    def __set_alt_pressed(self, pressed):
        self.__alt_pressed = pressed
        for x in range(0,len(self.__groups)):
            self.__groups[x].set_alt_pressed(pressed)
        self.__transport.set_alt_pressed(pressed)
        self.__master_strip.set_alt_pressed(pressed) 
        #log('ALT PRESSED: ' + str(pressed))

    def is_alt_pressed(self):
        return self.__alt_pressed

    def __toggle_all_views(self):
        if self.application().view.is_view_visible('Detail') and self.application().view.is_view_visible('Browser'):
            self.__toggle_view('Detail', False)
            self.__toggle_view('Browser', False)
        else:
            self.__toggle_view('Detail', True)
            self.__toggle_view('Browser', True)

    def __toggle_view(self, name, visible):
        views = self.application().view.available_main_views()
        for view in views:
            log(str(view))

        if self.application().view.is_view_visible(name) and visible is not True:
            self.application().view.hide_view(name)
        else:
            self.application().view.show_view(name)
    
    def __add_listeners(self):
        self.song().add_tracks_listener(self.__on_tracks_change)
        self.song().view.add_selected_track_listener(self.__on_track_selected)

    def __remove_listeners(self):
        self.song().remove_tracks_listener(self.__on_tracks_change)
        self.song().view.remove_selected_track_listener(self.__on_track_selected)

    def __on_tracks_change(self):
        self.__init_groups()

    def __on_track_selected(self):
        log('SELECTED TRACK: ' + self.song().view.selected_track.name)
        self.__set_bank_to_selected_track()

    def __init_groups(self):

        if len(self.song().tracks) <= 0:
            return

        log('INIT GROUPS: ' + str(len(self.song().tracks)) + ' tracks')
        tracks = self.song().tracks;
        length = len(tracks)

        idx = -1
        offset = 0
        groups = []
        in_group = False
        group_tracks = []
        bank_map = []

        for x in range(0, length):

            if tracks[x].is_foldable:
                if len(group_tracks) > 0:
                    groups.append(group_tracks)
                group_tracks = []
                group_tracks.append(tracks[x])
                in_group = True
                continue

            if tracks[x].is_grouped and in_group:
                group_tracks.append(tracks[x])
                continue

            if len(group_tracks) > 0 and in_group:
                groups.append(group_tracks)
                group_tracks = []
                in_group = False

            if len(group_tracks) == NUM_CHANNEL_STRIPS:
                groups.append(group_tracks)
                group_tracks = []

            group_tracks.append(tracks[x])

        if len(group_tracks) > 0:
            groups.append(group_tracks)

        for x in range(0,len(groups)):

            log('Group ' + str(x+1) + ', Offset: ' + str(offset) + ', ' + str(len(groups[x])) + ' tracks')
            log('----------------------')
            for t in groups[x]:
                log('- ' + t.name)
            log('')


            groups[x] = ZoomR16Group(self.__c_instance, groups[x], offset)
            offset += len(groups[x].tracks())

            for b in range(0, groups[x].num_banks()):
                bank_map.append([b,x])

        self.__groups = groups
        self.__bank_map = bank_map
        self.__set_bank_to_selected_track()

    def __select_bank(self, index):

        self.__bank_map_index = index
        self.__bank_index = self.__bank_map[index][0]
        self.__group_index = self.__bank_map[index][1]
        self.__selected_group = self.__groups[self.__group_index]
        self.__selected_bank = self.__selected_group.banks()[self.__bank_index]

        if self.application().view.focused_document_view == 'Arranger':
            for x in range(0, len(self.__groups)):
                self.__groups[x].fold()

            self.__selected_group.unfold()


        self.__selected_group.select_bank(self.__bank_index)

        log('Select group/bank: ' + str(self.__group_index) + '/' +str(self.__bank_index))
        self.request_rebuild_midi_map()

    def __set_bank_to_selected_track(self):

        selected_track = self.song().view.selected_track
        ptr = selected_track._live_ptr
        bank_index = None
        group_index = None

        for x in range(0,len(self.__groups)):
            g = self.__groups[x]
            gt = self.__groups[x].group_track()

            if gt and gt._live_ptr == ptr:
                group_index = x
                bank_index = 0
                break

            for i in range(0, len(g.banks())):
                b = g.banks()[i]
                for t in b.tracks():
                    if t._live_ptr == ptr:
                        bank_index = i
                        group_index = x
                        break

        if bank_index == None:
            group_index = 0
            bank_index = 0

        for i in range(0, len(self.__bank_map)):
            m = self.__bank_map[i]
            if m[1] == group_index and m[0] == bank_index:
                self.__select_bank(i)
                break

    def __browse_banks(self, nextbank):

        if self.__mixer_mode:
            return

        bank = self.__bank_map_index

        if nextbank and len(self.__bank_map) > bank+1:
            bank += 1
        elif not nextbank and bank-1 >= 0:
            bank -= 1

        self.__select_bank(bank)

    def __next_bank(self):
        self.__browse_banks(True)

    def __prev_bank(self):
        self.__browse_banks(False)

    def __select_group(self, index):
        self.__groups[index].select_bank(0)

    def __set_mixer_mode(self, on):

        log('MIXER MODE: '+ str(on))

        if on:
            self.__mixer_mode = True
            self.__clear_all_leds()
            for t in self.song().tracks:
                if t.is_foldable:
                    t.fold_state = True
        else:
            self.__mixer_mode = False
            for t in self.song().tracks:
                if t.is_foldable:
                    t.fold_state = False
            self.__select_bank(self.__bank_map_index)

        self.request_rebuild_midi_map()
        
    def __toggle_loop(self):
        
        beat = self.song().get_current_beats_song_time()
        log('Set loop point at: ' + str(beat) + ' ' + str(self.beat_to_time(beat)))
        if self.__loop_start == None and self.__loop_end == None:
            self.__loop_start = int(((beat.bars-1) * 4)) + (beat.beats-1)
            if beat.sub_division > 2:
                self.__loop_start = self.__loop_start+1

            self.__loop_length = 1
            self.song().loop = False
            self.song().loop_start = self.__loop_start
            self.song().loop_end = self.__loop_start
            self.song().loop_length = 1
            log('Set loop in: ' + str(beat) + ', bars: ' + str(beat.bars) + ', new: ' + str(self.song().get_beats_loop_start()))

        elif self.__loop_start is not None and self.__loop_end == None:
            
            self.__loop_end = ((beat.bars-1) * 4) + (beat.beats-1)

            if beat.sub_division > 2:
                self.__loop_end = self.__loop_end+1
            
            if self.__loop_end - self.__loop_start <= 0:
                self.__loop_end = self.__loop_start+1

            self.__loop_length = self.__loop_end - self.__loop_start
            self.song().loop_length = self.__loop_length
            self.song().loop = True
            self.song().current_song_time = self.__loop_start
            
        elif self.__loop_start is not None and self.__loop_end is not None:
            self.song().loop = False
            self.__loop_start = None
            self.__loop_end = None
            log('DISABLE LOOP')

        log('LOOPING: ' + str(self.__loop_start) + ' > ' +  str(self.__loop_end))

    def __edit_loop_length(self, extend):
        if self.__loop_start == None or self.__loop_end == None:
            return
        if extend:
            self.song().loop_length = self.song().loop_length+1
        elif self.song().loop_length > 1:
            self.song().loop_length = self.song().loop_length-1
        self.__loop_length = self.song().loop_length
        self.song().current_song_time = self.__loop_start

    def __clear_all_leds(self):
        for x in range(0, NUM_CHANNEL_STRIPS):
            self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + x, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + x, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + x, BUTTON_STATE_OFF))
            self.send_midi((NOTE_ON_STATUS, SID_SELECT_BASE + x, BUTTON_STATE_OFF))

    def disconnect(self):

        self.__remove_listeners()
        for g in self.__groups:
            g.destroy()

    
    def mixer_mode(self):
        return self.__mixer_mode

    def toggle_view(self):

        view = self.application().view.focused_document_view

        if view == 'Arranger':
            self.application().view.focus_view('Session')
        else:
            self.application().view.focus_view('Arranger')

    def request_rebuild_midi_map(self):
        self.__c_instance.request_rebuild_midi_map()

    def connect_script_instances(self, instanciated_scripts):
        log('Zoom R16 connected')
        self.run_startup_animation()

    def thread_test(self, arg):
        log('thread')

    def suggest_input_port(self):
        return str('Zoom R16')

    def suggest_output_port(self):
        return str('Zoom R16')

    def can_lock_to_devices(self):
        return True
    
    def request_rebuild_midi_map(self):
        self.__c_instance.request_rebuild_midi_map()

    def send_midi(self, midi_event_bytes):
        self.__c_instance.send_midi(midi_event_bytes)

    def send_cc(self, midi_event_bytes, value):
        self.__c_instance.send_cc(midi_event_bytes, value)

    def handle(self):
        return self.__c_instance.handle()

    def application(self):
        return Live.Application.get_application()

    def song(self):
        return self.__c_instance.song()

    def update_display(self):
        return

    def beat_to_time(self, beat):
        dem = self.song().signature_denominator
        num = self.song().signature_numerator
        bps = 60/self.song().tempo
        return ((((beat.bars-1)*dem) + (beat.beats-1)) * bps) + (((beat.sub_division-1)/dem)*bps) + (((beat.ticks-1)/100)*bps)

    def run_startup_animation(self):
        log('running startup animatipn')
        speed = 0.1
        rounds = 1
        pattern = [
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,1,1,0,0,0],
            [0,0,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1],
            [1,1,1,0,0,1,1,1],
            [1,1,0,0,0,0,1,1],
            [1,0,0,0,0,0,0,1],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [1,0,0,0,0,0,0,1],
            [1,1,0,0,0,0,1,1],
            [0,1,1,0,0,1,1,0],
            [0,0,1,1,1,1,0,0],
            [0,0,0,1,1,0,0,0],
            [0,0,0,0,0,0,0,0]
        ]
        end_pattern = [
            [0,0,0,0,0,0,0,0],
            [0,0,0,1,1,0,0,0],
            [0,0,1,1,1,1,0,0],
            [0,1,1,0,0,1,1,0],
            [1,1,0,0,0,0,1,1],
            [1,0,0,0,0,0,0,1],
            [1,1,0,0,0,0,1,1],
            [1,1,1,0,0,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [0,0,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1],
            [0,0,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1],
            [0,0,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
        ]
        # Pattern animation
        for i in range(rounds):
            for p in pattern:
                for ch in range(len(p)):
                    if p[ch] == 1:
                        self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + ch, BUTTON_STATE_ON))
                        self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + ch, BUTTON_STATE_ON))
                        self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + ch, BUTTON_STATE_ON))
                    else:
                        self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + ch, BUTTON_STATE_OFF))
                        self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + ch, BUTTON_STATE_OFF))
                        self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + ch, BUTTON_STATE_OFF))

                time.sleep(speed)

        # End pattern
        for p in end_pattern:
            for ch in range(len(p)):
                if p[ch] == 1:
                    self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + ch, BUTTON_STATE_ON))
                    self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + ch, BUTTON_STATE_ON))
                    self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + ch, BUTTON_STATE_ON))
                else:
                    self.send_midi((NOTE_ON_STATUS, SID_RECORD_ARM_BASE + ch, BUTTON_STATE_OFF))
                    self.send_midi((NOTE_ON_STATUS, SID_MUTE_BASE + ch, BUTTON_STATE_OFF))
                    self.send_midi((NOTE_ON_STATUS, SID_SOLO_BASE + ch, BUTTON_STATE_OFF))

            time.sleep(speed)

        if self.__selected_bank != None:
            self.__selected_bank.update_strip_leds()


