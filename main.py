import cv2
import sys
import pygame
import time
from constants import *
from hand_detector import HandDetector
from game_state import TowerOfHanoiGame
from ui_renderer import GameRenderer

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
                    # Scaling mouse pos not needed if window resizes logic handled by renderer
                    # But renderer keeps checking internal rects. 
                    # Renderer needs to know we clicked locally.
                    
                    if renderer.play_button_rect.collidepoint(event.pos):
                        game.show_play_screen = False
                        game.game_started = True
                        game.reset_game()
                        game.start_time = time.time()
                        game.timer_active = True
                        game.show_action_message("Game started! Pinch to move disks")
                        
                    # Difficulty
                    diff_box = pygame.Rect(0, 0, 300, 40)
                    diff_box.center = (renderer.width//2, renderer.height//2 + 200)
                    arrow_left = pygame.Rect(diff_box.left + 10, diff_box.top, 40, 40)
                    arrow_right = pygame.Rect(diff_box.right - 50, diff_box.top, 40, 40)
                    
                    if arrow_left.collidepoint(event.pos):
                        game.num_disks = max(2, game.num_disks - 1)
                        game.reset_game()
                    elif arrow_right.collidepoint(event.pos):
                        game.num_disks = min(5, game.num_disks + 1)
                        game.reset_game()
                        
            elif event.type == pygame.VIDEORESIZE:
                renderer.handle_resize(event.w, event.h)
                # Note: Game logic (tower positions) uses constants, which might be an issue for resizing 
                # if we want logic to scale. 
                # For now keeping logic to fixed constants or we need to update GameState with width/height too.
                # However, original code updated tower_positions on resize.
                # Let's simple ignore dynamic logic scaling for now or update it?
                # The constants are fixed. The Original code updated `self.tower_x_positions`.
                # Ideally GameState should handle this. 
                # For this refactor I will keep it simple as constants are used.
                pass

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
            # HandDetector returns pixels in 640x480 (Camera res)
            # GameState expects coordinates to map to SCREEN_WIDTH
            
            scaled_landmarks = None
            if hand_landmarks:
                # Scale
                cam_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                cam_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                # We need to scale to current renderer width/height
                scale_x = renderer.width / cam_w
                scale_y = renderer.height / cam_h
                
                scaled_landmarks = []
                for x, y in hand_landmarks:
                    scaled_landmarks.append((x * scale_x, y * scale_y))
            
            # Pass (index, thumb, wrist)
            # Note: HandDetector returns exactly that list
            
            game.update_interaction(scaled_landmarks, renderer.width)
            
            if game.check_win():
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
