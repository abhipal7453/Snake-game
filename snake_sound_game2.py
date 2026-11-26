import pygame
import random
import time
import math
import array
import json
import os
from collections import deque

# Pygame initialize
pygame.init()

# Mixer ko specific settings ke sath initialize karna taaki humari Math waves isse match karein
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# ==========================================
# MEMORY / DATA STORAGE SYSTEM (JSON)
# ==========================================
DATA_FILE = "snake_data.json"

def load_data():
    # Agar file pehle se maujood hai toh data load karo
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Agar file nahi hai ya kharab hai, toh default scores set karo
    return {"SLOW": 0, "MEDIUM": 0, "FAST": 0}

def save_data(scores):
    # High score ko file mein save karna
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(scores, f)
    except:
        pass

# Game shuru hote hi data load karna
high_scores = load_data()

# ==========================================
# MATH-BASED SOUND GENERATOR FUNCTIONS
# ==========================================
def create_click_sound():
    sample_rate = 44100
    duration = 0.05 
    num_samples = int(sample_rate * duration)
    buf = array.array('h') 
    for i in range(num_samples):
        t = float(i) / sample_rate
        val = math.sin(2 * math.pi * 800 * t) 
        decay = 1.0 - (i / num_samples) 
        sample = int(0.3 * 32767 * val * decay)
        buf.append(sample)
        buf.append(sample)
    return pygame.mixer.Sound(buffer=buf)

def create_eat_sound():
    sample_rate = 44100
    duration = 0.15
    num_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(num_samples):
        t = float(i) / sample_rate
        freq = 400 + (800 * (i / num_samples))
        val = math.sin(2 * math.pi * freq * t)
        decay = 1.0 - (i / num_samples)
        sample = int(0.5 * 32767 * val * decay)
        buf.append(sample)
        buf.append(sample)
    return pygame.mixer.Sound(buffer=buf)

def create_currency_sound():
    sample_rate = 44100
    duration = 1.2 
    num_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(num_samples):
        t = float(i) / sample_rate
        val1 = math.sin(2 * math.pi * 1800 * t)
        val2 = math.sin(2 * math.pi * 2400 * t)
        val = (val1 + val2) / 2.0
        tremolo = 0.5 + 0.5 * math.sin(2 * math.pi * 15 * t)
        decay = math.exp(-4 * t) 
        sample = int(0.5 * 32767 * val * tremolo * decay)
        buf.append(sample)
        buf.append(sample)
    return pygame.mixer.Sound(buffer=buf)

# Ek Laybaddh (Melodic) aur komal Awaaz! (1.2 Seconds)
def create_startup_sound():
    sample_rate = 44100
    duration = 1.2 
    num_samples = int(sample_rate * duration)
    buf = array.array('h')
    
    # 4 soft musical notes (Sa, Re, Ga, Pa) ki frequency
    freqs = [261.63, 293.66, 329.63, 392.00] 
    
    for i in range(num_samples):
        t = float(i) / sample_rate
        
        # Determine karna ki abhi kaunsa note bajna chahiye
        note_idx = int(t / 0.3)
        if note_idx > 3: note_idx = 3
        freq = freqs[note_idx]
        local_t = t - (note_idx * 0.3)
        
        # Soft sine wave
        val = math.sin(2 * math.pi * freq * t)
        
        # Exponential decay (har aawaz dheere se band ho ek jhatke mein nahi)
        decay = math.exp(-6 * local_t) 
        
        # Volume ekdum kam rakhi hai (0.15) taaki mithi lage
        sample = int(0.15 * 32767 * val * decay)
        buf.append(sample)
        buf.append(sample)
    return pygame.mixer.Sound(buffer=buf)

# Sounds Generate aur Store karna
eat_sound = create_eat_sound()
click_sound = create_click_sound()
game_over_sound = create_currency_sound()
startup_sound = create_startup_sound()

def play_sound(sound_obj):
    if sound_obj:
        sound_obj.play()

# ==========================================
# GAME SETUP & UI VARIABLES
# ==========================================
infoObject = pygame.display.Info()
DEVICE_WIDTH = infoObject.current_w
DEVICE_HEIGHT = infoObject.current_h

screen = pygame.display.set_mode((DEVICE_WIDTH, DEVICE_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Modern 3D Snake Game")

COLS = 20  
BLOCK_SIZE = DEVICE_WIDTH // COLS
ROWS = DEVICE_HEIGHT // BLOCK_SIZE
UI_ROWS = 5  

BG_COLOR = (15, 15, 20)
TEXT_SAFFRON = (255, 153, 51)
TEXT_WHITE = (255, 255, 255)
TEXT_GREEN = (50, 255, 50)
TEXT_RED = (255, 50, 50)
SNAKE_COLOR = (0, 180, 0)       
SNAKE_HEAD_COLOR = (0, 255, 0)  
FOOD_COLOR = (255, 50, 50)      
BUTTON_COLOR = (0, 180, 180)
BUTTON_HOVER = (0, 130, 130)

FONT_TINY = pygame.font.Font(None, int(BLOCK_SIZE * 0.9))
FONT_SMALL = pygame.font.Font(None, int(BLOCK_SIZE * 1.2))
FONT_MED = pygame.font.Font(None, int(BLOCK_SIZE * 1.8))
FONT_LARGE = pygame.font.Font(None, int(BLOCK_SIZE * 3.0))

SCORE_INCREMENT = 10
SPEEDS = {"SLOW": 4, "MEDIUM": 8, "FAST": 12}

def draw_text(surface, text, font, color, x, y, align="center"):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if align == "center":
        text_rect.center = (x, y)
    elif align == "left":
        text_rect.topleft = (x, y)
    elif align == "right":
        text_rect.topright = (x, y)
    surface.blit(text_obj, text_rect)

# ==========================================
# CLASSES (Button, Particles, Game Logic)
# ==========================================
class Button:
    def __init__(self, x, y, w, h, text, color, hover_color, font_size=FONT_SMALL):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = font_size

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        
        glow_rect = self.rect.inflate(8, 8)
        glow_surface = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (0, 255, 255, 40), glow_surface.get_rect(), border_radius=10)
        surface.blit(glow_surface, glow_rect.topleft)
        
        pygame.draw.rect(surface, current_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, TEXT_WHITE, self.rect, 2, border_radius=8)
        draw_text(surface, self.text, self.font, TEXT_WHITE, self.rect.centerx, self.rect.centery)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                play_sound(click_sound) 
                return True
        return False

class BubbleEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.life = 1.0

    def update(self):
        self.radius += 4 
        self.life -= 0.05 

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * self.life)
            thickness = max(1, int(4 * self.life))
            b_surf = pygame.Surface((int(self.radius*2), int(self.radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(b_surf, (150, 200, 255, alpha), (int(self.radius), int(self.radius)), int(self.radius), thickness)
            surface.blit(b_surf, (int(self.x - self.radius), int(self.y - self.radius)))

class Particle:
    def __init__(self, x, y, color, explode=False):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        
        if explode:
            speed = random.uniform(10, 25)
            self.decay = random.uniform(0.01, 0.02)
        else:
            speed = random.uniform(1, 5)
            self.decay = random.uniform(0.02, 0.05)
            
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * self.life)
            radius = max(1, int(4 * self.life))
            p_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surface, (*self.color, alpha), (radius, radius), radius)
            surface.blit(p_surface, (int(self.x - radius), int(self.y - radius)))

class SnakeGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.state = "SPLASH" 
        self.next_state = "HOME"
        self.splash_start_time = pygame.time.get_ticks() 
        self.transition_start_time = 0
        
        play_sound(startup_sound)
        
        self.score = 0
        self.mode = "MANUAL"
        self.speed_level = "MEDIUM"
        self.speed = SPEEDS[self.speed_level]
        self.particles = []
        self.bubbles = []
        self.start_touch_pos = None
        self.swipe_threshold = 20
        self.last_move_time = 0

        self.stars = []
        for _ in range(120):
            x = random.randint(0, DEVICE_WIDTH)
            y = random.randint(0, DEVICE_HEIGHT)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4) 
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1, 3)
            self.stars.append([x, y, vx, vy, size])
            
        self.reset_game()

    # Naya System: Page badalne se pehle chakke wali screen lagana
    def change_state(self, new_state):
        self.next_state = new_state
        self.state = "TRANSITION"
        self.transition_start_time = pygame.time.get_ticks()

    def reset_game(self):
        start_x = COLS // 2
        start_y = ROWS // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.particles.clear()
        self.bubbles.clear()
        self.spawn_food()

    def spawn_food(self):
        while True:
            fx = random.randint(1, COLS - 2)
            fy = random.randint(UI_ROWS + 1, ROWS - 2)
            if (fx, fy) not in self.snake:
                self.food = (fx, fy)
                break

    def get_bfs_path(self):
        start = self.snake[0]
        target = self.food
        queue = deque([[start]])
        visited = set([start])
        body_set = set(self.snake[:-1]) 
        
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        while queue:
            path = queue.popleft()
            x, y = path[-1]
            
            if (x, y) == target:
                return path
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < COLS and UI_ROWS <= ny < ROWS:
                    if (nx, ny) not in visited and (nx, ny) not in body_set:
                        queue.append(path + [(nx, ny)])
                        visited.add((nx, ny))
        return None

    def auto_play_move(self):
        path = self.get_bfs_path()
        if path and len(path) > 1:
            next_pos = path[1]
            dx = next_pos[0] - self.snake[0][0]
            dy = next_pos[1] - self.snake[0][1]
            self.next_direction = (dx, dy)
        else:
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx = self.snake[0][0] + dx
                ny = self.snake[0][1] + dy
                if 0 <= nx < COLS and UI_ROWS <= ny < ROWS and (nx, ny) not in self.snake:
                    self.next_direction = (dx, dy)
                    break

    def update_snake(self):
        if self.mode == "AUTO":
            self.auto_play_move()
            
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        
        if not (0 <= new_head[0] < COLS and UI_ROWS <= new_head[1] < ROWS):
            self.trigger_game_over()
            return
            
        if new_head in self.snake[:-1]:
            self.trigger_game_over()
            return
            
        self.snake.insert(0, new_head)
        
        if new_head == self.food:
            self.score += SCORE_INCREMENT
            play_sound(eat_sound) 
            self.spawn_food()
            self.on_food_animation(new_head)
        else:
            self.snake.pop()

    def trigger_game_over(self):
        global high_scores
        # Memory save karna: Agar score purane high score se zyada hai
        if self.score > high_scores[self.speed_level]:
            high_scores[self.speed_level] = self.score
            save_data(high_scores) # Storage me permanent save

        self.change_state("GAME_OVER")
        play_sound(game_over_sound) 
        for segment in self.snake:
            px = segment[0] * BLOCK_SIZE + BLOCK_SIZE // 2
            py = segment[1] * BLOCK_SIZE + BLOCK_SIZE // 2
            for _ in range(15):
                self.particles.append(Particle(px, py, SNAKE_COLOR, explode=True))

    def on_food_animation(self, eaten_pos):
        px = eaten_pos[0] * BLOCK_SIZE + BLOCK_SIZE // 2
        py = eaten_pos[1] * BLOCK_SIZE + BLOCK_SIZE // 2
        self.bubbles.append(BubbleEffect(px, py))
        for _ in range(8):
            self.particles.append(Particle(px, py, (255, 255, 100))) 

    def draw_bg_and_ui(self):
        screen.fill(BG_COLOR)
        for star in self.stars:
            star[0] += star[2]
            star[1] += star[3]
            if star[0] < 0: star[0] += DEVICE_WIDTH
            elif star[0] > DEVICE_WIDTH: star[0] -= DEVICE_WIDTH
            if star[1] < 0: star[1] += DEVICE_HEIGHT
            elif star[1] > DEVICE_HEIGHT: star[1] -= DEVICE_HEIGHT
            pygame.draw.circle(screen, (200, 200, 200), (int(star[0]), int(star[1])), int(star[4]))
            
        ui_height = UI_ROWS * BLOCK_SIZE
        pygame.draw.rect(screen, (20, 20, 25), (0, 0, DEVICE_WIDTH, ui_height))
        pygame.draw.line(screen, TEXT_SAFFRON, (0, ui_height), (DEVICE_WIDTH, ui_height), 2)
        draw_text(screen, "JAI SHREE RAM", FONT_TINY, TEXT_SAFFRON, DEVICE_WIDTH // 2, ui_height * 0.2)
        draw_text(screen, "This game is created by Abhishek Pal", FONT_SMALL, TEXT_WHITE, DEVICE_WIDTH // 2, ui_height * 0.5)

    def draw_circle_shiny(self, surface, color, center, radius):
        pygame.draw.circle(surface, color, center, radius)
        hl_radius = max(1, radius // 3)
        hl_center = (center[0] - radius//3, center[1] - radius//3)
        pygame.draw.circle(surface, (255, 255, 255), hl_center, hl_radius)

    def draw(self):
        self.draw_bg_and_ui()
        ui_height = UI_ROWS * BLOCK_SIZE
        
        for b in self.bubbles[:]:
            b.update()
            b.draw(screen)
            if b.life <= 0:
                self.bubbles.remove(b)

        for p in self.particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                self.particles.remove(p)
                
        draw_text(screen, f"Score: {self.score}", FONT_MED, TEXT_GREEN, 15, ui_height * 0.8, align="left")
        best_score = high_scores[self.speed_level]
        draw_text(screen, f"High Score: {best_score}", FONT_SMALL, (200, 200, 200), DEVICE_WIDTH - 15, ui_height * 0.8, align="right")
        
        fx, fy = self.food
        px, py = fx * BLOCK_SIZE + BLOCK_SIZE // 2, fy * BLOCK_SIZE + BLOCK_SIZE // 2
        food_radius = int(BLOCK_SIZE * 0.35) 
        
        pygame.draw.circle(screen, (0, 0, 0), (px + 4, py + 4), food_radius)
        self.draw_circle_shiny(screen, FOOD_COLOR, (px, py), food_radius)
        
        for i in range(len(self.snake) - 1, -1, -1):
            segment = self.snake[i]
            sx, sy = segment
            px, py = sx * BLOCK_SIZE + BLOCK_SIZE // 2, sy * BLOCK_SIZE + BLOCK_SIZE // 2
            radius = int(BLOCK_SIZE * 0.55) 
            
            if i > len(self.snake) - 4:
                radius = max(3, int(radius * (1 - (i - (len(self.snake)-4)) * 0.2))) 
                
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_COLOR
            pygame.draw.circle(screen, (0, 0, 0), (px + 4, py + 4), radius)
            self.draw_circle_shiny(screen, color, (px, py), radius)
            
            if i == 0:
                dx, dy = self.direction
                if dx == 1: e1, e2 = (px + radius//2, py - radius//3), (px + radius//2, py + radius//3)
                elif dx == -1: e1, e2 = (px - radius//2, py - radius//3), (px - radius//2, py + radius//3)
                elif dy == 1: e1, e2 = (px - radius//3, py + radius//2), (px + radius//3, py + radius//2)
                elif dy == -1: e1, e2 = (px - radius//3, py - radius//2), (px + radius//3, py - radius//2)
                else: e1, e2 = (px + radius//2, py - radius//3), (px + radius//2, py + radius//3)
                    
                pygame.draw.circle(screen, TEXT_WHITE, e1, radius//3)
                pygame.draw.circle(screen, TEXT_WHITE, e2, radius//3)
                pygame.draw.circle(screen, (0, 0, 0), (e1[0] + dx*2, e1[1] + dy*2), radius//6)
                pygame.draw.circle(screen, (0, 0, 0), (e2[0] + dx*2, e2[1] + dy*2), radius//6)
            
        pygame.display.flip()

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.start_touch_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.start_touch_pos:
                end_pos = event.pos
                dx = end_pos[0] - self.start_touch_pos[0]
                dy = end_pos[1] - self.start_touch_pos[1]
                if abs(dx) > self.swipe_threshold or abs(dy) > self.swipe_threshold:
                    if abs(dx) > abs(dy): 
                        if dx > 0 and self.direction != (-1, 0): self.next_direction = (1, 0)
                        elif dx < 0 and self.direction != (1, 0): self.next_direction = (-1, 0)
                    else: 
                        if dy > 0 and self.direction != (0, -1): self.next_direction = (0, 1)
                        elif dy < 0 and self.direction != (0, 1): self.next_direction = (0, -1)
                self.start_touch_pos = None
        return events

    # ==========================================
    # SCREENS
    # ==========================================
    
    # 0.3 Second chakke wali loading screen
    def run_transition_screen(self):
        self.handle_events()
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.transition_start_time
        
        # 300 ms (0.3 seconds) baad next page kholna
        if elapsed > 300:
            self.state = self.next_state
            return
            
        self.draw_bg_and_ui()
        
        # Chakke ka math
        center = (DEVICE_WIDTH // 2, DEVICE_HEIGHT // 2)
        radius = int(BLOCK_SIZE * 2.0)
        # 300ms mein 360 degree ek round poora ghumega
        angle = (elapsed / 300.0) * 360
        
        x = center[0] + radius * math.cos(math.radians(angle - 90))
        y = center[1] + radius * math.sin(math.radians(angle - 90))
        
        # Chakka draw karna
        pygame.draw.circle(screen, (60, 60, 70), center, radius, 4) # Piche ki gol line
        pygame.draw.circle(screen, TEXT_SAFFRON, (int(x), int(y)), int(BLOCK_SIZE * 0.4)) # Ghumne wala dot
        
        pygame.display.flip()
        self.clock.tick(60)

    def run_splash_screen(self):
        self.handle_events() 
        current_time = pygame.time.get_ticks()
        
        # Screen 1.2 seconds tak (1200 ms) dikhegi
        if current_time - self.splash_start_time > 1200: 
            self.change_state("HOME") # Home screen pe bhej dega chakke ke through
            
        screen.fill(BG_COLOR)
        
        for star in self.stars:
            pygame.draw.circle(screen, (200, 200, 200), (int(star[0]), int(star[1])), int(star[4]))

        draw_text(screen, "Welcome AP snake x", FONT_MED, TEXT_SAFFRON, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.35)
        draw_text(screen, "This game is created", FONT_SMALL, TEXT_WHITE, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.48)
        draw_text(screen, "by Abhishek Pal", FONT_SMALL, TEXT_WHITE, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.54)
        draw_text(screen, "Thanks for playing!", FONT_TINY, TEXT_GREEN, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.65)
        
        pygame.display.flip()
        self.clock.tick(60)

    def run_home_screen(self):
        bw, bh = DEVICE_WIDTH * 0.6, DEVICE_HEIGHT * 0.06
        btn_auto = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2, bw, bh, "AUTO PLAY", BUTTON_COLOR, BUTTON_HOVER, FONT_SMALL)
        btn_manual = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 + bh*1.5, bw, bh, "MANUAL PLAY", BUTTON_COLOR, BUTTON_HOVER, FONT_SMALL)
        btn_dev = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 + bh*3.0, bw, bh, "DEVELOPER INFO", (100, 100, 200), (80, 80, 180), FONT_SMALL)
        
        while self.state == "HOME":
            events = self.handle_events()
            for event in events:
                if btn_auto.is_clicked(event): 
                    self.mode = "AUTO"
                    self.change_state("MODE_SELECT")
                if btn_manual.is_clicked(event): 
                    self.mode = "MANUAL"
                    self.change_state("MODE_SELECT")
                if btn_dev.is_clicked(event): 
                    self.change_state("DEV_INFO")
            
            self.draw_bg_and_ui()
            draw_text(screen, "SNAKE GAME", FONT_LARGE, TEXT_SAFFRON, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.3)
            best_all_time = max(high_scores.values())
            draw_text(screen, f"All Time High Score: {best_all_time}", FONT_MED, (200, 200, 200), DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.4)
            
            btn_auto.draw(screen)
            btn_manual.draw(screen)
            btn_dev.draw(screen)
            pygame.display.flip()
            self.clock.tick(60)

    def run_dev_info_screen(self):
        bw, bh = DEVICE_WIDTH * 0.4, DEVICE_HEIGHT * 0.06
        btn_back = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT - bh * 2, bw, bh, "<- Back", (100, 100, 100), (150, 150, 150), FONT_SMALL)
        while self.state == "DEV_INFO":
            events = self.handle_events()
            for event in events:
                if btn_back.is_clicked(event): self.change_state("HOME")
            self.draw_bg_and_ui()
            draw_text(screen, "DEVELOPER INFO", FONT_LARGE, TEXT_SAFFRON, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.3)
            draw_text(screen, "Name: Abhishek Pal", FONT_MED, TEXT_WHITE, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.45)
            draw_text(screen, "Education: Diploma in CSE", FONT_SMALL, TEXT_GREEN, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.52)
            draw_text(screen, "Location:  Shahjahanpur, Uttar Pradesh", FONT_SMALL, TEXT_WHITE, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.58)
            draw_text(screen, "YouTube: Mast Bharat AI", FONT_MED, (255, 100, 100), DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.68)
            btn_back.draw(screen)
            pygame.display.flip()
            self.clock.tick(60)

    def run_mode_select_screen(self):
        bw, bh = DEVICE_WIDTH * 0.5, DEVICE_HEIGHT * 0.06
        btn_slow = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 - bh*1.5, bw, bh, "SLOW", TEXT_SAFFRON, (200, 120, 0), FONT_SMALL)
        btn_med = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 + bh*0.5, bw, bh, "MEDIUM", (200, 200, 0), (180, 180, 0), FONT_SMALL)
        btn_fast = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 + bh*2.5, bw, bh, "FAST", TEXT_SAFFRON, (200, 120, 0), FONT_SMALL)
        
        while self.state == "MODE_SELECT":
            events = self.handle_events()
            for event in events:
                if btn_slow.is_clicked(event): 
                    self.speed_level, self.speed = "SLOW", SPEEDS["SLOW"]
                    self.reset_game()
                    self.change_state("PLAYING")
                if btn_med.is_clicked(event): 
                    self.speed_level, self.speed = "MEDIUM", SPEEDS["MEDIUM"]
                    self.reset_game()
                    self.change_state("PLAYING")
                if btn_fast.is_clicked(event): 
                    self.speed_level, self.speed = "FAST", SPEEDS["FAST"]
                    self.reset_game()
                    self.change_state("PLAYING")
            
            self.draw_bg_and_ui()
            draw_text(screen, "SELECT SPEED", FONT_MED, TEXT_WHITE, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.3)
            btn_slow.draw(screen)
            btn_med.draw(screen)
            btn_fast.draw(screen)
            pygame.display.flip()
            self.clock.tick(60)

    def run_game_over_screen(self):
        bw, bh = DEVICE_WIDTH * 0.5, DEVICE_HEIGHT * 0.06
        btn_restart = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 + bh, bw, bh, "Restart Game", BUTTON_COLOR, BUTTON_HOVER, FONT_SMALL)
        btn_home = Button(DEVICE_WIDTH // 2 - bw // 2, DEVICE_HEIGHT // 2 + bh*2.5, bw, bh, "Home", (100, 100, 100), (150, 150, 150), FONT_SMALL)
        
        while self.state == "GAME_OVER":
            events = self.handle_events()
            for event in events:
                if btn_restart.is_clicked(event): 
                    self.reset_game()
                    self.change_state("PLAYING")
                if btn_home.is_clicked(event): 
                    self.change_state("HOME")
            
            self.draw_bg_and_ui()
            for p in self.particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0: self.particles.remove(p)
            
            draw_text(screen, "GAME OVER", FONT_LARGE, TEXT_RED, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.35)
            draw_text(screen, f"Final Score: {self.score}", FONT_MED, TEXT_WHITE, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.45)
            
            if self.score > 0 and self.score >= high_scores[self.speed_level]:
                draw_text(screen, "NEW HIGH SCORE!", FONT_SMALL, TEXT_GREEN, DEVICE_WIDTH // 2, DEVICE_HEIGHT * 0.52)
            
            btn_restart.draw(screen)
            btn_home.draw(screen)
            pygame.display.flip()
            self.clock.tick(60)

    def main_loop(self):
        while self.running:
            if self.state == "SPLASH": self.run_splash_screen()
            elif self.state == "TRANSITION": self.run_transition_screen()
            elif self.state == "HOME": self.run_home_screen()
            elif self.state == "DEV_INFO": self.run_dev_info_screen()
            elif self.state == "MODE_SELECT": self.run_mode_select_screen()
            elif self.state == "PLAYING":
                self.handle_events()
                current_time = pygame.time.get_ticks()
                move_delay = 1000 // self.speed
                if current_time - self.last_move_time > move_delay:
                    self.update_snake()
                    self.last_move_time = current_time
                self.draw()
                self.clock.tick(90) 
            elif self.state == "GAME_OVER": self.run_game_over_screen()
        pygame.quit()

if __name__ == "__main__":
    game = SnakeGame()
    game.main_loop()
