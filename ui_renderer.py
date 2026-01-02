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
        pygame.display.set_caption("Tower of Hanoi - Cyberpunk Edition")
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        # Load custom fonts (fallback to system safe)
        self.title_font = pygame.font.SysFont('Arial', 56, bold=True)
        self.font = pygame.font.SysFont('Arial', 32)
        self.small_font = pygame.font.SysFont('Verdana', 18)
        
        self.camera_feed_surface = None
        self.play_button_rect = pygame.Rect(0, 0, 240, 70)
        
        # Particle System
        # List of {'x', 'y', 'vx', 'vy', 'life', 'color', 'size'}
        self.particles = []
        
        # Cached Background
        self.background_surface = None
        
    def handle_resize(self, new_width, new_height):
        self.width = new_width
        self.height = new_height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.background_surface = None # Recreate BG on resize
        
    def prepare_camera_surface(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        frame = cv2.resize(frame, (240, 180)) # Higher res preview
        
        # Apply a cool color filter to camera (Matrix style)
        # frame[:, :, 0] = 0 # Remove Red
        # frame[:, :, 2] = list(np.clip(frame[:, :, 2] * 1.2, 0, 255)) # Boost Blue
        
        frame = pygame.surfarray.make_surface(frame)
        self.camera_feed_surface = frame
        
    def create_background(self):
        if self.background_surface is None:
            self.background_surface = pygame.Surface((self.width, self.height))
            
            # 1. Radial Gradient (approximate with circles)
            cx, cy = self.width // 2, self.height // 2
            max_dist = math.sqrt(cx**2 + cy**2)
            
            # Draw darker circles from outside in? No, fill dark, draw light center
            self.background_surface.fill(COLOR_BG_DARK)
            
            # Draw a subtle glow in center
            glow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            for r in range(int(max_dist), 0, -20):
                alpha = int(20 * (1 - r/max_dist))
                if alpha > 0:
                    pygame.draw.circle(glow_surf, (*COLOR_BG_LIGHT, alpha), (cx, cy), r)
            self.background_surface.blit(glow_surf, (0,0))
            
            # 2. Grid lines (Perspective or flat? Flat is safer for performace)
            grid_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            grid_spacing = 40
            for x in range(0, self.width, grid_spacing):
                pygame.draw.line(grid_surf, COLOR_GRID, (x, 0), (x, self.height), 1)
            for y in range(0, self.height, grid_spacing):
                pygame.draw.line(grid_surf, COLOR_GRID, (0, y), (self.width, y), 1)
            self.background_surface.blit(grid_surf, (0,0))

    def update_particles(self, dt):
        # Update existing
        alive_particles = []
        for p in self.particles:
            p['x'] += p['vx'] * dt * 60
            p['y'] += p['vy'] * dt * 60
            p['life'] -= dt
            if p['life'] > 0:
                alive_particles.append(p)
        self.particles = alive_particles

    def spawn_particles(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.5, 1.0),
                'color': color,
                'size': random.randint(2, 5)
            })

    def draw_particles(self):
        for p in self.particles:
            alpha = int(255 * (p['life'] / PARTICLE_LIFETIME))
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], alpha), (p['size'], p['size']), p['size'])
            self.screen.blit(s, (int(p['x']-p['size']), int(p['y']-p['size'])))
            
    def draw_glass_panel(self, rect, border_radius=15):
        # Glassmorphism effect:
        # 1. Dark semi-transparent fill
        # 2. Bright subtle border
        
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((20, 20, 30, 200)) # Slightly darker and more opaque for clarity
        pygame.draw.rect(s, (100, 150, 255, 30), s.get_rect(), border_radius=border_radius) # Inner slight wash
        
        self.screen.blit(s, rect)
        
        # Outer Border
        pygame.draw.rect(self.screen, (100, 200, 255, 80), rect, 1, border_radius=border_radius)

    def draw_neon_text(self, text, font, color, center_pos, glow_color=(0, 200, 255)):
        # Main text
        txt = font.render(text, True, color)
        rect = txt.get_rect(center=center_pos)
        
        # Glow (Reduced count for performance, increased opacity check)
        glow = font.render(text, True, (*glow_color, 40))
        self.screen.blit(glow, (rect.x - 2, rect.y - 2))
        self.screen.blit(glow, (rect.x + 2, rect.y + 2))
            
        self.screen.blit(txt, rect)
        return rect
        
    def draw_camera_preview(self):
         if self.camera_feed_surface:
            rect_w, rect_h = 240, 180
            padding = 10
            x = self.width - rect_w - 30
            y = 30
            
            panel_rect = pygame.Rect(x - padding, y - padding, rect_w + padding*2, rect_h + padding*2 + 30)
            self.draw_glass_panel(panel_rect, 10)
            
            # Display feed
            self.screen.blit(self.camera_feed_surface, (x, y))
            
            # Scanlines effect
            scanlines = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
            for i in range(0, rect_h, 4):
                pygame.draw.line(scanlines, (0, 0, 0, 50), (0, i), (rect_w, i))
            self.screen.blit(scanlines, (x, y))
            
            # Label
            lbl = self.small_font.render("VISUAL SENSOR", True, COLOR_TEXT_DIM)
            self.screen.blit(lbl, (panel_rect.centerx - lbl.get_width()//2, y + rect_h + 8))

    def draw_tower(self, x_pos, y_base, disks):
        # 1. Base (Glowing Platform)
        base_rect = pygame.Rect(x_pos - TOWER_BASE_WIDTH//2, y_base + 2, TOWER_BASE_WIDTH, TOWER_BASE_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_BASE_GLOW, base_rect, border_radius=3)
        
        # 2. Rod (Neon Line)
        rod_rect = pygame.Rect(x_pos - TOWER_WIDTH//2, y_base - TOWER_HEIGHT, TOWER_WIDTH, TOWER_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_TOWER_CORE, rod_rect, border_radius=TOWER_WIDTH//2)
        
        # Glow for rod
        s = pygame.Surface((TOWER_WIDTH+10, TOWER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s, (*COLOR_TOWER_GLOW, 100), s.get_rect(), border_radius=TOWER_WIDTH//2)
        self.screen.blit(s, (rod_rect.x - 5, rod_rect.y))
        
        # 4. Disks
        for j, disk in enumerate(disks):
            self.draw_disk(x_pos, y_base - (j + 1) * DISK_HEIGHT + DISK_HEIGHT//2, disk)

    def draw_disk(self, cx, cy, disk_val, alpha=255):
        disk_w = BASE_DISK_WIDTH - (disk_val - 1) * 35
        rect = pygame.Rect(0, 0, disk_w, DISK_HEIGHT)
        rect.center = (cx, cy) # CY is center of disk now
        
        color = DISK_COLORS[(disk_val - 1) % len(DISK_COLORS)]
        
        # Main Body (Gradient-ish)
        pygame.draw.rect(self.screen, color, rect, border_radius=DISK_ROUNDING)
        
        # Shine (Top half lighter)
        shine_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height//2)
        s = pygame.Surface((rect.width, rect.height//2), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 60), s.get_rect(), border_radius=DISK_ROUNDING) # Top Gloss
        self.screen.blit(s, shine_rect)
        
        # Border (Metallic)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=DISK_ROUNDING)
        
        # Label
        lbl = self.small_font.render(str(disk_val), True, (20, 20, 20)) # Dark text on bright neon
        self.screen.blit(lbl, lbl.get_rect(center=rect.center))

    def draw_game_screen(self, game_state):
        # Background
        self.create_background()
        self.screen.blit(self.background_surface, (0,0))
        
        # Calculate Vertical Center for Game Stage
        stage_ground_y = self.height // 2 + 150 # Move towers down a bit
        
        # HUD Panel (Top Left) - Improved alignment
        hud_panel = pygame.Rect(30, 30, 220, 90)
        self.draw_glass_panel(hud_panel)
        
        time_text = f"TIME: {game_state.elapsed_time:.1f}"
        self.draw_neon_text(time_text, self.font, COLOR_TOWER_CORE, (hud_panel.centerx, hud_panel.top + 25))
        
        moves_text = f"MOVES: {game_state.moves}"
        self.draw_neon_text(moves_text, self.font, COLOR_TOWER_CORE, (hud_panel.centerx, hud_panel.bottom - 25))
        
        # Action Message (Top Center)
        now = time.time()
        if game_state.action_message and now - game_state.action_message_time < ACTION_MESSAGE_DURATION:
            msg_rect = pygame.Rect(0, 0, 600, 60)
            msg_rect.center = (self.width//2, 60)
            self.draw_glass_panel(msg_rect, 10)
            self.draw_neon_text(game_state.action_message, self.font, COLOR_WHITE, msg_rect.center)
            
        # Towers
        tower_x_positions = [self.width//4, self.width//2, 3*self.width//4]
        
        # Base platform connecting towers
        base_connector = pygame.Rect(self.width//6, stage_ground_y + 7, 2*self.width//3, 4)
        pygame.draw.rect(self.screen, COLOR_BG_LIGHT, base_connector)
        
        for i, x in enumerate(tower_x_positions):
            # Base/Rod
            self.draw_tower(x, stage_ground_y, game_state.towers[i])
            
            # Correct Label
            lbl_center = (x, stage_ground_y + 40)
            self.draw_neon_text(f"NODE {i+1}", self.font, COLOR_TEXT_DIM, lbl_center)
            
        # Held Disk
        if game_state.disk_in_hand is not None and game_state.hand_position is not None:
             hx, hy = game_state.hand_position
             
             # Draw Ghost target??
             # For now, just the disk
             self.draw_disk(hx, hy, game_state.disk_in_hand)
             
             # Glow under finger
             pygame.draw.circle(self.screen, (255, 255, 255), (int(hx), int(hy)), 5)
             
        # Pinch Indicator
        if game_state.hand_position is not None:
             hx, hy = game_state.hand_position
             color = game_state.pinch_indicator_color
             
             # Reticle style
             size = 30
             s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
             
             # Dynamic rotation? No time, just static cool reticle
             pygame.draw.arc(s, color, (0, 0, size*2, size*2), 0, math.pi*2, 3)
             pygame.draw.line(s, color, (size, 0), (size, size*0.6), 2)
             pygame.draw.line(s, color, (size, size*2), (size, size*1.4), 2)
             pygame.draw.line(s, color, (0, size), (size*0.6, size), 2)
             pygame.draw.line(s, color, (size*2, size), (size*1.4, size), 2)
             
             self.screen.blit(s, (hx-size, hy-size))

        # Win Screen
        if game_state.game_won:
             # Spawn confetti check
             if random.random() < 0.3:
                 self.spawn_particles(random.randint(0, self.width), 0, random.choice(DISK_COLORS))
                 
             win_panel = pygame.Rect(0, 0, 500, 250)
             win_panel.center = (self.width//2, self.height//2)
             self.draw_glass_panel(win_panel, 20)
             
             self.draw_neon_text("SYSTEM HACKED", self.title_font, (0, 255, 0), (self.width//2, self.height//2 - 50))
             self.draw_neon_text("PUZZLE SOLVED", self.font, COLOR_WHITE, (self.width//2, self.height//2 + 10))
             
             # Instructions to reset
             self.draw_neon_text("[ PRESS 'R' TO REBOOT ]", self.small_font, COLOR_TEXT_DIM, (self.width//2, self.height//2 + 60))

        self.update_particles(1/60)
        self.draw_particles()
        self.draw_camera_preview()


    def draw_play_screen(self, game_state):
        self.create_background()
        self.screen.blit(self.background_surface, (0,0))
        
        # Particles
        if random.random() < 0.1:
             self.spawn_particles(random.randint(0, self.width), self.height, random.choice(DISK_COLORS))
        self.update_particles(1/60)
        self.draw_particles()
        
        # Center Panel
        panel_w, panel_h = 700, 500
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (self.width//2, self.height//2)
        self.draw_glass_panel(panel_rect, 20)
        
        # Title
        self.draw_neon_text("NEON HANOI", self.title_font, (0, 255, 255), (self.width//2, panel_rect.top + 70))
        self.draw_neon_text("GESTURE INTERFACE", self.font, (255, 0, 255), (self.width//2, panel_rect.top + 130))
        
        # Horizontal Divider
        pygame.draw.line(self.screen, (100, 200, 255), (panel_rect.left + 50, panel_rect.top + 160), (panel_rect.right - 50, panel_rect.top + 160), 2)
        
        # Instructions
        instr_y = panel_rect.top + 200
        lines = [
            "INITIATE SEQUENCE:",
            "  [PINCH] thumb & index to manipulate data cores",
            "  [DRAG]  to relocate cores between nodes",
            "  [GOAL]  Transfer stack to Node 3",
        ]
        
        for i, line in enumerate(lines):
             col = (200, 255, 200) if i == 0 else COLOR_WHITE
             fnt = self.small_font
             self.draw_neon_text(line, fnt, col, (self.width//2, instr_y + i*35))
        
        # Play Button
        self.play_button_rect.center = (self.width//2, panel_rect.bottom - 110)
        
        # Hover check
        mouse_pos = pygame.mouse.get_pos()
        hover = self.play_button_rect.collidepoint(mouse_pos)
        
        btn_col = (0, 255, 150) if hover else (0, 100, 200)
        if hover:
            pulse = (math.sin(time.time()*5)+1)/2 * 5
            glow_rect = self.play_button_rect.inflate(pulse*2, pulse*2)
            s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (*btn_col, 80), s.get_rect(), border_radius=20)
            self.screen.blit(s, glow_rect)
        
        pygame.draw.rect(self.screen, btn_col, self.play_button_rect, border_radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), self.play_button_rect, 2, border_radius=20)
        self.draw_neon_text("INITIALIZE", self.title_font, (0, 20, 20), self.play_button_rect.center)
        
        # Difficulty Controls
        diff_y = panel_rect.bottom - 45
        # Arrows drawn as triangles
        arrow_size = 15
        diff_bg = pygame.Rect(0, 0, 260, 40)
        diff_bg.center = (self.width//2, diff_y)
        self.draw_glass_panel(diff_bg, 10)
        
        self.draw_neon_text(f"DIFFICULTY: {game_state.num_disks}", self.small_font, COLOR_TEXT_GLOW, diff_bg.center)
        
        # Draw Arrow Hints
        self.draw_neon_text("<", self.font, COLOR_WHITE, (diff_bg.left - 20, diff_y - 2))
        self.draw_neon_text(">", self.font, COLOR_WHITE, (diff_bg.right + 20, diff_y - 2))
        
        self.draw_camera_preview()
        
    def render(self, game_state):
        if game_state.show_play_screen:
            self.draw_play_screen(game_state)
        else:
            self.draw_game_screen(game_state)
            
        pygame.display.flip()
