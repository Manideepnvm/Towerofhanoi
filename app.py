import cv2
import numpy as np
import pygame
import sys
import time
import os
from collections import deque
import mediapipe as mp
import math

class TowerOfHanoiGame:
    def __init__(self, num_disks=3):
        # GUI settings
        self.width, self.height = 1280, 720  # Higher resolution for better UI
        
        # Initialize game state
        self.num_disks = num_disks
        self.towers = [deque(), deque(), deque()] 
        self.tower_positions = [self.width//4, self.width//2, 3*self.width//4]
        self.reset_game()
        
        # Game state
        self.selected_tower = None
        self.disk_in_hand = None
        self.game_won = False
        self.game_started = False
        self.show_play_screen = True
        
        self.tower_width = 20
        self.tower_height = 300
        self.tower_y = 250
        self.tower_x_positions = [self.width//4, self.width//2, 3*self.width//4]
        self.disk_height = 30
        self.base_disk_width = 200
        self.disk_colors = [(220, 20, 60), (50, 205, 50), (65, 105, 225), (255, 215, 0), (148, 0, 211)]
        
        # Timer variables
        self.start_time = 0
        self.elapsed_time = 0
        self.pickup_time = 0
        self.timer_active = False
        
        # Move counter
        self.moves = 0
        
        # Finger tracking variables
        self.finger_positions = []
        self.last_action_time = 0
        self.action_cooldown = 0.3  # Reduced cooldown for more responsive controls
        self.pinch_threshold = 50   # Reduced threshold for easier pinch detection
        self.pinch_state = False    # Track if currently pinching
        self.pinch_hold_time = 0    # Time pinch has been held
        self.hand_position = None   # Current hand position for disk placement
        
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Tower of Hanoi - Gesture Control")
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        # Load fonts
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.font = pygame.font.SysFont('Arial', 28)
        self.small_font = pygame.font.SysFont('Arial', 20)
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        
        # Create transparent background
        self.background = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Create play button - properly centered
        self.play_button_rect = pygame.Rect(0, 0, 200, 60)
        self.play_button_rect.center = (self.width//2, self.height//2 + 50)
        
        # Initialize the camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            sys.exit()
            
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Visual feedback for pinching
        self.pinch_indicator_color = (255, 255, 255, 128)  # White with transparency
        
        # Add disk pickup and placement indicators
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.0  # Show message for 2 seconds
    
    def reset_game(self):
        # Clear all towers
        for tower in self.towers:
            tower.clear()
        
        # Start with all disks on the first tower
        for i in range(self.num_disks, 0, -1):
            self.towers[0].append(i)
        
        # Reset game state
        self.selected_tower = None
        self.disk_in_hand = None
        self.game_won = False
        self.moves = 0
        self.elapsed_time = 0
        self.timer_active = False
        self.pinch_state = False
        self.action_message = ""
        
    def is_valid_move(self, from_tower, to_tower):
        if not self.towers[from_tower]:  # Source tower is empty
            return False
        
        if not self.towers[to_tower]:  # Destination tower is empty
            return True
        
        # Check if disk on source is smaller than disk on destination
        return self.towers[from_tower][-1] < self.towers[to_tower][-1]
    
    def check_win(self):
        # Game is won if all disks are on tower 2 (index 2)
        return len(self.towers[2]) == self.num_disks
    
    def detect_hands(self, frame):
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image and find hands
        results = self.hands.process(rgb_frame)
        
        hand_landmarks = []
        
        # If hands are detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks on the image
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style())
                
                # Get the position of the index finger tip and thumb tip
                index_finger_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                
                # Also get the wrist position for better hand tracking
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                
                # Convert the normalized coordinates to pixel coordinates
                h, w, _ = frame.shape
                index_x, index_y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
                wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)
                
                # Store the coordinates
                hand_landmarks = [(index_x, index_y), (thumb_x, thumb_y), (wrist_x, wrist_y)]
        
        return hand_landmarks, frame
    
    def pickup_disc(self, tower_index):
        """Improved disc pickup with better visual feedback"""
        if self.towers[tower_index]:
            self.disk_in_hand = self.towers[tower_index].pop()
            self.selected_tower = tower_index
            
            # Enhanced visual feedback
            self.pinch_indicator_color = (50, 200, 50, 230)  # Bright green when holding
            self.show_action_message(f"Picked up disc {self.disk_in_hand} from tower {tower_index+1}")
            
            # Start tracking picked disc time for analytics
            self.pickup_time = time.time()
            return True
        return False

    def place_disc(self, tower_index):
        """Improved disc placement with validation and feedback"""
        if self.disk_in_hand is None:
            return False
            
        # Check if the move is valid
        if not self.towers[tower_index] or self.disk_in_hand < self.towers[tower_index][-1]:
            # Valid move
            self.towers[tower_index].append(self.disk_in_hand)
            
            # Track move analytics
            self.moves += 1
            move_time = time.time() - self.pickup_time
            
            # Give feedback based on move time
            if move_time < 1.5:
                self.show_action_message(f"Quick move! Disc {self.disk_in_hand} placed on tower {tower_index+1}")
            else:
                self.show_action_message(f"Disc {self.disk_in_hand} placed on tower {tower_index+1}")
                
            self.disk_in_hand = None
            self.pinch_indicator_color = (255, 255, 255, 128)  # Reset to default
            return True
        else:
            # Invalid move
            self.show_action_message("Invalid move! Larger disc cannot go on smaller disc")
            # Animated shake effect can be added here
            
            # Return disc to original tower
            self.towers[self.selected_tower].append(self.disk_in_hand)
            self.disk_in_hand = None
            self.pinch_indicator_color = (255, 100, 100, 200)  # Red for invalid
            return False

    def interpret_hand_gesture(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) < 3:
            # If hand is lost, release any held disk with visual indication
            if self.disk_in_hand is not None and self.selected_tower is not None:
                self.towers[self.selected_tower].append(self.disk_in_hand)
                self.disk_in_hand = None
                self.pinch_state = False
                self.show_action_message("Disc returned (hand tracking lost)")
                # Flash red indicator
                self.pinch_indicator_color = (255, 0, 0, 200)
            return None
        
        # Get positions of index finger, thumb, and wrist
        index_finger_pos, thumb_pos, wrist_pos = hand_landmarks
        
        # Calculate distance between index finger and thumb (pinch detection)
        distance = ((index_finger_pos[0] - thumb_pos[0]) ** 2 + 
                    (index_finger_pos[1] - thumb_pos[1]) ** 2) ** 0.5
        
        # Get the average position (center between fingers)
        avg_x = (index_finger_pos[0] + thumb_pos[0]) // 2
        avg_y = (index_finger_pos[1] + thumb_pos[1]) // 2
        
        # Save hand position for disk positioning
        self.hand_position = (avg_x, avg_y)
        
        # Map x position to tower index (scaled to screen width)
        camera_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        scaled_x = avg_x * (self.width / camera_width)
        
        # Determine which tower the hand is over with improved indicators
        if scaled_x < self.width / 3:
            tower_index = 0
        elif scaled_x < 2 * self.width / 3:
            tower_index = 1
        else:
            tower_index = 2
        
        now = time.time()
        
        # Detect pinch state (close fingers)
        is_pinching = distance < self.pinch_threshold
        
        # State transitions with improved responsiveness
        if is_pinching and not self.pinch_state:
            # Just started pinching
            self.pinch_state = True
            self.pinch_hold_time = now
            self.pinch_indicator_color = (0, 255, 0, 180)  # Green
            
            # Pick up a disk if none in hand
            if self.disk_in_hand is None and self.towers[tower_index] and now - self.last_action_time > self.action_cooldown:
                self.pickup_disc(tower_index)  # Use new method
                self.last_action_time = now
                return f"Picked up disc from tower {tower_index+1}"
                
        elif not is_pinching and self.pinch_state:
            # Just released pinch
            self.pinch_state = False
            self.pinch_indicator_color = (255, 255, 255, 128)  # White
            
            # Place disk if one is in hand
            if self.disk_in_hand is not None and now - self.last_action_time > self.action_cooldown:
                # Use improved placement method
                if self.place_disc(tower_index):
                    self.last_action_time = now
                    return f"Placed disc on tower {tower_index+1}"
                else:
                    self.last_action_time = now
                    return "Invalid move"
        
        elif is_pinching:
            # Continuing to pinch - update color based on pinch duration for better feedback
            hold_duration = now - self.pinch_hold_time
            if hold_duration > 0.5:  # Held for more than half a second
                if self.disk_in_hand is not None:
                    # Pulsing effect when holding disc
                    pulse = (math.sin(time.time() * 5) + 1) / 2  # Value between 0 and 1
                    g_value = int(120 + pulse * 60)  # Green value pulsing between 120 and 180
                    self.pinch_indicator_color = (0, g_value, 0, 200)
                else:
                    self.pinch_indicator_color = (0, 180, 0, 200)  # Darker green
        
        return None
    
    def show_action_message(self, message):
        self.action_message = message
        self.action_message_time = time.time()
    
    # Fixed play button alignment and UI
    def draw_play_screen(self):
        # Start with a transparent background
        self.screen.fill((0, 0, 0))  # Use solid black for cleaner UI
        
        # Draw a gradient background for better aesthetics
        for i in range(self.height):
            gradient_color = (15, 15, max(10, min(50, 30 + i // 10)), 255)
            pygame.draw.line(self.screen, gradient_color, (0, i), (self.width, i))
        
        # Add a semi-transparent overlay for better UI visibility
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((15, 15, 30, 200))  # Dark blue-black with alpha
        self.screen.blit(overlay, (0, 0))
        
        # Draw title with shadow effect
        title_shadow = self.title_font.render("Tower of Hanoi", True, (30, 30, 50))
        title_text = self.title_font.render("Tower of Hanoi", True, (255, 255, 255))
        subtitle_text = self.font.render("Gesture Controlled", True, (180, 180, 180))
        
        # Calculate exact center positions
        title_rect = title_text.get_rect(center=(self.width//2, self.height//4))
        shadow_rect = title_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        subtitle_rect = subtitle_text.get_rect(center=(self.width//2, self.height//4 + 60))
        
        # Draw shadow then text
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw instructions with improved box
        instructions = [
            "Control the game using your hand gestures:",
            "• Use pinch gesture (thumb and index finger) to pick up discs",
            "• Hold the pinch and move to position the disc",
            "• Release the pinch to place the disc on a tower",
            "• Win by moving all discs to the rightmost tower",
            "",
            ""
        ]
        
        # Draw instruction box with rounded corners
        instruction_box = pygame.Surface((600, 220), pygame.SRCALPHA)
        instruction_box.fill((0, 0, 0, 150))
        instruction_rect = instruction_box.get_rect(center=(self.width//2, self.height//2 - 80))
        pygame.draw.rect(instruction_box, (65, 105, 225, 50), instruction_box.get_rect(), 2, border_radius=15)
        self.screen.blit(instruction_box, instruction_rect)
        
        # Add a title to the instruction box
        instr_title = self.font.render("How to Play", True, (180, 180, 255))
        instr_title_rect = instr_title.get_rect(center=(self.width//2, instruction_rect.top + 25))
        self.screen.blit(instr_title, instr_title_rect)
        
        for i, line in enumerate(instructions):
            instruction_text = self.small_font.render(line, True, (200, 200, 200))
            instruction_rect = instruction_text.get_rect(midleft=(instruction_rect.left + 30, instruction_rect.top + 55 + i*26))
            self.screen.blit(instruction_text, instruction_rect)
        
        # Draw play button with proper centered alignment and improved appearance
        self.play_button_rect = pygame.Rect(0, 0, 200, 60)
        self.play_button_rect.center = (self.width//2, self.height//2 + 120)  # Fixed position
        
        # Draw button shadow for depth
        shadow_rect = self.play_button_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(self.screen, (30, 50, 100, 150), shadow_rect, border_radius=30)
        
        # Draw glowing effect for button
        glow_size = int(5 + math.sin(time.time() * 3) * 2)  # Pulsing glow
        for i in range(glow_size, 0, -1):
            glow_alpha = 150 - i * 20
            if glow_alpha > 0:
                glow_rect = self.play_button_rect.inflate(i*2, i*2)
                pygame.draw.rect(self.screen, (65, 105, 225, glow_alpha), glow_rect, border_radius=30+i)
        
        # Main button
        pygame.draw.rect(self.screen, (65, 105, 225, 230), self.play_button_rect, border_radius=30)
        pygame.draw.rect(self.screen, (100, 149, 237), self.play_button_rect, 3, border_radius=30)
        
        # Button text with shadow
        play_shadow = self.font.render("PLAY", True, (30, 50, 100))
        play_text = self.font.render("PLAY", True, (255, 255, 255))
        
        play_shadow_rect = play_shadow.get_rect(center=(self.play_button_rect.center[0]+1, self.play_button_rect.center[1]+1))
        play_text_rect = play_text.get_rect(center=self.play_button_rect.center)
        
        self.screen.blit(play_shadow, play_shadow_rect)
        self.screen.blit(play_text, play_text_rect)
        
        # Draw difficulty selection - more intuitive controls with better alignment
        difficulty_box = pygame.Rect(0, 0, 300, 40)
        difficulty_box.center = (self.width//2, self.height//2 + 200)  # Fixed position below play button
        
        # Draw difficulty background with rounded corners
        pygame.draw.rect(self.screen, (0, 0, 0, 150), difficulty_box, border_radius=15)
        pygame.draw.rect(self.screen, (100, 149, 237, 150), difficulty_box, 1, border_radius=15)
        
        # Draw arrows with hover effect
        arrow_left_rect = pygame.Rect(difficulty_box.left + 10, difficulty_box.top, 40, 40)
        arrow_right_rect = pygame.Rect(difficulty_box.right - 50, difficulty_box.top, 40, 40)
        
        # Check if mouse is over arrows
        mouse_pos = pygame.mouse.get_pos()
        left_hover = arrow_left_rect.collidepoint(mouse_pos)
        right_hover = arrow_right_rect.collidepoint(mouse_pos)
        
        # Draw arrow with hover effect
        left_color = (255, 255, 255) if left_hover else (200, 200, 200)
        right_color = (255, 255, 255) if right_hover else (200, 200, 200)
        
        pygame.draw.polygon(self.screen, left_color, 
                          [(arrow_left_rect.centerx - 10, arrow_left_rect.centery), 
                            (arrow_left_rect.centerx + 5, arrow_left_rect.centery - 10),
                            (arrow_left_rect.centerx + 5, arrow_left_rect.centery + 10)])
        
        pygame.draw.polygon(self.screen, right_color, 
                          [(arrow_right_rect.centerx + 10, arrow_right_rect.centery), 
                            (arrow_right_rect.centerx - 5, arrow_right_rect.centery - 10),
                            (arrow_right_rect.centerx - 5, arrow_right_rect.centery + 10)])
        
        # Draw disk count with shadow
        difficulty_shadow = self.font.render(f"Disks: {self.num_disks}", True, (30, 30, 50))
        difficulty_text = self.font.render(f"Disks: {self.num_disks}", True, (255, 255, 255))
        
        shadow_rect = difficulty_shadow.get_rect(center=(difficulty_box.center[0]+1, difficulty_box.center[1]+1))
        text_rect = difficulty_text.get_rect(center=difficulty_box.center)
        
        self.screen.blit(difficulty_shadow, shadow_rect)
        self.screen.blit(difficulty_text, text_rect)
        
        # Draw camera feed in corner with an improved frame
        if hasattr(self, 'camera_feed_surface') and self.camera_feed_surface is not None:
            # Draw a stylish border for the camera feed
            border_rect = pygame.Rect(self.width - 230, 10, 220, 170)
            
            # Draw outer glow
            for i in range(3, 0, -1):
                glow_rect = border_rect.copy()
                glow_rect.inflate_ip(i*2, i*2)
                pygame.draw.rect(self.screen, (100, 100, 200, 50-i*10), glow_rect, border_radius=10)
            
            # Draw main border
            pygame.draw.rect(self.screen, (50, 50, 100, 180), border_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 149, 237), border_rect, 2, border_radius=8)
            
            # Display camera feed
            self.screen.blit(self.camera_feed_surface, (self.width - 220, 20))
            
            # Add camera preview label with improved look
            camera_bg = pygame.Surface((120, 25), pygame.SRCALPHA)
            camera_bg.fill((0, 0, 0, 150))
            camera_bg_rect = camera_bg.get_rect(center=(border_rect.centerx, border_rect.bottom + 15))
            pygame.draw.rect(camera_bg, (0, 0, 0, 150), camera_bg.get_rect(), border_radius=8)
            self.screen.blit(camera_bg, camera_bg_rect)
            
            camera_label = self.small_font.render("Camera Preview", True, (200, 200, 200))
            camera_label_rect = camera_label.get_rect(center=camera_bg_rect.center)
            self.screen.blit(camera_label, camera_label_rect)
        # Start with a transparent background
        self.screen.fill((0, 0, 0, 0))
        
        # Draw a semi-transparent overlay for better UI visibility
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((15, 15, 30, 200))  # Dark blue-black with alpha
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title_text = self.title_font.render("Tower of Hanoi", True, (255, 255, 255))
        subtitle_text = self.font.render("Gesture Controlled", True, (180, 180, 180))
        
        title_rect = title_text.get_rect(center=(self.width//2, self.height//4))
        subtitle_rect = subtitle_text.get_rect(center=(self.width//2, self.height//4 + 60))
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw instructions
        instructions = [
            "Control the game using your hand gestures:",
            "• Use pinch gesture (thumb and index finger) to pick up and place disks",
            "• Move your hand left/right to select different towers",
            "• Win by moving all disks to the rightmost tower",
            "",
            ""
        ]
        
        # Draw instruction box
        instruction_box = pygame.Surface((600, 200), pygame.SRCALPHA)
        instruction_box.fill((0, 0, 0, 150))
        self.screen.blit(instruction_box, (self.width//2 - 300, self.height//2 - 120))
        
        for i, line in enumerate(instructions):
            instruction_text = self.small_font.render(line, True, (200, 200, 200))
            self.screen.blit(instruction_text, (self.width//2 - 280, self.height//2 - 100 + i*30))
        
        # Draw play button - properly centered
        pygame.draw.rect(self.screen, (65, 105, 225, 230), self.play_button_rect, border_radius=30)
        pygame.draw.rect(self.screen, (100, 149, 237), self.play_button_rect, 2, border_radius=30)
        
        play_text = self.font.render("PLAY", True, (255, 255, 255))
        play_text_rect = play_text.get_rect(center=self.play_button_rect.center)
        self.screen.blit(play_text, play_text_rect)
        
        # Draw difficulty selection - more intuitive controls
        difficulty_box = pygame.Rect(0, 0, 300, 40)
        difficulty_box.center = (self.width//2, self.height//2 + 150)
        
        # Draw difficulty background
        pygame.draw.rect(self.screen, (0, 0, 0, 150), difficulty_box, border_radius=15)
        
        # Draw arrows
        arrow_left_rect = pygame.Rect(difficulty_box.left + 10, difficulty_box.top, 40, 40)
        arrow_right_rect = pygame.Rect(difficulty_box.right - 50, difficulty_box.top, 40, 40)
        
        pygame.draw.polygon(self.screen, (200, 200, 200), 
                           [(arrow_left_rect.centerx - 10, arrow_left_rect.centery), 
                            (arrow_left_rect.centerx + 5, arrow_left_rect.centery - 10),
                            (arrow_left_rect.centerx + 5, arrow_left_rect.centery + 10)])
        
        pygame.draw.polygon(self.screen, (200, 200, 200), 
                           [(arrow_right_rect.centerx + 10, arrow_right_rect.centery), 
                            (arrow_right_rect.centerx - 5, arrow_right_rect.centery - 10),
                            (arrow_right_rect.centerx - 5, arrow_right_rect.centery + 10)])
        
        # Draw disk count
        difficulty_text = self.font.render(f"Disks: {self.num_disks}", True, (255, 255, 255))
        difficulty_rect = difficulty_text.get_rect(center=difficulty_box.center)
        self.screen.blit(difficulty_text, difficulty_rect)
        
        # Draw camera feed in corner with a frame
        if hasattr(self, 'camera_feed_surface') and self.camera_feed_surface is not None:
            # Draw a border for the camera feed
            border_rect = pygame.Rect(self.width - 230, 10, 220, 170)
            pygame.draw.rect(self.screen, (100, 100, 100, 150), border_rect, border_radius=5)
            self.screen.blit(self.camera_feed_surface, (self.width - 220, 20))
            
            # Add camera preview label
            camera_label = self.small_font.render("Camera Preview", True, (200, 200, 200))
            camera_label_rect = camera_label.get_rect(midtop=(border_rect.centerx, border_rect.bottom + 5))
            self.screen.blit(camera_label, camera_label_rect)
    
    def draw_game(self):
        # Start with a transparent background
        self.screen.fill((0, 0, 0, 0))
        
        # Draw a semi-transparent overlay for the game area
        game_area = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        game_area.fill((15, 15, 30, 160))  # Very transparent background
        self.screen.blit(game_area, (0, 0))
        
        # Draw timer with a background
        timer_bg = pygame.Surface((150, 40), pygame.SRCALPHA)
        timer_bg.fill((0, 0, 0, 150))
        self.screen.blit(timer_bg, (20, 20))
        
        if self.timer_active:
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time
        
        timer_text = self.font.render(f"Time: {self.elapsed_time:.1f}s", True, (255, 255, 255))
        self.screen.blit(timer_text, (30, 30))
        
        # Draw move counter with a background
        moves_bg = pygame.Surface((150, 40), pygame.SRCALPHA)
        moves_bg.fill((0, 0, 0, 150))
        self.screen.blit(moves_bg, (20, 70))
        
        moves_text = self.font.render(f"Moves: {self.moves}", True, (255, 255, 255))
        self.screen.blit(moves_text, (30, 70))
        
        # Draw action message if active
        now = time.time()
        if self.action_message and now - self.action_message_time < self.action_message_duration:
            # Action message background
            msg_bg = pygame.Surface((400, 40), pygame.SRCALPHA)
            msg_bg.fill((0, 0, 0, 180))
            msg_rect = msg_bg.get_rect(center=(self.width//2, 50))
            self.screen.blit(msg_bg, msg_rect)
            
            # Action message
            msg_text = self.font.render(self.action_message, True, (255, 255, 255))
            msg_rect = msg_text.get_rect(center=(self.width//2, 50))
            self.screen.blit(msg_text, msg_rect)
        
        # Draw message
        if self.game_won:
            # Win message background
            win_bg = pygame.Surface((400, 120), pygame.SRCALPHA)
            win_bg.fill((0, 0, 0, 180))
            win_bg_rect = win_bg.get_rect(center=(self.width//2, 120))
            self.screen.blit(win_bg, win_bg_rect)
            
            win_text = self.title_font.render("You Win!", True, (255, 215, 0))
            win_rect = win_text.get_rect(center=(self.width//2, 100))
            self.screen.blit(win_text, win_rect)
            
            stats_text = self.font.render(f"Time: {self.elapsed_time:.1f}s | Moves: {self.moves}", True, (255, 255, 255))
            stats_rect = stats_text.get_rect(center=(self.width//2, 150))
            self.screen.blit(stats_text, stats_rect)
        else:
            # Instructions background
            instr_bg = pygame.Surface((500, 40), pygame.SRCALPHA)
            instr_bg.fill((0, 0, 0, 150))
            instr_rect = instr_bg.get_rect(center=(self.width//2, 100))
            self.screen.blit(instr_bg, instr_rect)
            
            # Instructions
            instructions = self.font.render("Pinch to pick up and place disks", True, (200, 200, 200))
            instr_rect = instructions.get_rect(center=(self.width//2, 100))
            self.screen.blit(instructions, instr_rect)
        
        # Draw the base
        pygame.draw.rect(self.screen, 
                        (139, 69, 19), 
                        (self.width//6, self.tower_y + self.tower_height, 
                        2*self.width//3, 20),
                        border_radius=5)
        
        # Draw towers
        for i, x in enumerate(self.tower_x_positions):
            pygame.draw.rect(self.screen, 
                          (180, 180, 180), 
                          (x - self.tower_width // 2, self.tower_y, 
                          self.tower_width, self.tower_height))
            
            # Draw tower number with background
            tower_label_bg = pygame.Surface((30, 30), pygame.SRCALPHA)
            tower_label_bg.fill((0, 0, 0, 150))
            tower_label_rect = tower_label_bg.get_rect(center=(x, self.tower_y + self.tower_height + 30))
            self.screen.blit(tower_label_bg, tower_label_rect)
            
            label = self.font.render(f"{i+1}", True, (255, 255, 255))
            label_rect = label.get_rect(center=(x, self.tower_y + self.tower_height + 30))
            self.screen.blit(label, label_rect)
            
            # Draw disks on this tower
            for j, disk in enumerate(self.towers[i]):
                disk_width = self.base_disk_width - (disk - 1) * 25
                color = self.disk_colors[(disk - 1) % len(self.disk_colors)]
                
                disk_y = self.tower_y + self.tower_height - (j + 1) * self.disk_height
                
                # Draw disk with rounded corners
                disk_rect = pygame.Rect(x - disk_width // 2, disk_y, disk_width, self.disk_height)
                pygame.draw.rect(self.screen, color, disk_rect, border_radius=10)
                pygame.draw.rect(self.screen, (255, 255, 255), disk_rect, 2, border_radius=10)
                
                # Add disk number
                disk_label = self.font.render(f"{disk}", True, (255, 255, 255))
                disk_label_rect = disk_label.get_rect(center=(x, disk_y + self.disk_height//2))
                self.screen.blit(disk_label, disk_label_rect)
        
        # Draw disk in hand if any
        if self.disk_in_hand is not None and self.hand_position is not None:
            disk_width = self.base_disk_width - (self.disk_in_hand - 1) * 25
            color = self.disk_colors[(self.disk_in_hand - 1) % len(self.disk_colors)]
            
            # Get hand position and convert to screen coordinates
            hand_x, hand_y = self.hand_position
            camera_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            camera_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            scaled_x = hand_x * (self.width / camera_width)
            scaled_y = hand_y * (self.height / camera_height)
            
            # Draw the disk at hand position with a glow effect
            # Draw glow first (larger, semi-transparent)
            glow_width = disk_width + 10
            glow_height = self.disk_height + 10
            glow_rect = pygame.Rect(scaled_x - glow_width // 2, scaled_y - glow_height // 2, 
                                   glow_width, glow_height)
            glow_color = (*color, 100)  # Add transparency
            glow_surface = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=15)
            self.screen.blit(glow_surface, glow_rect)
            
            # Draw the actual disk
            disk_rect = pygame.Rect(scaled_x - disk_width // 2, scaled_y - self.disk_height // 2, 
                                  disk_width, self.disk_height)
            pygame.draw.rect(self.screen, color, disk_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), disk_rect, 2, border_radius=10)
            
            # Add disk number
            disk_label = self.font.render(f"{self.disk_in_hand}", True, (255, 255, 255))
            disk_label_rect = disk_label.get_rect(center=(scaled_x, scaled_y))
            self.screen.blit(disk_label, disk_label_rect)
        
        # Draw pinch indicator
        if self.hand_position is not None:
            hand_x, hand_y = self.hand_position
            camera_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            camera_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            scaled_x = hand_x * (self.width / camera_width)
            scaled_y = hand_y * (self.height / camera_height)
            
            # Draw circle to indicate pinch state
            pygame.draw.circle(self.screen, self.pinch_indicator_color, (int(scaled_x), int(scaled_y)), 20, 3)
        
        # Draw camera feed in corner with a frame
        if hasattr(self, 'camera_feed_surface') and self.camera_feed_surface is not None:
            # Draw a border for the camera feed
            border_rect = pygame.Rect(self.width - 230, 10, 220, 170)
            pygame.draw.rect(self.screen, (100, 100, 100, 150), border_rect, border_radius=5)
            self.screen.blit(self.camera_feed_surface, (self.width - 220, 20))
        
    def show_camera_feed(self, frame):
        # Convert frame to RGB for pygame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Rotate as needed
        frame = np.rot90(frame)
        frame = pygame.surfarray.make_surface(frame)
        
        # Scale to fit in corner
        self.camera_feed_surface = pygame.transform.scale(frame, (200, 150))
        
    def run(self):
        running = True
        
        while running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_started:
                            self.game_started = False
                            self.show_play_screen = True
                        else:
                            running = False
                    elif event.key == pygame.K_r:  # Reset game
                        self.reset_game()
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        # Increase number of disks (max 5)
                        self.num_disks = min(5, self.num_disks + 1)
                        self.reset_game()
                    elif event.key == pygame.K_MINUS:
                        # Decrease number of disks (min 2)
                        self.num_disks = max(2, self.num_disks - 1)
                        self.reset_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.show_play_screen:
                        # Check play button click
                        if self.play_button_rect.collidepoint(event.pos):
                            self.show_play_screen = False
                            self.game_started = True
                            self.reset_game()
                            self.start_time = time.time()
                            self.timer_active = True
                            self.show_action_message("Game started! Use pinch gestures to move disks")
                        
                        # Check difficulty arrow clicks
                        difficulty_box = pygame.Rect(0, 0, 300, 40)
                        difficulty_box.center = (self.width//2, self.height//2 + 150)
                        
                        arrow_left_rect = pygame.Rect(difficulty_box.left + 10, difficulty_box.top, 40, 40)
                        arrow_right_rect = pygame.Rect(difficulty_box.right - 50, difficulty_box.top, 40, 40)
                        
                        if arrow_left_rect.collidepoint(event.pos):
                            # Decrease disks
                            self.num_disks = max(2, self.num_disks - 1)
                            self.reset_game()
                        elif arrow_right_rect.collidepoint(event.pos):
                            # Increase disks
                            self.num_disks = min(5, self.num_disks + 1)
                            self.reset_game()
                            
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize
                    self.width, self.height = event.size
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    # Update UI positions
                    self.tower_x_positions = [self.width//4, self.width//2, 3*self.width//4]
                    self.play_button_rect.center = (self.width//2, self.height//2 + 50)
            
            # Read camera frame
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            # Flip frame horizontally for more intuitive control
            # Flip frame horizontally for more intuitive control
            frame = cv2.flip(frame, 1)
            
            # Process hand landmarks
            hand_landmarks, processed_frame = self.detect_hands(frame)
            
            # Show camera feed
            self.show_camera_feed(processed_frame)
            
            # Handle game logic if game is started
            if self.game_started and not self.game_won:
                # Interpret hand gestures and update game state
                gesture_result = self.interpret_hand_gesture(hand_landmarks)
                
                # Check if game is won
                if self.check_win():
                    self.game_won = True
                    self.timer_active = False
                    self.show_action_message("Congratulations! You solved the puzzle!")
            
            # Draw game elements
            if self.show_play_screen:
                self.draw_play_screen()
            else:
                self.draw_game()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(30)
        
        # Clean up
        self.cap.release()
        pygame.quit()
        cv2.destroyAllWindows()
        sys.exit()

# Main function to run the game
def main():
    game = TowerOfHanoiGame(num_disks=3)
    game.run()

if __name__ == "__main__":
    main()

