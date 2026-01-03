from collections import deque
import time
import math
from typing import List, Optional, Tuple, Deque
from constants import *

class TowerOfHanoiGame:
    """
    Manages the logic and state of the Tower of Hanoi game.
    """
    def __init__(self, num_disks: int = 3) -> None:
        """
        Initialize the game state.

        Args:
            num_disks (int): Number of disks to start with.
        """
        self.num_disks: int = num_disks
        self.towers: List[Deque[int]] = [deque(), deque(), deque()]
        
        # State variables
        self.selected_tower: Optional[int] = None
        self.disk_in_hand: Optional[int] = None
        self.game_won: bool = False
        self.game_started: bool = False
        self.show_play_screen: bool = True
        
        # Timer and Stats
        self.start_time: float = 0.0
        self.elapsed_time: float = 0.0
        self.pickup_time: float = 0.0
        self.timer_active: bool = False
        self.moves: int = 0
        
        # Interaction state
        self.last_action_time: float = 0.0
        self.pinch_state: bool = False
        self.pinch_hold_time: float = 0.0
        self.hand_position: Optional[Tuple[int, int]] = None
        self.action_message: str = ""
        self.action_message_time: float = 0.0
        self.pinch_indicator_color: Tuple[int, int, int, int] = PINCH_COLOR_IDLE
        
        # Event System for Audio/UI
        self.last_event: Optional[str] = None

        self.reset_game()

    def reset_game(self) -> None:
        """Resets the game to the initial state."""
        for tower in self.towers:
            tower.clear()
        
        for i in range(self.num_disks, 0, -1):
            self.towers[0].append(i)
            
        self.selected_tower = None
        self.disk_in_hand = None
        self.game_won = False
        self.moves = 0
        self.elapsed_time = 0.0
        self.timer_active = False
        self.pinch_state = False
        self.action_message = ""
        self.last_event = "RESET"

    def check_win(self) -> bool:
        """Checks if the game has been won."""
        return len(self.towers[2]) == self.num_disks

    def show_action_message(self, message: str) -> None:
        """
        Sets a message to be displayed on the UI.
        
        Args:
            message (str): The message to display.
        """
        self.action_message = message
        self.action_message_time = time.time()
        
    def pickup_disc(self, tower_index: int) -> bool:
        """
        Attempts to pick up a disk from the specified tower.

        Args:
            tower_index (int): Index of the tower (0-2).

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.towers[tower_index]:
            self.disk_in_hand = self.towers[tower_index].pop()
            self.selected_tower = tower_index
            self.pinch_indicator_color = PINCH_COLOR_ACTIVE
            self.show_action_message(f"Picked up disc {self.disk_in_hand}")
            self.pickup_time = time.time()
            self.last_event = "PICKUP"
            return True
        return False

    def place_disc(self, tower_index: int) -> bool:
        """
        Attempts to place the currently held disk onto a tower.

        Args:
            tower_index (int): Index of the target tower (0-2).

        Returns:
            bool: True if placement was valid, False otherwise.
        """
        if self.disk_in_hand is None:
            return False
            
        # Check valid move rule: Empty tower OR smaller disk on larger disk
        if not self.towers[tower_index] or self.disk_in_hand < self.towers[tower_index][-1]:
            self.towers[tower_index].append(self.disk_in_hand)
            self.moves += 1
            
            # Message logic
            move_time = time.time() - self.pickup_time
            if move_time < 1.5:
                self.show_action_message("Quick move!")
            else:
                self.show_action_message(f"Placed on tower {tower_index+1}")
                
            self.disk_in_hand = None
            self.pinch_indicator_color = PINCH_COLOR_IDLE
            self.last_event = "DROP_VALID"
            return True
        else:
            self.show_action_message("Invalid move!")
            # Return to original tower
            self.towers[self.selected_tower].append(self.disk_in_hand)
            self.disk_in_hand = None
            self.pinch_indicator_color = PINCH_COLOR_ERROR
            self.last_event = "DROP_INVALID"
            return False

    def update_interaction(self, hand_landmarks: Optional[List[Tuple[float, float]]], camera_width: int) -> None:
        """
        Updates game interaction based on hand tracking data.

        Args:
            hand_landmarks: List of (x, y) tuples for index, thumb, wrist.
            camera_width: Width of the camera/renderer for scaling logic.
        """
        self.last_event = None # Reset event frame
        
        if not hand_landmarks:
            if self.disk_in_hand is not None and self.selected_tower is not None:
                self.towers[self.selected_tower].append(self.disk_in_hand)
                self.disk_in_hand = None
                self.pinch_state = False
                self.show_action_message("Lost tracking - Disc returned")
                self.pinch_indicator_color = PINCH_COLOR_ERROR
                self.last_event = "DROP_INVALID"
            return
            
        index_pos, thumb_pos, _ = hand_landmarks
        
        # Calculate pinch distance (Euclidean)
        distance = math.hypot(index_pos[0] - thumb_pos[0], index_pos[1] - thumb_pos[1])
                   
        # Average position (Centroid of pinch)
        avg_x = (index_pos[0] + thumb_pos[0]) // 2
        avg_y = (index_pos[1] + thumb_pos[1]) // 2
        self.hand_position = (int(avg_x), int(avg_y))
        
        # Map to tower zones
        # Assuming screen is split into 3 columns
        scaled_x = avg_x * (SCREEN_WIDTH / camera_width)
        if scaled_x < SCREEN_WIDTH / 3:
            tower_index = 0
        elif scaled_x < 2 * SCREEN_WIDTH / 3:
            tower_index = 1
        else:
            tower_index = 2
            
        now = time.time()
        is_pinching = distance < PINCH_THRESHOLD
        
        # --- State Machine ---
        
        # 1. Start Pinch
        if is_pinching and not self.pinch_state:
            self.pinch_state = True
            self.pinch_hold_time = now
            self.pinch_indicator_color = PINCH_COLOR_ACTIVE
            
            # Attempt Pickup
            if self.disk_in_hand is None:
                 if self.towers[tower_index]:
                      if now - self.last_action_time > ACTION_COOLDOWN:
                          self.pickup_disc(tower_index)
                          self.last_action_time = now
            
        # 2. Release Pinch
        elif not is_pinching and self.pinch_state:
            self.pinch_state = False
            self.pinch_indicator_color = PINCH_COLOR_IDLE
            
            # Attempt Place
            if self.disk_in_hand is not None:
                if now - self.last_action_time > ACTION_COOLDOWN:
                    self.place_disc(tower_index)
                    self.last_action_time = now
                    
        # 3. Holding Pinch (Visual Feedback)
        elif is_pinching:
            hold_duration = now - self.pinch_hold_time
            if hold_duration > 0.5:
                # Pulse effect
                pulse = (math.sin(time.time() * 8) + 1) / 2
                if self.disk_in_hand is not None:
                     # Carrying
                     val = int(150 + pulse * 105)
                     self.pinch_indicator_color = (0, val, 255, 200)
                else:
                    # Empty pinch
                    self.pinch_indicator_color = (100, 100, 100, 200)
