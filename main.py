import cv2
import sys
import pygame
import time
import numpy as np
from typing import Optional, List, Tuple
from constants import *
from hand_detector import HandDetector
from game_state import TowerOfHanoiGame
from ui_renderer import GameRenderer

class SoundManager:
    """
    Manages synthetic sound effects for the game.
    """
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        self.sounds = {}
        self.generate_sounds()
        
    def generate_wave(self, frequency: float, duration: float, volume: float = 0.5):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Sine wave with decay
        wave = np.sin(frequency * t * 2 * np.pi)
        
        # Apply decay envelope
        decay = np.linspace(1.0, 0.0, n_samples)
        wave = wave * decay * volume
        
        # Convert to 16-bit signed integers
        wave = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(wave)

    def generate_sounds(self):
        # Pickup: Non-intrusive high blip
        self.sounds['PICKUP'] = self.generate_wave(600, 0.1, 0.3)
        
        # Drop Valid: Satisfying lower thud/click
        self.sounds['DROP_VALID'] = self.generate_wave(400, 0.15, 0.4)
        
        # Drop Invalid: Low buzz
        # Complex wave for error? Just simple low tone for now
        self.sounds['DROP_INVALID'] = self.generate_wave(150, 0.3, 0.4)
        
        # Win: Ascending arpeggio
        # We can play multiple sounds or a pre-mixed buffer.
        # For simplicity, just a "Ding" high note
        self.sounds['WIN'] = self.generate_wave(880, 0.8, 0.5)
        
        # Reset
        self.sounds['RESET'] = self.generate_wave(300, 0.2, 0.3)

    def play(self, event_name: str):
        if event_name in self.sounds:
            self.sounds[event_name].play()

def main():
    # Initialize components
    # Start capturing
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        sys.exit()
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    renderer = GameRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
    hand_detector = HandDetector()
    game = TowerOfHanoiGame(num_disks=3)
    sound_manager = SoundManager()
    
    running = True
    
    while running:
        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.game_started:
                        game.game_started = False
                        game.show_play_screen = True
                    else:
                        running = False
                elif event.key == pygame.K_r:
                    game.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.show_play_screen:
                    if renderer.play_button_rect.collidepoint(event.pos):
                        game.show_play_screen = False
                        game.game_started = True
                        game.reset_game()
                        game.start_time = time.time()
                        game.timer_active = True
                        game.show_action_message("Game started! Pinch to move disks")
                        sound_manager.play('PICKUP') # Start sound
                        
                    # Difficulty
                    # Center of screen calc for hitboxes
                    diff_y = renderer.play_button_rect.bottom + 65 # Approx position from renderer logic
                    # To be robust, we should ask renderer. 
                    # But for now, simple rect logic relative to center
                    cx, cy = renderer.width//2, renderer.height//2
                    
                    # Difficulty arrows (Hardcoded matching renderer visual approx)
                    # Renderer draws arrows at diff_bg.left - 20 etc.
                    # Let's just use a wide area check around projected positions
                    
                    # Diff box center y is roughly play_button + 150?
                    # Let's rely on standard positions
                    diff_cy = cy + 205 # From old renderer logic, refined renderer aligns differently
                    
                    # Improved Hitbox logic:
                    # Let's define hitboxes based on window center
                    w, h = renderer.width, renderer.height
                    
                    # Left Arrow
                    left_arrow = pygame.Rect(w//2 - 150, h//2 + 190, 60, 60)
                    # Right Arrow
                    right_arrow = pygame.Rect(w//2 + 90, h//2 + 190, 60, 60)
                    
                    if left_arrow.collidepoint(event.pos):
                        game.num_disks = max(2, game.num_disks - 1)
                        game.reset_game()
                        sound_manager.play('PICKUP') # Beep
                    elif right_arrow.collidepoint(event.pos):
                         game.num_disks = min(5, game.num_disks + 1)
                         game.reset_game()
                         sound_manager.play('PICKUP') # Beep
                        
            elif event.type == pygame.VIDEORESIZE:
                renderer.handle_resize(event.w, event.h)

        # Camera
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)
        
        # Hand Detection
        hand_landmarks, processed_frame = hand_detector.process_frame(frame)
        
        # Prepare camera surface for rendering
        renderer.prepare_camera_surface(processed_frame)
        
        # Game Logic
        if game.game_started and not game.game_won:
            # We need to scale hand coords to screen
            scaled_landmarks = None
            if hand_landmarks:
                # Scale from Camera (640x480) to Window
                cam_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                cam_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                scale_x = renderer.width / cam_w
                scale_y = renderer.height / cam_h
                
                scaled_landmarks = []
                for x, y in hand_landmarks:
                    scaled_landmarks.append((x * scale_x, y * scale_y))
            
            game.update_interaction(scaled_landmarks, renderer.width)
            
            # Sound Trigger
            if game.last_event:
                if game.last_event == 'DROP_VALID':
                    sound_manager.play('DROP_VALID')
                elif game.last_event == 'DROP_INVALID':
                    sound_manager.play('DROP_INVALID')
                elif game.last_event == 'PICKUP':
                    sound_manager.play('PICKUP')
            
            if game.check_win():
                if not game.game_won: # Just happened
                     sound_manager.play('WIN')
                game.game_won = True
                game.timer_active = False
                game.show_action_message("Victory!")
                
        if game.timer_active:
             game.elapsed_time = time.time() - game.start_time
             
        # Render
        renderer.render(game)
        
        renderer.clock.tick(FPS)
        
    cap.release()
    pygame.quit()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
