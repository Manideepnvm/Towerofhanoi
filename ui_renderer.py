import pygame
import cv2
import numpy as np
import time
import math
from constants import *

class GameRenderer:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        pygame.display.set_caption("Tower of Hanoi - Gesture Control")
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        # Load fonts
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.font = pygame.font.SysFont('Arial', 28)
        self.small_font = pygame.font.SysFont('Arial', 20)
        
        self.camera_feed_surface = None
        self.play_button_rect = pygame.Rect(0, 0, 200, 60)
        # Position needs update on resize/draw
        
    def handle_resize(self, new_width, new_height):
        self.width = new_width
        self.height = new_height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
    def prepare_camera_surface(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        frame = pygame.surfarray.make_surface(frame)
        self.camera_feed_surface = pygame.transform.scale(frame, (200, 150))
        
    def draw_background_gradient(self):
        # Start with solid black
        self.screen.fill(COLOR_BLACK)
        
        # Draw gradient
        for i in range(self.height):
             # Subtle blue gradient
            gradient_color = (15, 15, max(10, min(50, 30 + i // 10)), 255)
            pygame.draw.line(self.screen, gradient_color, (0, i), (self.width, i))
            
    def draw_overlay(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        
    def draw_camera_preview(self):
         if self.camera_feed_surface:
            border_rect = pygame.Rect(self.width - 230, 10, 220, 170)
            
            # Glow
            for i in range(3, 0, -1):
                glow_rect = border_rect.copy()
                glow_rect.inflate_ip(i*2, i*2)
                pygame.draw.rect(self.screen, (100, 100, 200, 50-i*10), glow_rect, border_radius=10)
            
            # Border
            pygame.draw.rect(self.screen, (50, 50, 100, 180), border_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 149, 237), border_rect, 2, border_radius=8)
            
            self.screen.blit(self.camera_feed_surface, (self.width - 220, 20))
            
            # Label
            camera_bg = pygame.Surface((120, 25), pygame.SRCALPHA)
            camera_bg.fill((0, 0, 0, 150))
            camera_bg_rect = camera_bg.get_rect(center=(border_rect.centerx, border_rect.bottom + 15))
            pygame.draw.rect(camera_bg, (0, 0, 0, 150), camera_bg.get_rect(), border_radius=8)
            self.screen.blit(camera_bg, camera_bg_rect)
            
            label = self.small_font.render("Camera Preview", True, COLOR_TEXT_GRAY)
            label_rect = label.get_rect(center=camera_bg_rect.center)
            self.screen.blit(label, label_rect)
            
    def draw_play_screen(self, game_state):
        self.draw_background_gradient()
        self.draw_overlay()
        
        # Title
        title_shadow = self.title_font.render("Tower of Hanoi", True, COLOR_TITLE_SHADOW)
        title_text = self.title_font.render("Tower of Hanoi", True, COLOR_WHITE)
        subtitle_text = self.font.render("Gesture Controlled", True, (180, 180, 180))
        
        title_rect = title_text.get_rect(center=(self.width//2, self.height//4))
        shadow_rect = title_rect.copy()
        shadow_rect.x += 2; shadow_rect.y += 2
        
        subtitle_rect = subtitle_text.get_rect(center=(self.width//2, self.height//4 + 60))
        
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Instructions
        instruction_box = pygame.Surface((600, 220), pygame.SRCALPHA)
        instruction_box.fill((0, 0, 0, 150))
        instruction_rect = instruction_box.get_rect(center=(self.width//2, self.height//2 - 80))
        pygame.draw.rect(instruction_box, (65, 105, 225, 50), instruction_box.get_rect(), 2, border_radius=15)
        self.screen.blit(instruction_box, instruction_rect)
        
        instr_title = self.font.render("How to Play", True, (180, 180, 255))
        self.screen.blit(instr_title, instr_title.get_rect(center=(self.width//2, instruction_rect.top + 25)))
        
        instructions = [
            "Control with gestures:",
            "• Pinch (thumb+index) to pick up/place",
            "• Hold pinch and move hand",
            "• Win: Move all disks to right tower",
            "", ""
        ]
        
        for i, line in enumerate(instructions):
            text = self.small_font.render(line, True, COLOR_TEXT_GRAY)
            self.screen.blit(text, (instruction_rect.left + 30, instruction_rect.top + 55 + i*26))
            
        # Play Button
        self.play_button_rect.center = (self.width//2, self.height//2 + 120)
        
        # Glow
        glow_size = int(5 + math.sin(time.time() * 3) * 2)
        for i in range(glow_size, 0, -1):
            if 150 - i*20 > 0:
                 pygame.draw.rect(self.screen, (65, 105, 225, 150-i*20), 
                                 self.play_button_rect.inflate(i*2, i*2), border_radius=30+i)

        pygame.draw.rect(self.screen, (65, 105, 225, 230), self.play_button_rect, border_radius=30)
        pygame.draw.rect(self.screen, (100, 149, 237), self.play_button_rect, 3, border_radius=30)
        
        shadow = self.font.render("PLAY", True, COLOR_TITLE_SHADOW)
        text = self.font.render("PLAY", True, COLOR_WHITE)
        self.screen.blit(shadow, shadow.get_rect(center=(self.play_button_rect.centerx+1, self.play_button_rect.centery+1)))
        self.screen.blit(text, text.get_rect(center=self.play_button_rect.center))
        
        # Difficulty Controls
        diff_box = pygame.Rect(0, 0, 300, 40)
        diff_box.center = (self.width//2, self.height//2 + 200)
        
        pygame.draw.rect(self.screen, (0, 0, 0, 150), diff_box, border_radius=15)
        pygame.draw.rect(self.screen, (100, 149, 237, 150), diff_box, 1, border_radius=15)
        
        # Arrows (Logic handled here for drawing, input in main)
        arrow_left = pygame.Rect(diff_box.left + 10, diff_box.top, 40, 40)
        arrow_right = pygame.Rect(diff_box.right - 50, diff_box.top, 40, 40)
        
        mouse_pos = pygame.mouse.get_pos()
        left_col = COLOR_WHITE if arrow_left.collidepoint(mouse_pos) else COLOR_TEXT_GRAY
        right_col = COLOR_WHITE if arrow_right.collidepoint(mouse_pos) else COLOR_TEXT_GRAY
        
        pygame.draw.polygon(self.screen, left_col, 
                           [(arrow_left.centerx-10, arrow_left.centery),
                            (arrow_left.centerx+5, arrow_left.centery-10),
                            (arrow_left.centerx+5, arrow_left.centery+10)])
                            
        pygame.draw.polygon(self.screen, right_col, 
                           [(arrow_right.centerx+10, arrow_right.centery),
                            (arrow_right.centerx-5, arrow_right.centery-10),
                            (arrow_right.centerx-5, arrow_right.centery+10)])
                            
        diff_text = self.font.render(f"Disks: {game_state.num_disks}", True, COLOR_WHITE)
        self.screen.blit(diff_text, diff_text.get_rect(center=diff_box.center))
        
        self.draw_camera_preview()
        
    def draw_game_screen(self, game_state):
        self.screen.fill(COLOR_TRANSPARENT)
        
        # Game Area BG
        game_area = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        game_area.fill((15, 15, 30, 160))
        self.screen.blit(game_area, (0, 0))
        
        # HUD: Timer
        timer_bg = pygame.Surface((150, 40), pygame.SRCALPHA)
        timer_bg.fill((0, 0, 0, 150))
        self.screen.blit(timer_bg, (20, 20))
        
        time_text = self.font.render(f"Time: {game_state.elapsed_time:.1f}s", True, COLOR_WHITE)
        self.screen.blit(time_text, (30, 30))
        
        # HUD: Moves
        moves_bg = pygame.Surface((150, 40), pygame.SRCALPHA)
        moves_bg.fill((0, 0, 0, 150))
        self.screen.blit(moves_bg, (20, 70))
        
        moves_text = self.font.render(f"Moves: {game_state.moves}", True, COLOR_WHITE)
        self.screen.blit(moves_text, (30, 70))
        
        # Action Message
        now = time.time()
        if game_state.action_message and now - game_state.action_message_time < ACTION_MESSAGE_DURATION:
            msg_bg = pygame.Surface((500, 40), pygame.SRCALPHA)
            msg_bg.fill((0, 0, 0, 180))
            msg_rect = msg_bg.get_rect(center=(self.width//2, 50))
            self.screen.blit(msg_bg, msg_rect)
            
            msg_text = self.font.render(game_state.action_message, True, COLOR_WHITE)
            self.screen.blit(msg_text, msg_text.get_rect(center=msg_rect.center))
            
        # Win or Instructions
        if game_state.game_won:
            win_bg = pygame.Surface((400, 120), pygame.SRCALPHA)
            win_bg.fill((0, 0, 0, 180))
            win_rect = win_bg.get_rect(center=(self.width//2, 120))
            self.screen.blit(win_bg, win_rect)
            
            win_txt = self.title_font.render("You Win!", True, (255, 215, 0))
            self.screen.blit(win_txt, win_txt.get_rect(center=(self.width//2, 100)))
            
            stats = self.font.render(f"Time: {game_state.elapsed_time:.1f}s | Moves: {game_state.moves}", True, COLOR_WHITE)
            self.screen.blit(stats, stats.get_rect(center=(self.width//2, 150)))
        else:
             instr_bg = pygame.Surface((500, 40), pygame.SRCALPHA)
             instr_bg.fill((0, 0, 0, 150))
             instr_rect = instr_bg.get_rect(center=(self.width//2, 100))
             self.screen.blit(instr_bg, instr_rect)
             
             txt = self.font.render("Pinch to pick up and place disks", True, COLOR_TEXT_GRAY)
             self.screen.blit(txt, txt.get_rect(center=(self.width//2, 100)))
             
        # Towers
        tower_x_positions = [self.width//4, self.width//2, 3*self.width//4]
        
        # Base
        pygame.draw.rect(self.screen, (139, 69, 19), 
                        (self.width//6, TOWER_Y + TOWER_HEIGHT, 2*self.width//3, 20), 
                        border_radius=5)
                        
        for i, x in enumerate(tower_x_positions):
            # Tower pole
            pygame.draw.rect(self.screen, (180, 180, 180),
                            (x - TOWER_WIDTH//2, TOWER_Y, TOWER_WIDTH, TOWER_HEIGHT))
                            
            # Label
            lbl_bg = pygame.Surface((30, 30), pygame.SRCALPHA)
            lbl_bg.fill((0, 0, 0, 150))
            lbl_rect = lbl_bg.get_rect(center=(x, TOWER_Y + TOWER_HEIGHT + 30))
            self.screen.blit(lbl_bg, lbl_rect)
            
            lbl = self.font.render(f"{i+1}", True, COLOR_WHITE)
            self.screen.blit(lbl, lbl.get_rect(center=lbl_rect.center))
            
            # Disks
            for j, disk in enumerate(game_state.towers[i]):
                disk_w = BASE_DISK_WIDTH - (disk - 1) * 25
                color = DISK_COLORS[(disk - 1) % len(DISK_COLORS)]
                disk_y = TOWER_Y + TOWER_HEIGHT - (j + 1) * DISK_HEIGHT
                
                disk_rect = pygame.Rect(x - disk_w//2, disk_y, disk_w, DISK_HEIGHT)
                pygame.draw.rect(self.screen, color, disk_rect, border_radius=10)
                pygame.draw.rect(self.screen, COLOR_WHITE, disk_rect, 2, border_radius=10)
                
                d_lbl = self.font.render(f"{disk}", True, COLOR_WHITE)
                self.screen.blit(d_lbl, d_lbl.get_rect(center=disk_rect.center))
                
        # Disk in Hand
        if game_state.disk_in_hand is not None and game_state.hand_position is not None:
             disk = game_state.disk_in_hand
             disk_w = BASE_DISK_WIDTH - (disk - 1) * 25
             color = DISK_COLORS[(disk - 1) % len(DISK_COLORS)]
             
             hand_x, hand_y = game_state.hand_position
             # Scale if needed (assuming hand_position is already scaled or we scale here)
             # NOTE: In our game_state logic we stored raw average xy.
             # Wait, in app.py we mapped avg_x to screen coords.
             # Let's check game_state.update_interaction logic.
             # Ideally game_state should just store raw or normalized, and renderer scales.
             # But here we will assume game_state.hand_position is in screen coordinates (or we scale it).
             # Let's adjust logic in main.py to pass correct coordinates to update_interaction.
             
             # Assuming hand_position is (x, y) on screen:
             sx, sy = hand_x, hand_y # We will handle scaling in Main before passing
             
             # Glow
             glow_rect = pygame.Rect(sx - (disk_w+10)//2, sy - (DISK_HEIGHT+10)//2, disk_w+10, DISK_HEIGHT+10)
             s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
             pygame.draw.rect(s, (*color, 100), s.get_rect(), border_radius=15)
             self.screen.blit(s, glow_rect)
             
             # Disk
             d_rect = pygame.Rect(sx - disk_w//2, sy - DISK_HEIGHT//2, disk_w, DISK_HEIGHT)
             pygame.draw.rect(self.screen, color, d_rect, border_radius=10)
             pygame.draw.rect(self.screen, COLOR_WHITE, d_rect, 2, border_radius=10)
             
             l = self.font.render(f"{disk}", True, COLOR_WHITE)
             self.screen.blit(l, l.get_rect(center=d_rect.center))

        # Pinch Indicator
        if game_state.hand_position is not None:
            hx, hy = game_state.hand_position
            pygame.draw.circle(self.screen, game_state.pinch_indicator_color, (int(hx), int(hy)), 20, 3)
            
        self.draw_camera_preview()
        
    def render(self, game_state):
        if game_state.show_play_screen:
            self.draw_play_screen(game_state)
        else:
            self.draw_game_screen(game_state)
            
        pygame.display.flip()
