import pygame
import random
import math
import sys
import threading
import numpy as np
import cv2
import mediapipe as mp

pygame.init()

try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SOUND_ON = True
except pygame.error:
    SOUND_ON = False

WIDTH, HEIGHT = 1280, 720
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("StickForce AI - Gesture Battle (Mirror Mode)")
clock = pygame.time.Clock()

WHITE = (246, 249, 255)
BLACK = (4, 7, 16)
MUTED = (145, 160, 190)
CYAN = (28, 238, 242)
BLUE = (55, 136, 255)
YELLOW = (255, 220, 54)
RED = (255, 69, 92)
GREEN = (83, 231, 145)
PURPLE = (182, 92, 255)
ORANGE = (255, 120, 45)
PINK = (255, 88, 180)

font_logo = pygame.font.SysFont("segoeui", 64, bold=True)
font_title = pygame.font.SysFont("segoeui", 34, bold=True)
font_mid = pygame.font.SysFont("segoeui", 23, bold=True)
font_body = pygame.font.SysFont("segoeui", 17)
font_small = pygame.font.SysFont("segoeui", 14)

state = "menu"
message = "Keyboard or gesture: G to toggle camera | MIRROR MODE: Right hand=Move, Left hand=Action"

current_level = 1
unlocked_level = 1
level_stars = [0 for _ in range(20)]

screen_shake = 0
hit_stop = 0
round_start_ticks = pygame.time.get_ticks()
combo_count = 0
combo_timer = 0
damage_flash_player = 0
damage_flash_enemy = 0
level_over = False
level_result = ""
earned_stars = 0

gesture_enabled = False
gesture_command = "none"
gesture_move = 0
gesture_jump = False
gesture_attack = False
gesture_shield = False
gesture_dash = False
gesture_status = "Gesture OFF"

control_mode = "keyboard"

joystick_enabled = False
joystick_move = 0
joystick_jump = False
joystick_attack = False
joystick_shield = False
joystick_dragging = False
joystick_pointer_id = None
joystick_status = "Joystick OFF"

joystick_base = pygame.Vector2(118, HEIGHT - 118)
joystick_knob = pygame.Vector2(118, HEIGHT - 118)
joystick_radius = 56
joystick_knob_radius = 24

jump_button_rect = pygame.Rect(WIDTH - 142, HEIGHT - 248, 104, 104)
attack_button_rect = pygame.Rect(WIDTH - 262, HEIGHT - 132, 104, 104)
shield_button_rect = pygame.Rect(WIDTH - 142, HEIGHT - 132, 104, 104)

camera_frame = None

MIRROR_MODE = True
MOVE_ZONE_LEFT = 0.38
MOVE_ZONE_RIGHT = 0.62
JUMP_ZONE_Y = 0.30
THUMB_JUMP_THRESHOLD = 0.08

kb_training_btn = None
gest_training_btn = None
joy_training_btn = None


def clamp(value, low, high):
    return max(low, min(high, value))


def make_sound(freq=440, duration=0.12, volume=0.25, wave="sine"):
    if not SOUND_ON:
        return None

    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)

    if wave == "square":
        audio = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "noise":
        audio = np.random.uniform(-1, 1, n_samples)
    else:
        audio = np.sin(2 * np.pi * freq * t)

    fade = np.linspace(1, 0, n_samples)
    audio = audio * fade * volume
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))


def make_music(duration=8.0, volume=0.10):
    if not SOUND_ON:
        return None

    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    notes = [220, 277, 330, 392, 330, 277, 247, 294]
    bass = [55, 55, 73, 73, 82, 82, 73, 65]
    audio = np.zeros(n_samples)
    beat = duration / len(notes)

    for i, freq in enumerate(notes):
        start = int(i * beat * sample_rate)
        end = int((i + 1) * beat * sample_rate)
        local_t = t[start:end] - t[start]
        env = np.minimum(1, local_t * 10) * np.maximum(0, 1 - local_t / beat)
        lead = np.sin(2 * np.pi * freq * local_t)
        lead += 0.25 * np.sin(2 * np.pi * freq * 2 * local_t)
        low = 0.7 * np.sin(2 * np.pi * bass[i] * local_t)
        audio[start:end] += (0.38 * lead + 0.46 * low) * env

    audio = audio / max(0.001, np.max(np.abs(audio)))
    stereo = np.column_stack((audio * volume, audio * volume))
    return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))


SND_ATTACK = make_sound(560, 0.08, 0.22, "square")
SND_HIT = make_sound(120, 0.14, 0.30, "noise")
SND_DASH = make_sound(280, 0.11, 0.20, "sine")
SND_JUMP = make_sound(700, 0.08, 0.16, "sine")
SND_ORB = make_sound(940, 0.12, 0.18, "sine")
SND_MENU = make_sound(760, 0.07, 0.13, "sine")
SND_WIN = make_sound(900, 0.20, 0.20, "sine")
SND_LOSE = make_sound(160, 0.25, 0.18, "sine")

if SOUND_ON:
    music_channel = pygame.mixer.Channel(0)
    music_channel.set_volume(0.35)
    music_channel.play(make_music(), loops=-1)


def play(sound):
    if SOUND_ON and sound:
        try:
            sound.play()
        except pygame.error:
            pass


def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))


def draw_glow(surface, x, y, radius, color, alpha=60):
    glow = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
    center = radius * 3 // 2

    for r in range(radius, 3, -6):
        a = int(alpha * (r / max(1, radius)) * 0.18)
        pygame.draw.circle(glow, (*color, a), (center, center), r)

    surface.blit(glow, (x - center, y - center), special_flags=pygame.BLEND_ADD)


def draw_neon_line(surface, start, end, color, width):
    pygame.draw.line(surface, BLACK, start, end, width + 7)
    pygame.draw.line(surface, color, start, end, width)
    pygame.draw.line(surface, WHITE, start, end, max(1, width // 4))


def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def draw_gradient_rect(surface, rect, left_color, right_color, border_radius=8):
    x, y, w, h = rect

    if w <= 0 or h <= 0:
        return

    gradient = pygame.Surface((w, h), pygame.SRCALPHA)

    for i in range(w):
        t = i / max(1, w - 1)
        pygame.draw.line(gradient, lerp_color(left_color, right_color, t), (i, 0), (i, h))

    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=border_radius)
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(gradient, (x, y))


def draw_star(cx, cy, r, color, outline=WHITE):
    points = []

    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r * 0.45
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))

    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, outline, points, 1)


theme_names = [
    "Neon Gate", "Crimson Deck", "Purple Core", "Solar Dock", "Aqua Tower",
    "Ghost Rail", "Violet Rift", "Inferno Pad", "Sky Matrix", "Jade Lab",
    "Night Forge", "Pulse Bridge", "Cyber Ring", "Amber Vault", "Redline",
    "Ion Temple", "Toxic Grid", "Royal Storm", "Final Circuit", "Omega Arena"
]

theme_colors = [
    ((10, 16, 42), (22, 42, 86), CYAN, (255, 214, 60), RED),
    ((30, 10, 22), (72, 24, 42), RED, ORANGE, YELLOW),
    ((20, 12, 45), (55, 28, 100), PURPLE, PINK, CYAN),
    ((36, 24, 8), (90, 54, 18), ORANGE, YELLOW, RED),
    ((7, 24, 34), (18, 74, 92), CYAN, GREEN, BLUE),
]

LEVELS = []

for i in range(20):
    bg1, bg2, accent, enemy, weapon = theme_colors[i % len(theme_colors)]
    LEVELS.append({
        "name": theme_names[i],
        "bg1": bg1,
        "bg2": bg2,
        "accent": accent,
        "enemy": enemy,
        "weapon": weapon,
        "speed": 3.45 + i * 0.045,
        "damage": 10 + i // 4,
        "orbs": max(2, 6 - i // 5),
        "layout": i % 5,
    })


def current_theme():
    return LEVELS[current_level - 1]


class FX:
    def __init__(self, x, y, color, kind="spark"):
        self.x = x
        self.y = y
        self.color = color
        self.kind = kind
        self.life = random.randint(16, 30)
        self.max_life = self.life
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = random.randint(2, 5)

    def update(self):
        self.life -= 1
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.91
        self.vy *= 0.91
        self.vy += 0.13

    def draw(self):
        if self.life <= 0:
            return

        alpha = int(255 * self.life / self.max_life)
        surf = pygame.Surface((38, 38), pygame.SRCALPHA)

        if self.kind == "ring":
            pygame.draw.circle(surf, (*self.color, alpha), (19, 19), self.size + (self.max_life - self.life), 2)
        else:
            pygame.draw.circle(surf, (*self.color, alpha), (19, 19), self.size)

        screen.blit(surf, (self.x - 19, self.y - 19), special_flags=pygame.BLEND_ADD)


effects = []


def burst(x, y, color, count=12):
    for _ in range(count):
        effects.append(FX(x, y, color, "spark"))
    effects.append(FX(x, y, color, "ring"))


class GestureController:
    def __init__(self):
        self.running = False
        self.cap = None
        self.thread = None
        self.jump_cooldown = 0
        self.action_cooldown = 0
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )

    def start(self):
        global gesture_status

        if self.running:
            return

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            gesture_status = "Camera not found"
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.running = True
        gesture_status = "Gesture ON | Right hand=Move | Left hand=Action"
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        global gesture_status, gesture_move, gesture_jump
        global gesture_attack, gesture_shield, gesture_dash

        self.running = False
        gesture_status = "Gesture OFF"
        gesture_move = 0
        gesture_jump = False
        gesture_attack = False
        gesture_shield = False
        gesture_dash = False

        if self.cap:
            self.cap.release()
            self.cap = None

    def is_finger_extended(self, lm, tip_idx, pip_idx):
        return lm[tip_idx].y < lm[pip_idx].y - 0.05

    def loop(self):
        global gesture_command, gesture_move, gesture_jump
        global gesture_attack, gesture_shield, gesture_dash
        global camera_frame, gesture_status

        while self.running:
            ok, frame = self.cap.read()

            if not ok:
                gesture_status = "Camera error"
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)

            gesture_move = 0
            gesture_jump = False
            gesture_attack = False
            gesture_shield = False
            gesture_dash = False

            if self.jump_cooldown > 0:
                self.jump_cooldown -= 1
            if self.action_cooldown > 0:
                self.action_cooldown -= 1

            move_text = "Show fingers"
            action_text = "Show fingers"

            h, w, _ = frame.shape

            if result.multi_hand_landmarks and result.multi_handedness:
                for hand_lms, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    lm = hand_lms.landmark
                    hand_label = handedness.classification[0].label

                    color = (0, 255, 255) if hand_label == "Right" else (255, 100, 255)
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        hand_lms,
                        self.mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=color, thickness=2),
                    )

                    extended = 0
                    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
                        if lm[tip].y < lm[pip].y - 0.05:
                            extended += 1

                    thumb_extended = abs(lm[4].x - lm[2].x) > 0.08
                    thumb_up = lm[4].y < lm[3].y - 0.03

                    if hand_label == "Right":
                        if thumb_up and self.jump_cooldown <= 0:
                            gesture_jump = True
                            self.jump_cooldown = 10
                            move_text = "JUMP"
                        elif extended == 1 and self.is_finger_extended(lm, 8, 6):
                            gesture_move = 1
                            move_text = "RIGHT"
                        elif extended == 2 and self.is_finger_extended(lm, 8, 6) and self.is_finger_extended(lm, 12, 10):
                            gesture_move = -1
                            move_text = "LEFT"
                        else:
                            gesture_move = 0
                            move_text = "STOP"

                        cv2.putText(frame, f"R:{extended}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                    else:
                        total_fingers = extended + (1 if thumb_extended else 0)

                        if self.action_cooldown <= 0:
                            if total_fingers <= 1:
                                gesture_attack = True
                                action_text = "ATTACK"
                                self.action_cooldown = 0
                            elif total_fingers >= 4:
                                gesture_shield = True
                                action_text = "SHIELD"
                            elif total_fingers == 2:
                                gesture_dash = True
                                action_text = "DASH"
                                self.action_cooldown = 10
                            else:
                                action_text = f"{total_fingers}f"
                        else:
                            action_text = f"{self.action_cooldown}"

                        cv2.putText(frame, f"L:{extended}", (w - 80, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 255), 2)

                gesture_command = f"{move_text} | {action_text}"
            else:
                gesture_command = "Show Right + Left"

            gesture_status = gesture_command if gesture_enabled else "Gesture OFF"

            frame = cv2.resize(frame, (260, 180))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            camera_frame = pygame.surfarray.make_surface(frame)


class Button:
    def __init__(self, x, y, w, h, text, fill, border):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.fill = fill
        self.border = border

    def draw(self):
        mouse = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse)
        fill = tuple(min(255, c + 28) for c in self.fill) if hovered else self.fill

        if hovered:
            draw_glow(screen, self.rect.centerx, self.rect.centery, 32, self.border, 45)

        pygame.draw.rect(screen, fill, self.rect, border_radius=12)
        pygame.draw.rect(screen, self.border, self.rect, 2, border_radius=12)

        label = font_mid.render(self.text, True, WHITE)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


class Platform:
    def __init__(self, x, y, w, h, color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color

    def draw(self):
        theme = current_theme()
        accent = theme["accent"]
        base = self.color if self.color else (42, 62, 112)
        r = self.rect

        pygame.draw.rect(screen, (5, 8, 18), (r.x + 8, r.y + 15, r.w, r.h), border_radius=8)
        pygame.draw.rect(screen, base, r, border_radius=9)
        pygame.draw.rect(screen, accent, (r.x, r.y, r.w, 5), border_radius=5)
        pygame.draw.rect(screen, (88, 118, 174), r, 2, border_radius=9)

        for x in range(r.x + 25, r.right - 20, 45):
            pygame.draw.line(screen, (25, 38, 70), (x, r.y + 10), (x + 18, r.bottom - 8), 3)


class EnergyOrb:
    def __init__(self):
        self.x = random.randint(140, WIDTH - 140)
        self.y = random.randint(170, HEIGHT - 175)
        self.radius = 6
        self.float_time = random.random() * 10

    def draw(self):
        bob = math.sin(pygame.time.get_ticks() * 0.004 + self.float_time) * 5
        theme = current_theme()
        draw_glow(screen, int(self.x), int(self.y + bob), 15, theme["accent"], 50)
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y + bob)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y + bob)), self.radius, 1)


class Hazard:
    def __init__(self, x, y, w, h, kind="spike"):
        self.rect = pygame.Rect(x, y, w, h)
        self.kind = kind
        self.cooldown = 0

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self):
        if self.kind == "laser":
            draw_glow(screen, self.rect.centerx, self.rect.centery, 24, RED, 60)
            pygame.draw.rect(screen, RED, self.rect, border_radius=8)
            pygame.draw.rect(screen, WHITE, self.rect, 1, border_radius=8)
        else:
            step = 28
            for x in range(self.rect.x, self.rect.right, step):
                tri = [(x, self.rect.bottom), (x + step // 2, self.rect.y), (x + step, self.rect.bottom)]
                pygame.draw.polygon(screen, RED, tri)
                pygame.draw.polygon(screen, WHITE, tri, 1)


class Fighter:
    def __init__(self, x, y, body_color, weapon_color, name, is_ai=False):
        self.x = x
        self.y = y
        self.w = 40
        self.h = 158
        self.body_color = body_color
        self.weapon_color = weapon_color
        self.name = name
        self.is_ai = is_ai
        self.vx = 0
        self.vy = 0
        self.speed = 5.7
        self.jump_power = 17.5
        self.gravity = 0.72
        self.facing = 1
        self.health = 100
        self.energy = 82
        self.score = 0
        self.on_ground = False
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.hit_registered = False
        self.shield_timer = 0
        self.dash_timer = 0
        self.stun_timer = 0
        self.flash_timer = 0
        self.trail = []

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def move(self, direction):
        if self.stun_timer > 0:
            return
        target = direction * self.speed
        self.vx += (target - self.vx) * 0.27
        if direction != 0:
            self.facing = direction

    def jump(self):
        if self.on_ground and self.stun_timer <= 0:
            self.vy = -self.jump_power
            self.on_ground = False
            play(SND_JUMP)
            burst(self.x, self.y + 74, current_theme()["accent"], 5)

    def attack(self):
        if self.attack_cooldown <= 0 and self.stun_timer <= 0:
            self.attack_timer = 10
            self.attack_cooldown = 6
            self.hit_registered = False
            play(SND_ATTACK)

    def shield(self):
        if self.energy > 0:
            self.shield_timer = 9
            self.energy = max(0, self.energy - 0.85)

    def dash(self):
        if self.energy >= 18 and self.dash_timer <= 0 and self.stun_timer <= 0:
            self.vx = self.facing * 18
            self.energy -= 18
            self.dash_timer = 28
            play(SND_DASH)
            burst(self.x - self.facing * 25, self.y + 18, self.weapon_color, 8)

    def apply_damage(self, amount, attacker_x):
        if self.shield_timer > 0:
            amount = 3
            burst(self.x, self.y, CYAN, 6)
        else:
            burst(self.x, self.y - 15, RED, 12)

        self.health -= amount
        self.stun_timer = 8
        self.flash_timer = 7
        direction = 1 if self.x > attacker_x else -1
        self.vx = direction * 7
        self.vy = -4.8
        play(SND_HIT)

    def update(self, platforms):
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
        if self.dash_timer > 0:
            self.dash_timer -= 1
        if self.stun_timer > 0:
            self.stun_timer -= 1
        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.energy < 100:
            self.energy += 0.17

        self.trail.append((self.x, self.y, self.facing))
        if len(self.trail) > 7:
            self.trail.pop(0)

        old_rect = self.rect()
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.x = clamp(self.x, 35, WIDTH - 35)

        self.on_ground = False
        new_rect = self.rect()

        for p in platforms:
            if new_rect.colliderect(p.rect):
                if old_rect.bottom <= p.rect.top and self.vy >= 0:
                    self.y = p.rect.top - self.h / 2
                    self.vy = 0
                    self.on_ground = True
                    new_rect = self.rect()

        if self.y > HEIGHT + 120:
            self.health = 0

        self.vx *= 0.86 if self.on_ground else 0.97

    def ai_control(self, target):
        if self.health <= 0:
            return

        theme = current_theme()
        distance_x = target.x - self.x
        distance_y = target.y - self.y
        backup = self.speed
        self.speed = theme["speed"]

        if abs(distance_x) > 125:
            self.move(1 if distance_x > 0 else -1)
        else:
            self.move(0)
            if self.attack_cooldown <= 0 and random.random() < 0.30:
                self.attack()

        if distance_y < -105 and self.on_ground and random.random() < 0.015:
            self.jump()

        if target.attack_timer > 5 and abs(distance_x) < 150 and random.random() < 0.015:
            self.shield()

        if abs(distance_x) > 320 and self.energy > 45 and random.random() < 0.002:
            self.dash()

        self.speed = backup

    def draw_limb(self, start, end, color, width=7):
        pygame.draw.line(screen, BLACK, start, end, width + 5)
        pygame.draw.line(screen, color, start, end, width)
        pygame.draw.circle(screen, BLACK, start, width // 2 + 3)
        pygame.draw.circle(screen, color, start, width // 2 + 1)
        pygame.draw.circle(screen, BLACK, end, width // 2 + 3)
        pygame.draw.circle(screen, color, end, width // 2 + 1)

    def draw_cape(self, neck, hip):
        wind = math.sin(pygame.time.get_ticks() * 0.006 + self.x * 0.01) * 7
        cape = [
            neck,
            (neck[0] - self.facing * 20, neck[1] + 25),
            (hip[0] - self.facing * 42 + int(wind), hip[1] + 28),
            (hip[0] - self.facing * 12, hip[1] + 6),
        ]
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (*self.weapon_color, 58), cape)
        pygame.draw.lines(surf, (*self.weapon_color, 100), True, cape, 2)
        screen.blit(surf, (0, 0), special_flags=pygame.BLEND_ADD)

    def draw(self):
        t = pygame.time.get_ticks() * 0.012
        idle = math.sin(t + self.x * 0.01) * 2
        walk = math.sin(t) * 15 if abs(self.vx) > 0.7 and self.on_ground else 0
        lean = self.facing * (10 if abs(self.vx) > 1 else 4)

        for i, item in enumerate(self.trail[:-3]):
            tx, ty, _ = item
            alpha = int(12 + i * 7)
            trail_surf = pygame.Surface((70, 178), pygame.SRCALPHA)
            pygame.draw.line(trail_surf, (*self.body_color, alpha), (35, 45), (35, 118), 6)
            pygame.draw.circle(trail_surf, (*self.body_color, alpha), (35, 24), 15)
            screen.blit(trail_surf, (tx - 35, ty - 92), special_flags=pygame.BLEND_ADD)

        head = (int(self.x + lean), int(self.y - 72 + idle))
        neck = (int(self.x), int(self.y - 42 + idle))
        chest = (int(self.x + lean), int(self.y - 4 + idle))
        waist = (int(self.x), int(self.y + 31 + idle))
        hip = (int(self.x), int(self.y + 49 + idle))

        left_foot = (int(self.x - 20 - walk), int(self.y + 78))
        right_foot = (int(self.x + 20 + walk), int(self.y + 78))
        back_hand = (int(self.x - self.facing * 35), int(self.y - 8 + idle))
        front_hand = (int(self.x + self.facing * 42), int(self.y - 17 + idle))

        if self.attack_timer > 0:
            swing = self.attack_timer
            front_hand = (int(self.x + self.facing * (80 - swing)), int(self.y - 46 + swing * 2))
            back_hand = (int(self.x - self.facing * 22), int(self.y + 5))

        if self.shield_timer > 0:
            pygame.draw.circle(screen, CYAN, (int(self.x), int(self.y)), 64, 3)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 70, 1)

        shadow = pygame.Rect(int(self.x - 36), int(self.y + 74), 72, 11)
        pygame.draw.ellipse(screen, (4, 7, 16), shadow)
        color = WHITE if self.flash_timer > 0 else self.body_color

        self.draw_cape(neck, hip)
        self.draw_limb(neck, chest, color, 8)
        self.draw_limb(chest, waist, color, 8)
        self.draw_limb(waist, hip, color, 7)
        self.draw_limb(chest, back_hand, color, 7)
        self.draw_limb(chest, front_hand, color, 7)
        self.draw_limb(hip, left_foot, color, 7)
        self.draw_limb(hip, right_foot, color, 7)

        pygame.draw.circle(screen, BLACK, head, 24)
        pygame.draw.circle(screen, color, head, 18)
        pygame.draw.circle(screen, WHITE, head, 18, 2)

        helmet = [
            (head[0] - 14, head[1] - 10),
            (head[0] + 7 * self.facing, head[1] - 22),
            (head[0] + 18 * self.facing, head[1] - 4),
        ]
        pygame.draw.polygon(screen, BLACK, helmet)
        pygame.draw.polygon(screen, color, helmet, 2)

        visor = pygame.Rect(head[0] - 11 + self.facing * 4, head[1] - 7, 20, 7)
        pygame.draw.rect(screen, BLACK, visor, border_radius=4)
        pygame.draw.rect(screen, self.weapon_color, visor, 2, border_radius=4)

        pygame.draw.circle(screen, BLACK, chest, 9)
        pygame.draw.circle(screen, self.weapon_color, chest, 6)

        sword_start = front_hand
        if self.attack_timer > 0:
            sword_end = (int(front_hand[0] + self.facing * 105), int(front_hand[1] - 20))
            draw_glow(screen, sword_end[0], sword_end[1], 28, self.weapon_color, 70)
            draw_neon_line(screen, sword_start, sword_end, self.weapon_color, 7)
        else:
            sword_end = (int(front_hand[0] + self.facing * 50), int(front_hand[1] - 55))
            draw_neon_line(screen, sword_start, sword_end, self.weapon_color, 5)

        label = font_small.render(self.name, True, WHITE)
        screen.blit(label, label.get_rect(center=(int(self.x), int(self.y - 115))))


class StarParticle:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.12, 0.8)
        self.size = random.randint(1, 3)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self):
        pygame.draw.circle(screen, (45, 70, 128), (int(self.x), int(self.y)), self.size)


stars_bg = [StarParticle() for _ in range(90)]
platforms = []
orbs = []
hazards = []
player = None
enemy = None

menu_buttons = [
    Button(485, 292, 310, 54, "Continue", (28, 118, 215), CYAN),
    Button(485, 362, 310, 54, "Level Select", (86, 62, 168), PURPLE),
    Button(485, 432, 310, 54, "Online Lobby", (32, 138, 92), GREEN),
    Button(485, 502, 310, 54, "AI Training", (154, 82, 24), ORANGE),
    Button(485, 572, 310, 54, "Exit", (166, 48, 65), RED),
]

back_button = Button(28, 98, 100, 32, "MENU", (8, 47, 120), CYAN)
gesture_controller = GestureController()


def build_platforms(layout):
    if layout == 0:
        return [
            Platform(80, 620, 1120, 42),
            Platform(120, 485, 260, 28),
            Platform(900, 485, 260, 28),
            Platform(470, 380, 340, 28),
            Platform(210, 285, 180, 24),
            Platform(890, 285, 180, 24),
        ]
    if layout == 1:
        return [
            Platform(90, 620, 1100, 42),
            Platform(190, 505, 210, 28),
            Platform(880, 505, 210, 28),
            Platform(515, 420, 250, 26),
            Platform(90, 330, 190, 24),
            Platform(1000, 330, 190, 24),
        ]
    if layout == 2:
        return [
            Platform(90, 620, 1100, 42),
            Platform(420, 500, 440, 28),
            Platform(155, 405, 220, 26),
            Platform(905, 405, 220, 26),
            Platform(500, 300, 280, 24),
        ]
    if layout == 3:
        return [
            Platform(80, 620, 1120, 42),
            Platform(140, 515, 240, 26),
            Platform(455, 455, 370, 26),
            Platform(900, 515, 240, 26),
            Platform(265, 345, 210, 24),
            Platform(805, 345, 210, 24),
        ]
    return [
        Platform(90, 620, 1100, 42),
        Platform(130, 470, 190, 26),
        Platform(420, 390, 190, 26),
        Platform(670, 390, 190, 26),
        Platform(960, 470, 190, 26),
        Platform(520, 275, 240, 24),
    ]


def build_hazards(level_number):
    hazards_list = []
    if level_number >= 3:
        hazards_list.append(Hazard(520, 602, 80, 18, "spike"))
    if level_number >= 6:
        hazards_list.append(Hazard(720, 602, 80, 18, "spike"))
    if level_number >= 9:
        hazards_list.append(Hazard(210, 470, 90, 11, "laser"))
    if level_number >= 12:
        hazards_list.append(Hazard(980, 470, 90, 11, "laser"))
    if level_number >= 15:
        hazards_list.append(Hazard(585, 360, 105, 11, "laser"))
    if level_number >= 18:
        hazards_list.append(Hazard(340, 602, 75, 18, "spike"))
    return hazards_list


def reset_level(level_number):
    global current_level, platforms, orbs, hazards, player, enemy
    global message, screen_shake, hit_stop, round_start_ticks
    global combo_count, combo_timer, damage_flash_player, damage_flash_enemy
    global level_over, level_result, earned_stars

    current_level = clamp(level_number, 1, 20)
    theme = current_theme()
    platforms = build_platforms(theme["layout"])
    hazards = build_hazards(current_level)
    orbs = [EnergyOrb() for _ in range(theme["orbs"])]
    player = Fighter(260, 480, CYAN, BLUE, "YOU")
    enemy = Fighter(980, 480, theme["enemy"], theme["weapon"], "AI RIVAL", is_ai=True)
    enemy.facing = -1
    effects.clear()

    message = "Keyboard: A/D/W/F/E/Shift | G changes mode"
    screen_shake = 0
    hit_stop = 0
    round_start_ticks = pygame.time.get_ticks()
    combo_count = 0
    combo_timer = 0
    damage_flash_player = 0
    damage_flash_enemy = 0
    level_over = False
    level_result = ""
    earned_stars = 0


def calculate_stars():
    elapsed = (pygame.time.get_ticks() - round_start_ticks) // 1000
    stars = 1
    if player.health >= 45:
        stars += 1
    if elapsed <= 55:
        stars += 1
    return clamp(stars, 1, 3)


def draw_background():
    theme = current_theme()
    bg1, bg2, accent = theme["bg1"], theme["bg2"], theme["accent"]
    screen.fill(bg1)

    for s in stars_bg:
        s.update()
        s.draw()

    for y in range(HEIGHT):
        t = y / HEIGHT
        pygame.draw.line(screen, lerp_color(bg1, bg2, t), (0, y), (WIDTH, y))

    for i in range(8):
        x = 65 + i * 175
        pygame.draw.rect(screen, lerp_color(bg2, BLACK, 0.35), (x, 65, 94, 362), border_radius=22)
        pygame.draw.rect(screen, lerp_color(accent, WHITE, 0.20), (x + 12, 82, 70, 114), 2, border_radius=16)

    pulse = int(10 * math.sin(pygame.time.get_ticks() * 0.003))
    pygame.draw.circle(screen, lerp_color(accent, bg2, 0.55), (WIDTH // 2, 248), 270 + pulse, 7)
    pygame.draw.circle(screen, lerp_color(accent, WHITE, 0.25), (WIDTH // 2, 248), 190, 4)
    pygame.draw.line(screen, lerp_color(accent, WHITE, 0.15), (WIDTH // 2, 30), (WIDTH // 2, 475), 3)
    pygame.draw.line(screen, lerp_color(accent, WHITE, 0.15), (365, 248), (915, 248), 3)

    beam = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(beam, (*accent, 25), [(520, 75), (760, 75), (930, 620), (350, 620)])
    screen.blit(beam, (0, 0), special_flags=pygame.BLEND_ADD)

    pygame.draw.rect(screen, (8, 13, 31), (0, 630, WIDTH, 90))
    pygame.draw.rect(screen, lerp_color(bg2, BLACK, 0.25), (0, 650, WIDTH, 70))
    pygame.draw.line(screen, accent, (80, 620), (1200, 620), 3)

    for x in range(-40, WIDTH, 80):
        pygame.draw.line(screen, lerp_color(accent, bg2, 0.65), (x, 650), (x + 40, 720), 2)


def draw_title_logo():
    draw_text("STICKFORCE", font_logo, YELLOW, 384, 96)
    draw_text("AI", font_logo, CYAN, 762, 96)
    text = font_mid.render("Gesture Battle Arena", True, WHITE)
    screen.blit(text, text.get_rect(center=(WIDTH // 2, 210)))

    demo_left = Fighter(382, 286, CYAN, BLUE, "P1")
    demo_right = Fighter(898, 286, YELLOW, RED, "P2")
    demo_left.facing = 1
    demo_right.facing = -1
    demo_left.attack_timer = 12
    demo_right.attack_timer = 12
    demo_left.draw()
    demo_right.draw()


def draw_menu():
    draw_background()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 74))
    screen.blit(overlay, (0, 0))
    draw_title_logo()

    panel = pygame.Rect(445, 265, 390, 380)
    pygame.draw.rect(screen, (12, 19, 42), panel, border_radius=18)
    pygame.draw.rect(screen, CYAN, panel, 2, border_radius=18)

    for b in menu_buttons:
        b.draw()

    total_stars = sum(level_stars)
    draw_text(f"Unlocked: {unlocked_level}/20  |  Stars: {total_stars}/60", font_body, WHITE, 440, 655)
    draw_text("TIP: Press G to cycle Keyboard / Gesture / Joystick", font_small, MUTED, 430, 678)


def draw_level_select():
    draw_background()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 105))
    screen.blit(overlay, (0, 0))

    draw_text("SELECT LEVEL", font_logo, WHITE, 420, 48)
    draw_text("Higher levels add spikes and lasers.", font_body, MUTED, 465, 126)

    cards = []
    start_x, start_y = 135, 175
    card_w, card_h = 190, 92
    gap_x, gap_y = 30, 28

    for i in range(20):
        level_num = i + 1
        row, col = i // 5, i % 5
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        rect = pygame.Rect(x, y, card_w, card_h)
        locked = level_num > unlocked_level
        theme = LEVELS[i]
        mouse = pygame.mouse.get_pos()
        fill = (18, 26, 50) if not locked else (16, 18, 26)

        if rect.collidepoint(mouse) and not locked:
            fill = lerp_color(fill, theme["accent"], 0.25)

        pygame.draw.rect(screen, fill, rect, border_radius=14)
        pygame.draw.rect(screen, theme["accent"] if not locked else (70, 70, 80), rect, 2, border_radius=14)

        draw_text(f"LEVEL {level_num:02d}", font_mid, WHITE if not locked else MUTED, x + 16, y + 12)
        draw_text(theme["name"] if not locked else "Locked", font_small, MUTED, x + 16, y + 42)

        for s in range(3):
            color = YELLOW if level_stars[i] > s else (65, 68, 80)
            draw_star(x + 26 + s * 25, y + 72, 9, color, (120, 125, 145))

        if locked:
            draw_text("LOCK", font_small, (100, 105, 120), x + 135, y + 68)

        cards.append((rect, level_num, locked))

    back_button.draw()
    return cards


def draw_portrait(x, y, color, weapon_color, facing=1):
    pygame.draw.circle(screen, BLACK, (x, y), 26)
    pygame.draw.circle(screen, color, (x, y), 20)
    pygame.draw.circle(screen, WHITE, (x, y), 20, 2)
    visor = pygame.Rect(x - 11 + facing * 4, y - 7, 19, 7)
    pygame.draw.rect(screen, BLACK, visor, border_radius=4)
    pygame.draw.rect(screen, weapon_color, visor, 2, border_radius=4)


def draw_simple_bar(x, y, w, h, value, color, label):
    value = clamp(value, 0, 100)
    pygame.draw.rect(screen, (12, 20, 38), (x, y, w, h), border_radius=8)
    fill_w = int(w * value / 100)

    if fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=8)

    label_img = font_small.render(label, True, WHITE)
    screen.blit(label_img, label_img.get_rect(center=(x + w // 2, y + h // 2)))


def draw_hud():
    global combo_timer, combo_count

    theme = current_theme()
    elapsed = (pygame.time.get_ticks() - round_start_ticks) // 1000
    remaining = max(0, 99 - elapsed)

    hud_h = 118
    hud = pygame.Surface((WIDTH - 16, hud_h - 14), pygame.SRCALPHA)
    hud.fill((3, 7, 18, 175))
    screen.blit(hud, (8, 10))

    pygame.draw.rect(screen, PURPLE, (8, 10, WIDTH - 16, hud_h - 14), 2)
    pygame.draw.line(screen, theme["accent"], (8, hud_h - 4), (WIDTH - 8, hud_h - 4), 1)

    draw_text("STICKFORCE", font_body, WHITE, 24, 28)
    draw_text("AI", font_body, CYAN, 142, 28)
    draw_text(f"LEVEL {current_level}", font_body, WHITE, 24, 58)

    back_button.rect = pygame.Rect(24, 84, 86, 22)
    mouse = pygame.mouse.get_pos()
    hovered = back_button.rect.collidepoint(mouse)
    menu_fill = (12, 70, 155) if hovered else (7, 43, 110)
    pygame.draw.rect(screen, menu_fill, back_button.rect, border_radius=11)
    menu_txt = font_small.render("MENU", True, WHITE)
    screen.blit(menu_txt, menu_txt.get_rect(center=back_button.rect.center))

    pygame.draw.line(screen, (13, 118, 160), (185, 16), (185, hud_h - 10), 1)

    draw_text("YOU", font_small, WHITE, 212, 24)
    draw_portrait(235, 68, player.body_color, player.weapon_color, 1)
    draw_simple_bar(295, 48, 260, 13, player.health, (24, 130, 232), "HEALTH")
    draw_simple_bar(295, 80, 260, 13, player.energy, (24, 130, 232), "ENERGY")

    capsule_center_x = 690
    center = pygame.Rect(capsule_center_x - 95, 18, 190, 94)
    center_surf = pygame.Surface((center.w, center.h), pygame.SRCALPHA)
    pygame.draw.rect(center_surf, (5, 44, 118, 225), (0, 0, center.w, center.h), border_radius=26)
    screen.blit(center_surf, center.topleft)

    score_text = font_title.render(f"{player.score:05d}", True, CYAN)
    screen.blit(score_text, score_text.get_rect(center=(capsule_center_x, 42)))

    timer_text = font_mid.render(f"TIME {remaining:02d}", True, WHITE)
    screen.blit(timer_text, timer_text.get_rect(center=(capsule_center_x, 72)))

    best_text = font_mid.render(f"BEST {level_stars[current_level - 1]}/3", True, WHITE)
    screen.blit(best_text, best_text.get_rect(center=(capsule_center_x, 100)))

    draw_text("AI", font_small, WHITE, 910, 24)
    draw_portrait(935, 68, enemy.body_color, enemy.weapon_color, -1)
    draw_simple_bar(995, 48, 240, 13, enemy.health, (24, 130, 232), "HEALTH")
    draw_simple_bar(995, 80, 240, 13, enemy.energy, (24, 130, 232), "ENERGY")

    if combo_timer > 0:
        combo_timer -= 1
        combo = font_mid.render(f"{combo_count} HIT COMBO!", True, YELLOW)
        screen.blit(combo, combo.get_rect(center=(WIDTH // 2, hud_h + 20)))
    else:
        combo_count = 0


def draw_ability_icons():
    if control_mode == "joystick" and joystick_enabled:
        return

    items = [
        ("SHIELD", "Left: Palm", CYAN, 0),
        ("DASH", "Left: 2 Fingers", PURPLE, 18),
        ("ATTACK", "Left: Fist", RED, 0),
    ]
    start_x = WIDTH // 2 - 240
    y = HEIGHT - 82

    for i, (name, key, color, cost) in enumerate(items):
        x = start_x + i * 170
        box = pygame.Rect(x, y, 150, 58)
        pygame.draw.rect(screen, (9, 14, 31), box, border_radius=12)
        pygame.draw.rect(screen, color, box, 2, border_radius=12)

        key_text = font_small.render(key, True, WHITE)
        screen.blit(key_text, key_text.get_rect(center=(box.centerx, box.y + 20)))

        name_text = font_small.render(name, True, MUTED)
        screen.blit(name_text, name_text.get_rect(center=(box.centerx, box.y + 41)))

        if cost > 0:
            cost_text = font_small.render(f"-{cost}E", True, YELLOW)
            screen.blit(cost_text, cost_text.get_rect(center=(box.centerx + 55, box.y + 14)))


def reset_joystick_buttons():
    global joystick_move, joystick_jump, joystick_attack, joystick_shield
    global joystick_dragging, joystick_pointer_id, joystick_knob

    joystick_move = 0
    joystick_jump = False
    joystick_attack = False
    joystick_shield = False
    joystick_dragging = False
    joystick_pointer_id = None
    joystick_knob = joystick_base.copy()


def handle_joystick_event(event):
    global joystick_move, joystick_jump, joystick_attack, joystick_shield
    global joystick_dragging, joystick_pointer_id, joystick_knob

    if not joystick_enabled or state != "duel":
        return

    if event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.Vector2(event.pos)

        if pos.distance_to(joystick_base) <= joystick_radius + 34:
            joystick_dragging = True
            joystick_pointer_id = "mouse"

        if jump_button_rect.collidepoint(event.pos):
            joystick_jump = True
        if attack_button_rect.collidepoint(event.pos):
            joystick_attack = True
        if shield_button_rect.collidepoint(event.pos):
            joystick_shield = True

    elif event.type == pygame.MOUSEMOTION and joystick_dragging:
        pos = pygame.Vector2(event.pos)
        delta = pos - joystick_base

        if delta.length() > joystick_radius:
            delta.scale_to_length(joystick_radius)

        joystick_knob = joystick_base + delta

        if delta.x < -18:
            joystick_move = -1
        elif delta.x > 18:
            joystick_move = 1
        else:
            joystick_move = 0

    elif event.type == pygame.MOUSEBUTTONUP:
        joystick_dragging = False
        joystick_pointer_id = None
        joystick_move = 0
        joystick_knob = joystick_base.copy()

    elif event.type == pygame.FINGERDOWN:
        pos = pygame.Vector2(event.x * WIDTH, event.y * HEIGHT)

        if pos.distance_to(joystick_base) <= joystick_radius + 34:
            joystick_dragging = True
            joystick_pointer_id = event.finger_id

        point = (int(pos.x), int(pos.y))
        if jump_button_rect.collidepoint(point):
            joystick_jump = True
        if attack_button_rect.collidepoint(point):
            joystick_attack = True
        if shield_button_rect.collidepoint(point):
            joystick_shield = True

    elif event.type == pygame.FINGERMOTION and joystick_dragging and event.finger_id == joystick_pointer_id:
        pos = pygame.Vector2(event.x * WIDTH, event.y * HEIGHT)
        delta = pos - joystick_base

        if delta.length() > joystick_radius:
            delta.scale_to_length(joystick_radius)

        joystick_knob = joystick_base + delta

        if delta.x < -18:
            joystick_move = -1
        elif delta.x > 18:
            joystick_move = 1
        else:
            joystick_move = 0

    elif event.type == pygame.FINGERUP and event.finger_id == joystick_pointer_id:
        joystick_dragging = False
        joystick_pointer_id = None
        joystick_move = 0
        joystick_knob = joystick_base.copy()


def draw_round_button(rect, text, color, active=False):
    radius = rect.w // 2
    center = (radius, radius)

    surf = pygame.Surface((rect.w + 26, rect.h + 26), pygame.SRCALPHA)
    offset = 13
    c = (radius + offset, radius + offset)

    glow_alpha = 145 if active else 70
    pygame.draw.circle(surf, (*color, glow_alpha), c, radius + 12)
    pygame.draw.circle(surf, (0, 0, 0, 115), (c[0] + 5, c[1] + 8), radius)

    pygame.draw.circle(surf, (7, 13, 31, 245), c, radius)
    pygame.draw.circle(surf, (*color, 210 if active else 155), c, radius - 7)

    pygame.draw.circle(surf, (255, 255, 255, 45), (c[0] - 17, c[1] - 20), radius // 2)
    pygame.draw.circle(surf, (255, 255, 255, 210), c, radius - 2, 3)
    pygame.draw.circle(surf, (*color, 255), c, radius - 12, 3)

    pygame.draw.arc(
        surf,
        (255, 255, 255, 120),
        pygame.Rect(c[0] - radius + 12, c[1] - radius + 12, (radius - 12) * 2, (radius - 12) * 2),
        math.radians(205),
        math.radians(335),
        4,
    )

    screen.blit(surf, (rect.x - offset, rect.y - offset))

    main = font_mid.render(text, True, WHITE)
    screen.blit(main, main.get_rect(center=(rect.centerx, rect.centery - 3)))

    hint = ""
    if text == "JUMP":
        hint = "UP"
    elif text == "ATK":
        hint = "HIT"
    elif text == "SHLD":
        hint = "BLOCK"

    hint_img = font_small.render(hint, True, (225, 235, 255))
    screen.blit(hint_img, hint_img.get_rect(center=(rect.centerx, rect.centery + 24)))

def draw_joystick_controls():
    if not joystick_enabled or state != "duel":
        return

    base = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.circle(base, (4, 8, 20, 135), (80, 80), joystick_radius)
    pygame.draw.circle(base, (*CYAN, 155), (80, 80), joystick_radius, 3)

    knob_x = int(80 + joystick_knob.x - joystick_base.x)
    knob_y = int(80 + joystick_knob.y - joystick_base.y)
    pygame.draw.circle(base, (*BLUE, 205), (knob_x, knob_y), joystick_knob_radius)
    pygame.draw.circle(base, (*WHITE, 180), (knob_x, knob_y), joystick_knob_radius, 2)

    screen.blit(base, (joystick_base.x - 80, joystick_base.y - 80))

    draw_round_button(jump_button_rect, "JUMP", CYAN, joystick_jump)
    draw_round_button(attack_button_rect, "ATK", RED, joystick_attack)
    draw_round_button(shield_button_rect, "SHLD", BLUE, joystick_shield)


def resolve_attacks():
    global message, screen_shake, hit_stop, combo_count, combo_timer
    global damage_flash_player, damage_flash_enemy

    theme = current_theme()

    for attacker, defender in [(player, enemy), (enemy, player)]:
        if attacker.attack_timer > 0 and not attacker.hit_registered:
            in_front = (defender.x - attacker.x) * attacker.facing > 0
            close_x = abs(defender.x - attacker.x) < 145
            close_y = abs(defender.y - attacker.y) < 130

            if in_front and close_x and close_y:
                damage = 15 if attacker == player else theme["damage"]
                defender.apply_damage(damage, attacker.x)
                attacker.hit_registered = True
                attacker.score += 10
                screen_shake = 7
                hit_stop = 3

                if defender == player:
                    damage_flash_player = 8
                else:
                    damage_flash_enemy = 8

                if attacker == player:
                    combo_count += 1
                    combo_timer = 90
                    message = f"Clean hit! {combo_count}x combo!"
                else:
                    combo_count = 0
                    combo_timer = 0


def collect_orbs():
    global message

    for orb in orbs[:]:
        if math.hypot(player.x - orb.x, player.y - orb.y) < 30:
            player.energy = min(100, player.energy + 24)
            player.score += 6
            orbs.remove(orb)
            orbs.append(EnergyOrb())
            play(SND_ORB)
            burst(player.x, player.y, YELLOW, 8)
            message = "Energy +24! Score +6"


def update_hazards():
    global message

    for hazard in hazards:
        hazard.update()

        if player.rect().colliderect(hazard.rect) and hazard.cooldown <= 0:
            player.apply_damage(5 + current_level // 6, hazard.rect.centerx)
            hazard.cooldown = 55
            message = "Hazard hit! -5 HP"


def finish_level(result):
    global level_over, level_result, earned_stars, unlocked_level

    if level_over:
        return

    level_over = True
    level_result = result

    if result == "LEVEL COMPLETE":
        earned_stars = calculate_stars()
        idx = current_level - 1
        level_stars[idx] = max(level_stars[idx], earned_stars)
        unlocked_level = max(unlocked_level, min(20, current_level + 1))
        play(SND_WIN)
    else:
        earned_stars = 0
        play(SND_LOSE)


def update_duel(keys):
    global message, damage_flash_player, damage_flash_enemy
    global joystick_jump, joystick_attack, joystick_shield

    if level_over:
        return

    if damage_flash_player > 0:
        damage_flash_player -= 1
    if damage_flash_enemy > 0:
        damage_flash_enemy -= 1

    elapsed = (pygame.time.get_ticks() - round_start_ticks) // 1000
    remaining = max(0, 99 - elapsed)

    if enemy.health <= 0:
        player.score += 100
        message = "LEVEL COMPLETE!"
        finish_level("LEVEL COMPLETE")
        return

    if player.health <= 0:
        message = "You lost! Press R to retry"
        finish_level("LEVEL FAILED")
        return

    if remaining <= 0:
        finish_level("LEVEL COMPLETE" if player.health >= enemy.health else "LEVEL FAILED")
        return

    direction = 0

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        direction -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        direction += 1

    if gesture_enabled:
        direction += gesture_move

    if control_mode == "joystick" and joystick_enabled:
        direction += joystick_move

    direction = clamp(direction, -1, 1)
    player.move(direction)

    if gesture_enabled:
        if gesture_jump:
            player.jump()
        if gesture_attack:
            player.attack()
        if gesture_shield:
            player.shield()
            if random.random() < 0.05:
                message = "Shield active!"
        if gesture_dash:
            player.dash()

    if control_mode == "joystick" and joystick_enabled:
        if joystick_jump:
            player.jump()
            joystick_jump = False
        if joystick_attack:
            player.attack()
            joystick_attack = False
        if joystick_shield:
            player.shield()
            joystick_shield = False

    if keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
        if not gesture_enabled or not gesture_jump:
            player.jump()
    if keys[pygame.K_f]:
        player.attack()
    if keys[pygame.K_e]:
        player.shield()
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        player.dash()

    enemy.ai_control(player)
    player.update(platforms)
    enemy.update(platforms)
    resolve_attacks()
    collect_orbs()
    update_hazards()

    for fx in effects[:]:
        fx.update()
        if fx.life <= 0:
            effects.remove(fx)


def draw_camera_preview(x, y):
    if gesture_enabled and camera_frame is not None:
        preview_box = pygame.Rect(x, y, 270, 190)
        pygame.draw.rect(screen, (8, 13, 31), preview_box, border_radius=12)
        pygame.draw.rect(screen, current_theme()["accent"], preview_box, 2, border_radius=12)
        screen.blit(camera_frame, (x + 5, y + 5))

        cmd = gesture_command.upper()
        if len(cmd) > 28:
            cmd = cmd[:25] + "..."
        draw_text(cmd, font_small, WHITE, x + 12, y + 165)
        draw_text("Right hand -> Move | Left hand -> Action", font_small, CYAN, x + 8, y + 5)


def draw_duel():
    global screen_shake

    offset_x = offset_y = 0

    if screen_shake > 0:
        offset_x = random.randint(-screen_shake, screen_shake)
        offset_y = random.randint(-screen_shake, screen_shake)
        screen_shake -= 1

    world = pygame.Surface((WIDTH, HEIGHT))
    old_screen = screen
    globals()["screen"] = world

    draw_background()

    for p in platforms:
        p.draw()
    for hazard in hazards:
        hazard.draw()
    for orb in orbs:
        orb.draw()

    player.draw()
    enemy.draw()

    for fx in effects:
        fx.draw()

    draw_hud()
    draw_ability_icons()
    draw_camera_preview(WIDTH - 292, HEIGHT - 218)
    draw_joystick_controls()

    if level_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        world.blit(overlay, (0, 0))

        color = GREEN if level_result == "LEVEL COMPLETE" else RED
        text = font_logo.render(level_result, True, color)
        world.blit(text, text.get_rect(center=(WIDTH // 2, 255)))

        if level_result == "LEVEL COMPLETE":
            for i in range(3):
                star_color = YELLOW if earned_stars > i else (65, 68, 80)
                draw_star(WIDTH // 2 - 60 + i * 60, 335, 24, star_color)
            msg = "Press N: Next | R: Replay | Esc: Menu"
        else:
            msg = "Press R: Retry | Esc: Menu"

        sub = font_mid.render(f"Score: {player.score}", True, WHITE)
        world.blit(sub, sub.get_rect(center=(WIDTH // 2, 395)))

        hint = font_body.render(msg, True, MUTED)
        world.blit(hint, hint.get_rect(center=(WIDTH // 2, 435)))

    globals()["screen"] = old_screen
    screen.blit(world, (offset_x, offset_y))


def draw_placeholder(title, lines):
    draw_background()

    panel = pygame.Rect(260, 170, 760, 360)
    pygame.draw.rect(screen, (13, 20, 42), panel, border_radius=18)
    pygame.draw.rect(screen, current_theme()["accent"], panel, 2, border_radius=18)

    heading = font_title.render(title, True, WHITE)
    screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 220)))

    y = 290
    for line in lines:
        item = font_mid.render(line, True, MUTED)
        screen.blit(item, item.get_rect(center=(WIDTH // 2, y)))
        y += 55

    back_button.draw()


def draw_training_screen():
    draw_background()

    panel = pygame.Rect(180, 100, 920, 520)
    pygame.draw.rect(screen, (13, 20, 42), panel, border_radius=18)
    pygame.draw.rect(screen, current_theme()["accent"], panel, 2, border_radius=18)

    heading = font_title.render("Control Methods", True, WHITE)
    screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 140)))

    btn_w, btn_h = 240, 50
    btn_y = 190

    global kb_training_btn, gest_training_btn, joy_training_btn
    kb_training_btn = Button(WIDTH // 2 - 380, btn_y, btn_w, btn_h, "Keyboard", (40, 80, 140), CYAN)
    gest_training_btn = Button(WIDTH // 2 - 120, btn_y, btn_w, btn_h, "Gestures", (80, 40, 120), PURPLE)
    joy_training_btn = Button(WIDTH // 2 + 140, btn_y, btn_w, btn_h, "Joystick", (32, 120, 150), BLUE)

    kb_training_btn.draw()
    gest_training_btn.draw()
    joy_training_btn.draw()

    info_panel = pygame.Rect(220, 270, 840, 300)
    pygame.draw.rect(screen, (18, 26, 50), info_panel, border_radius=12)
    pygame.draw.rect(screen, current_theme()["accent"], info_panel, 1, border_radius=12)

    if control_mode == "keyboard":
        draw_text("KEYBOARD CONTROLS", font_mid, CYAN, 250, 290)
        draw_text("A / Left Arrow  -> Move Left", font_body, WHITE, 270, 325)
        draw_text("D / Right Arrow -> Move Right", font_body, WHITE, 270, 355)
        draw_text("W / Up Arrow / Space -> Jump", font_body, CYAN, 270, 385)
        draw_text("F -> Attack", font_body, RED, 270, 415)
        draw_text("E -> Shield", font_body, CYAN, 270, 445)
        draw_text("Shift -> Dash", font_body, PURPLE, 270, 475)
        draw_text("Tip: Hold keys for continuous action", font_small, MUTED, 270, 510)

    elif control_mode == "gesture":
        draw_text("GESTURE CONTROLS", font_mid, PURPLE, 250, 290)
        draw_text("RIGHT HAND (Movement):", font_body, BLUE, 270, 320)
        draw_text("  Index finger only -> Move Right", font_small, WHITE, 290, 345)
        draw_text("  Index + Middle -> Move Left", font_small, WHITE, 290, 370)
        draw_text("  Thumb pointing up -> Jump", font_small, CYAN, 290, 395)
        draw_text("LEFT HAND (Actions):", font_body, PURPLE, 580, 320)
        draw_text("  Closed fist -> Attack", font_small, RED, 600, 345)
        draw_text("  Open palm -> Shield", font_small, CYAN, 600, 370)
        draw_text("  Two fingers -> Dash", font_small, PURPLE, 600, 395)
        draw_text("Press G to toggle control modes", font_small, MUTED, 270, 440)

    elif control_mode == "joystick":
        draw_text("JOYSTICK CONTROLS", font_mid, BLUE, 250, 290)
        draw_text("Left side joystick:", font_body, WHITE, 270, 325)
        draw_text("  Drag left/right -> Move player", font_small, WHITE, 290, 355)
        draw_text("Right side buttons:", font_body, WHITE, 270, 390)
        draw_text("  JUMP -> Jump", font_small, CYAN, 290, 420)
        draw_text("  ATK -> Attack", font_small, RED, 290, 445)
        draw_text("  SHLD -> Shield", font_small, BLUE, 290, 470)
        draw_text("Works with mouse drag or touchscreen.", font_small, MUTED, 270, 510)

    if control_mode == "gesture":
        draw_text(gesture_status, font_small, current_theme()["accent"], 240, 540)
        if camera_frame is not None:
            pygame.draw.rect(screen, (8, 13, 31), (880, 525, 180, 120), border_radius=8)
            screen.blit(camera_frame, (885, 530))
    elif control_mode == "joystick":
        draw_text("Mode: Joystick - left stick + right buttons", font_small, BLUE, 240, 540)
    else:
        draw_text("Mode: Keyboard - Use keys to play", font_small, MUTED, 240, 540)

    back_button.draw()


reset_level(1)
running = True
level_cards = []

while running:
    clock.tick(FPS)

    if hit_stop > 0:
        hit_stop -= 1
        pygame.display.flip()
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        handle_joystick_event(event)

        if state == "menu":
            if menu_buttons[0].clicked(event):
                play(SND_MENU)
                reset_level(unlocked_level)
                state = "duel"
            if menu_buttons[1].clicked(event):
                play(SND_MENU)
                state = "level_select"
            if menu_buttons[2].clicked(event):
                play(SND_MENU)
                state = "online"
            if menu_buttons[3].clicked(event):
                play(SND_MENU)
                state = "training"
            if menu_buttons[4].clicked(event):
                running = False

        elif state == "level_select":
            if back_button.clicked(event):
                play(SND_MENU)
                state = "menu"
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, level_num, locked in level_cards:
                    if rect.collidepoint(event.pos) and not locked:
                        play(SND_MENU)
                        reset_level(level_num)
                        state = "duel"

        elif state == "training":
            if back_button.clicked(event):
                play(SND_MENU)
                state = "menu"

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()

                if kb_training_btn and kb_training_btn.rect.collidepoint(mouse):
                    play(SND_MENU)
                    control_mode = "keyboard"
                    gesture_controller.stop()
                    gesture_enabled = False
                    joystick_enabled = False
                    reset_joystick_buttons()
                    message = "Control mode: Keyboard"

                elif gest_training_btn and gest_training_btn.rect.collidepoint(mouse):
                    play(SND_MENU)
                    control_mode = "gesture"
                    gesture_controller.start()
                    gesture_enabled = True
                    joystick_enabled = False
                    reset_joystick_buttons()
                    message = "Control mode: Gestures"

                elif joy_training_btn and joy_training_btn.rect.collidepoint(mouse):
                    play(SND_MENU)
                    control_mode = "joystick"
                    gesture_controller.stop()
                    gesture_enabled = False
                    joystick_enabled = True
                    message = "Control mode: Joystick"

        else:
            if back_button.clicked(event):
                play(SND_MENU)
                state = "menu"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                if control_mode == "keyboard":
                    control_mode = "gesture"
                    gesture_controller.start()
                    gesture_enabled = True
                    joystick_enabled = False
                    reset_joystick_buttons()
                    message = "Gesture mode ON"

                elif control_mode == "gesture":
                    control_mode = "joystick"
                    gesture_controller.stop()
                    gesture_enabled = False
                    joystick_enabled = True
                    message = "Joystick mode ON"

                else:
                    control_mode = "keyboard"
                    gesture_controller.stop()
                    gesture_enabled = False
                    joystick_enabled = False
                    reset_joystick_buttons()
                    message = "Keyboard mode"

                play(SND_MENU)

            if event.key == pygame.K_ESCAPE:
                state = "menu"

            if state == "duel":
                if event.key == pygame.K_r:
                    reset_level(current_level)
                if event.key == pygame.K_n and level_over and level_result == "LEVEL COMPLETE":
                    if current_level < 20:
                        reset_level(current_level + 1)
                    else:
                        state = "level_select"

    keys = pygame.key.get_pressed()

    if state == "menu":
        draw_menu()
    elif state == "level_select":
        level_cards = draw_level_select()
    elif state == "duel":
        update_duel(keys)
        draw_duel()
    elif state == "online":
        draw_placeholder("Online Lobby", [
            "Coming soon: Host lobby with code",
            "Friend joins using same code",
            "Real-time multiplayer sync + chat",
        ])
    elif state == "training":
        draw_training_screen()

    pygame.display.flip()

gesture_controller.stop()
pygame.quit()
sys.exit()