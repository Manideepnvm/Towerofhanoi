import pygame
import cv2
import numpy as np
import time
import math
import random
from constants import *

class GameRenderer:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        pygame.display.set_caption("Tower of Hanoi - Professional Edition")
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        # Load high-quality fonts (Serif/Sans-Serif mix for elegance)
        self.title_font = pygame.font.SysFont('Georgia', 56, bold=True)
        self.font = pygame.font.SysFont('Arial', 28, bold=True) # Bold for readability
        self.small_font = pygame.font.SysFont('Arial', 18, bold=True)
        
        self.camera_feed_surface = None
        self.play_button_rect = pygame.Rect(0, 0, 240, 60)
        
        self.particles = []
        self.background_surface = None
        
    def handle_resize(self, new_width, new_height):
        self.width = new_width
        self.height = new_height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.background_surface = None
        
    def prepare_camera_surface(self, frame):
        # Frame is likely 640x480 from CV2
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Pygame expects (Width, Height, Channels), CV2 is (Height, Width, Channels)
        # We need to transpose/swap axes 0 and 1
        frame = np.swapaxes(frame, 0, 1)
        
        frame = pygame.surfarray.make_surface(frame)
        
        # Scale to a reasonable preview size (maintaining 4:3 aspect ratio)
        # 640x480 -> 320x240 (Half size is clearer than 240x180)
        self.camera_feed_surface = pygame.transform.smoothscale(frame, (320, 240))
        
    def create_background(self):
        if self.background_surface is None:
            self.background_surface = pygame.Surface((self.width, self.height))
            self.background_surface.fill(COLOR_BG_DARK)
            
            # Simple Metallic Gradient
            for y in range(self.height):
                # Interpolate between Off-White and Light-Steel-Blue
                ratio = y / self.height
                r = 255 - ratio * 20
                g = 255 - ratio * 15
                b = 255 - ratio * 10
                pygame.draw.line(self.background_surface, (r, g, b), (0, y), (self.width, y))

    def update_particles(self, dt):
        alive_particles = []
        for p in self.particles:
            p['x'] += p['vx'] * dt * 60
            p['y'] += p['vy'] * dt * 60
            p['life'] -= dt
            if p['life'] > 0:
                alive_particles.append(p)
        self.particles = alive_particles

    def spawn_particles(self, x, y, color):
        for _ in range(5):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.3, 0.6),
                'color': (255, 255, 255), # Glints are white
                'size': random.randint(1, 3)
            })

    def draw_particles(self):
        for p in self.particles:
            alpha = int(255 * (p['life'] / 0.6))
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], alpha), (p['size'], p['size']), p['size'])
            self.screen.blit(s, (int(p['x']-p['size']), int(p['y']-p['size'])))
            
    def draw_glass_panel(self, rect, border_radius=10):
        # Frosted "Crystal" effect
        # 1. White semi-transparent fill
        # 2. Blur (simulated by just lightening)
        # 3. Crisp gray border
        # 4. Drop shadow
        
        # Shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 30), shadow_surf.get_rect(), border_radius=border_radius)
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Glass Body
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((255, 255, 255, 180)) # Milky white
        pygame.draw.rect(s, (255, 255, 255, 100), s.get_rect(), border_radius=border_radius)
        self.screen.blit(s, rect)
        
        # Border (Crisp Steel)
        pygame.draw.rect(self.screen, (150, 160, 170), rect, 1, border_radius=border_radius)

    def draw_text(self, text, font, color, center_pos, shadow=True):
        if shadow:
            # Subtle drop shadow for "lifting" text off the page
            sh_txt = font.render(text, True, (180, 180, 190))
            sh_rect = sh_txt.get_rect(center=(center_pos[0]+1, center_pos[1]+1))
            self.screen.blit(sh_txt, sh_rect)
            
        txt = font.render(text, True, color)
        rect = txt.get_rect(center=center_pos)
        self.screen.blit(txt, rect)
        return rect
        
    def draw_camera_preview(self):
         if self.camera_feed_surface:
            # Dimensions: 320x240
            rect_w, rect_h = 320, 240
            padding = 10
            x = self.width - rect_w - 30
            y = 30
            
            panel_rect = pygame.Rect(x - padding, y - padding, rect_w + padding*2, rect_h + padding*2 + 30)
            self.draw_glass_panel(panel_rect, 8)
            
            # Feed
            self.screen.blit(self.camera_feed_surface, (x, y))
            
            # Border around feed
            pygame.draw.rect(self.screen, (50, 50, 50), (x, y, rect_w, rect_h), 2)
            
            # Label
            lbl = self.small_font.render("CAMERA FEED", True, COLOR_TEXT_DIM)
            self.screen.blit(lbl, (panel_rect.centerx - lbl.get_width()//2, y + rect_h + 8))

    def draw_metallic_disk(self, rect, base_color):
        # Simulate metal cylinder with vertical shine (horizontal gradient)
        
        # 1. Main body
        pygame.draw.rect(self.screen, base_color, rect, border_radius=DISK_ROUNDING)
        
        # 2. Highlights (Shine) to look like a cylinder
        # We need a surface to blit highlights
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Highlight stripe
        highlight_x = int(rect.width * 0.3)
        highlight_w = int(rect.width * 0.15)
        highlight_rect = pygame.Rect(highlight_x, 0, highlight_w, rect.height)
        pygame.draw.rect(s, (255, 255, 255, 100), highlight_rect)
        
        # Edge highlights (Top is lit, Bottom is shadow) - Bevel
        pygame.draw.rect(s, (255, 255, 255, 150), (0, 0, rect.width, 4), border_radius=DISK_ROUNDING) # Top edge
        pygame.draw.rect(s, (0, 0, 0, 50), (0, rect.height-4, rect.width, 4), border_radius=DISK_ROUNDING) # Bottom edge
        
        # Apply texture
        self.screen.blit(s, rect)
        
        # 3. Rim Outline (Darker version of base color)
        pygame.draw.rect(self.screen, (50, 50, 60), rect, 1, border_radius=DISK_ROUNDING)

    def draw_tower(self, x_pos, y_base, disks):
        # 1. Base (Marble slab)
        base_rect = pygame.Rect(x_pos - TOWER_BASE_WIDTH//2, y_base, TOWER_BASE_WIDTH, TOWER_BASE_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), base_rect, border_radius=2)
        # Top highlight
        pygame.draw.line(self.screen, (200, 200, 200), base_rect.topleft, base_rect.topright, 2)
        
        # 2. Rod (Polished Steel)
        rod_rect = pygame.Rect(x_pos - TOWER_WIDTH//2, y_base - TOWER_HEIGHT, TOWER_WIDTH, TOWER_HEIGHT)
        pygame.draw.rect(self.screen, (120, 120, 130), rod_rect, border_radius=TOWER_WIDTH//2)
        # Rod Shine
        pygame.draw.line(self.screen, (200, 200, 210), (rod_rect.centerx - 3, rod_rect.top), (rod_rect.centerx - 3, rod_rect.bottom), 3)
        
        # 4. Disks
        for j, disk in enumerate(disks):
            # Calculate pos
            disk_w = BASE_DISK_WIDTH - (disk - 1) * 35
            rect = pygame.Rect(0, 0, disk_w, DISK_HEIGHT)
            rect.center = (x_pos, y_base - (j + 1) * DISK_HEIGHT + DISK_HEIGHT//2)
            
            color = DISK_COLORS[(disk - 1) % len(DISK_COLORS)]
            self.draw_metallic_disk(rect, color)
            
            # Label (Etched)
            lbl = self.small_font.render(str(disk), True, (50, 50, 50))
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))

    def draw_game_screen(self, game_state):
        self.create_background()
        self.screen.blit(self.background_surface, (0,0))
        
        stage_ground_y = self.height // 2 + 150
        
        # HUD Panel
        hud_panel = pygame.Rect(30, 30, 220, 90)
        self.draw_glass_panel(hud_panel)
        
        time_text = f"TIME: {game_state.elapsed_time:.1f}s"
        self.draw_text(time_text, self.font, COLOR_WHITE, (hud_panel.centerx, hud_panel.top + 25), False)
        
        moves_text = f"MOVES: {game_state.moves}"
        self.draw_text(moves_text, self.font, COLOR_WHITE, (hud_panel.centerx, hud_panel.bottom - 25), False)
        
        # Message
        now = time.time()
        if game_state.action_message and now - game_state.action_message_time < ACTION_MESSAGE_DURATION:
            msg_rect = pygame.Rect(0, 0, 600, 60)
            msg_rect.center = (self.width//2, 60)
            self.draw_glass_panel(msg_rect)
            self.draw_text(game_state.action_message, self.font, (20, 20, 20), msg_rect.center, False)
            
        # Towers
        tower_x_positions = [self.width//4, self.width//2, 3*self.width//4]
        
        # Floor (Tabletop)
        pygame.draw.rect(self.screen, (220, 220, 225), (0, stage_ground_y + 10, self.width, self.height - stage_ground_y), 0)
        pygame.draw.line(self.screen, (180, 180, 185), (0, stage_ground_y + 10), (self.width, stage_ground_y + 10), 2)
        
        for i, x in enumerate(tower_x_positions):
            self.draw_tower(x, stage_ground_y, game_state.towers[i])
            
            # Label
            lbl_center = (x, stage_ground_y + 40)
            self.draw_text(f"POST {i+1}", self.font, COLOR_TEXT_DIM, lbl_center)
            
        # Held Disk
        if game_state.disk_in_hand is not None and game_state.hand_position is not None:
             hx, hy = game_state.hand_position
             
             disk_w = BASE_DISK_WIDTH - (game_state.disk_in_hand - 1) * 35
             rect = pygame.Rect(0, 0, disk_w, DISK_HEIGHT)
             rect.center = (hx, hy)
             
             # Shadow below disk (floating effect)
             shadow_rect = rect.copy()
             shadow_rect.y += 20
             s_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
             pygame.draw.ellipse(s_surf, (0, 0, 0, 50), s_surf.get_rect())
             self.screen.blit(s_surf, shadow_rect)
             
             color = DISK_COLORS[(game_state.disk_in_hand - 1) % len(DISK_COLORS)]
             self.draw_metallic_disk(rect, color)
             
             # Label
             lbl = self.small_font.render(str(game_state.disk_in_hand), True, (50, 50, 50))
             self.screen.blit(lbl, lbl.get_rect(center=rect.center))
             
        # Pinch
        if game_state.hand_position is not None:
             hx, hy = game_state.hand_position
             color = game_state.pinch_indicator_color
             # Elegant thin circle
             pygame.draw.circle(self.screen, color, (int(hx), int(hy)), 20, 2)
             # Center dot
             pygame.draw.circle(self.screen, color, (int(hx), int(hy)), 4)

        # Win
        if game_state.game_won:
             if random.random() < 0.2:
                 self.spawn_particles(random.randint(0, self.width), 0, (255, 215, 0))
                 
             win_panel = pygame.Rect(0, 0, 500, 250)
             win_panel.center = (self.width//2, self.height//2)
             self.draw_glass_panel(win_panel)
             
             self.draw_text("SUCCESS", self.title_font, (50, 150, 50), (self.width//2, self.height//2 - 50))
             self.draw_text("Sequence Completed", self.font, (50, 50, 50), (self.width//2, self.height//2 + 10))
             self.draw_text("Press 'R' to Restart", self.small_font, (100, 100, 100), (self.width//2, self.height//2 + 60))

        self.update_particles(1/60)
        self.draw_particles()
        self.draw_camera_preview()


    def draw_play_screen(self, game_state):
        self.create_background()
        self.screen.blit(self.background_surface, (0,0))
        
        # Center Panel
        panel_rect = pygame.Rect(0, 0, 700, 500)
        panel_rect.center = (self.width//2, self.height//2)
        self.draw_glass_panel(panel_rect, 15)
        
        # Title
        self.draw_text("TOWER OF HANOI", self.title_font, (20, 20, 40), (self.width//2, panel_rect.top + 70))
        self.draw_text("GESTURE CONTROL EDITION", self.font, (80, 80, 90), (self.width//2, panel_rect.top + 130))
        
        # Line
        pygame.draw.line(self.screen, (200, 200, 200), (panel_rect.left + 80, panel_rect.top + 160), (panel_rect.right - 80, panel_rect.top + 160), 1)
        
        # Instructions
        instr_y = panel_rect.top + 200
        lines = [
            "INSTRUCTIONS",
            "• Pinch thumb & index finger to grasp objects",
            "• Drag to move disks between posts",
            "• Objective: Move entire stack to Post 3"
        ]
        
        for i, line in enumerate(lines):
             fnt = self.font if i == 0 else self.small_font
             col = (20, 20, 20)
             self.draw_text(line, fnt, col, (self.width//2, instr_y + i*35), shadow=False)
        
        # Button
        self.play_button_rect.center = (self.width//2, panel_rect.bottom - 110)
        mouse_pos = pygame.mouse.get_pos()
        hover = self.play_button_rect.collidepoint(mouse_pos)
        
        btn_col = (50, 100, 200) if hover else (70, 70, 80)
        pygame.draw.rect(self.screen, btn_col, self.play_button_rect, border_radius=30)
        self.draw_text("START SIMULATION", self.font, (255, 255, 255), self.play_button_rect.center, shadow=False)
        
        # Difficulty
        diff_y = panel_rect.bottom - 45
        diff_bg = pygame.Rect(0, 0, 260, 40)
        diff_bg.center = (self.width//2, diff_y)
        self.draw_glass_panel(diff_bg, 20)
        
        self.draw_text(f"Disks: {game_state.num_disks}", self.small_font, (20, 20, 20), diff_bg.center, False)
        self.draw_text("<", self.font, (50, 50, 50), (diff_bg.left - 20, diff_y - 2), False)
        self.draw_text(">", self.font, (50, 50, 50), (diff_bg.right + 20, diff_y - 2), False)
        
        self.draw_camera_preview()
        
    def render(self, game_state):
        if game_state.show_play_screen:
            self.draw_play_screen(game_state)
        else:
            self.draw_game_screen(game_state)
            
        pygame.display.flip()
