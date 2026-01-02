from collections import deque
import time
import math
from constants import *

class TowerOfHanoiGame:
    def __init__(self, num_disks=3):
        self.num_disks = num_disks
        self.towers = [deque(), deque(), deque()]
        self.reset_game()
        
        # State variables
        self.selected_tower = None
        self.disk_in_hand = None
        self.game_won = False
        self.game_started = False
        self.show_play_screen = True
        
        # Timer and Stats
        self.start_time = 0
        self.elapsed_time = 0
        self.pickup_time = 0
        self.timer_active = False
        self.moves = 0
        
        # Interaction state
        self.last_action_time = 0
        self.pinch_state = False
        self.pinch_hold_time = 0
        self.hand_position = None
        self.action_message = ""
        self.action_message_time = 0
        self.pinch_indicator_color = PINCH_COLOR_IDLE

    def reset_game(self):
        for tower in self.towers:
            tower.clear()
        
        for i in range(self.num_disks, 0, -1):
            self.towers[0].append(i)
            
        self.selected_tower = None
        self.disk_in_hand = None
        self.game_won = False
        self.moves = 0
        self.elapsed_time = 0
        self.timer_active = False
        self.pinch_state = False
        self.action_message = ""
        
    def check_win(self):
        return len(self.towers[2]) == self.num_disks

    def show_action_message(self, message):
        self.action_message = message
        self.action_message_time = time.time()
        
    def pickup_disc(self, tower_index):
        if self.towers[tower_index]:
            self.disk_in_hand = self.towers[tower_index].pop()
            self.selected_tower = tower_index
            self.pinch_indicator_color = PINCH_COLOR_ACTIVE
            self.show_action_message(f"Picked up disc {self.disk_in_hand} from tower {tower_index+1}")
            self.pickup_time = time.time()
            return True
        return False

    def place_disc(self, tower_index):
        if self.disk_in_hand is None:
            return False
            
        if not self.towers[tower_index] or self.disk_in_hand < self.towers[tower_index][-1]:
            self.towers[tower_index].append(self.disk_in_hand)
            self.moves += 1
            move_time = time.time() - self.pickup_time
            
            if move_time < 1.5:
                self.show_action_message(f"Quick move! Disc {self.disk_in_hand} placed on tower {tower_index+1}")
            else:
                self.show_action_message(f"Disc {self.disk_in_hand} placed on tower {tower_index+1}")
                
            self.disk_in_hand = None
            self.pinch_indicator_color = PINCH_COLOR_IDLE
            return True
        else:
            self.show_action_message("Invalid move! Larger disc cannot go on smaller disc")
            self.towers[self.selected_tower].append(self.disk_in_hand)
            self.disk_in_hand = None
            self.pinch_indicator_color = PINCH_COLOR_ERROR
            return False

    def update_interaction(self, hand_landmarks, camera_width):
        if not hand_landmarks:
            if self.disk_in_hand is not None and self.selected_tower is not None:
                self.towers[self.selected_tower].append(self.disk_in_hand)
                self.disk_in_hand = None
                self.pinch_state = False
                self.show_action_message("Disc returned (hand tracking lost)")
                self.pinch_indicator_color = PINCH_COLOR_ERROR
            return
            
        index_pos, thumb_pos, wrist_pos = hand_landmarks
        
        # Calculate pinch distance
        distance = ((index_pos[0] - thumb_pos[0]) ** 2 + 
                   (index_pos[1] - thumb_pos[1]) ** 2) ** 0.5
                   
        # Average position
        avg_x = (index_pos[0] + thumb_pos[0]) // 2
        avg_y = (index_pos[1] + thumb_pos[1]) // 2
        self.hand_position = (avg_x, avg_y)
        
        # Map to tower
        scaled_x = avg_x * (SCREEN_WIDTH / camera_width)
        if scaled_x < SCREEN_WIDTH / 3:
            tower_index = 0
        elif scaled_x < 2 * SCREEN_WIDTH / 3:
            tower_index = 1
        else:
            tower_index = 2
            
        now = time.time()
        is_pinching = distance < PINCH_THRESHOLD
        
        # Logic state machine
        if is_pinching and not self.pinch_state: # Start pinch
            self.pinch_state = True
            self.pinch_hold_time = now
            self.pinch_indicator_color = PINCH_COLOR_ACTIVE
            
            if self.disk_in_hand is None and self.towers[tower_index] and (now - self.last_action_time > ACTION_COOLDOWN):
                self.pickup_disc(tower_index)
                self.last_action_time = now
                
        elif not is_pinching and self.pinch_state: # Release pinch
            self.pinch_state = False
            self.pinch_indicator_color = PINCH_COLOR_IDLE
            
            if self.disk_in_hand is not None and (now - self.last_action_time > ACTION_COOLDOWN):
                if self.place_disc(tower_index):
                    self.last_action_time = now
                else:
                    self.last_action_time = now
                    
        elif is_pinching: # Holding pinch
            hold_duration = now - self.pinch_hold_time
            if hold_duration > 0.5:
                if self.disk_in_hand is not None:
                     pulse = (math.sin(time.time() * 5) + 1) / 2
                     g_value = int(120 + pulse * 60)
                     self.pinch_indicator_color = (0, g_value, 0, 200)
                else:
                    self.pinch_indicator_color = (0, 180, 0, 200)
