I'll create a professional GitHub README for your **StickForce AI - Gesture Battle Arena** game. Let me write this directly since I have all the code details from your upload.

---

# StickForce AI — Gesture Battle Arena

**A neon-soaked, gesture-controlled stick-fighter platformer with 20 levels, AI rivals, and three control modes.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.x-green.svg)](https://pygame.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange.svg)](https://mediapipe.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red.svg)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![Game Screenshot](assets/screenshot.png)

---

## Overview

StickForce AI is a fast-paced 2D fighting platformer where you battle AI rivals across **20 themed levels** with escalating difficulty. What sets it apart is its **multi-modal control system** — play with traditional keyboard, **hand gestures via webcam**, or an on-screen **virtual joystick**.

The game features a custom-built physics engine, procedural audio synthesis, dynamic theming, particle effects, screen shake, hit-stop frames, and a full star-rating progression system.

---

## Features

| Feature | Description |
|---------|-------------|
| **20 Unique Levels** | Themed arenas from *Neon Gate* to *Omega Arena* with progressive hazards |
| **3 Control Modes** | Keyboard, Hand Gestures (MediaPipe), Touchscreen Joystick |
| **Gesture Recognition** | Real-time hand tracking — right hand moves, left hand acts |
| **AI Opponents** | Adaptive AI with dodging, shielding, and dash mechanics |
| **Dynamic Audio** | Procedurally generated SFX and background music |
| **Visual Effects** | Neon glows, particle bursts, screen shake, hit-stop, motion trails |
| **Progression System** | 1-3 star ratings per level, unlock system, score tracking |
| **Hazards** | Spikes and lasers introduced from Level 3 onwards |
| **Energy Orbs** | Collectible orbs for energy regeneration and bonus score |

---

## Controls

### Keyboard (Default)
| Key | Action |
|-----|--------|
| `A` / `←` | Move Left |
| `D` / `→` | Move Right |
| `W` / `↑` / `Space` | Jump |
| `F` | Attack |
| `E` | Shield |
| `Shift` | Dash |
| `G` | Toggle Control Mode |
| `R` | Retry Level |
| `N` | Next Level (after victory) |
| `Esc` | Return to Menu |

### Gesture Mode (Webcam Required)
| Hand | Gesture | Action |
|------|---------|--------|
| **Right Hand** | Index finger only | Move Right |
| **Right Hand** | Index + Middle finger | Move Left |
| **Right Hand** | Thumb pointing up | Jump |
| **Left Hand** | Closed fist (≤1 finger) | Attack |
| **Left Hand** | Open palm (≥4 fingers) | Shield |
| **Left Hand** | Two fingers | Dash |

> Press **G** to cycle through Keyboard → Gesture → Joystick modes.

### Joystick Mode (Touch/Mouse)
- **Left Side**: Drag virtual stick to move
- **Right Side**: Tap JUMP, ATK, or SHLD buttons

---

## Installation

### Prerequisites
- Python 3.8+
- Webcam (for gesture mode)

### Dependencies
```bash
pip install pygame numpy opencv-python mediapipe
```

### Run the Game
```bash
git clone https://github.com/yourusername/stickforce-ai.git
cd stickforce-ai
python stickforce.py
```

---

## Project Structure

```
stickforce-ai/
├── stickforce.py          # Main game file (single-file architecture)
├── assets/
│   └── screenshot.png     # Gameplay preview
├── README.md
└── LICENSE
```

> The game is intentionally built as a **single Python file** for easy distribution and hackability.

---

## Game Mechanics

### Combat System
- **Attack**: Sword swing with hit detection based on facing direction and proximity
- **Shield**: Reduces incoming damage to 3 HP, drains energy
- **Dash**: High-speed burst costing 18 energy
- **Combo System**: Chain hits for score multipliers

### Level Progression
- **Stars**: Earn 1-3 stars based on health remaining and completion time
- **Unlocks**: Complete a level to unlock the next
- **Hazards**: Spikes (Level 3+) and lasers (Level 9+) add environmental danger
- **AI Scaling**: Enemy speed and damage increase with each level

### Energy System
- Energy regenerates slowly over time
- Collect **yellow orbs** for +24 energy and +6 score
- Shield and Dash consume energy

---

## Technical Highlights

| System | Implementation |
|--------|----------------|
| **Physics** | Custom gravity, friction, collision resolution with platforms |
| **Audio** | NumPy-based procedural synthesis (square, sine, noise waves) |
| **Rendering** | Pygame with additive blending, alpha surfaces, gradient rectangles |
| **Gesture Pipeline** | MediaPipe Hands → finger counting → action mapping |
| **AI Behavior** | Distance-based state machine with randomized decisions |
| **Visual Polish** | Screen shake, hit-stop frames, motion trails, neon glows |

---

## Screenshots

### Main Menu
*Neon-themed menu with animated background and demo fighters*

### Gesture Mode
*Live webcam preview with hand landmark overlay and command feedback*

### Level Select
*20 themed cards with star ratings and lock states*

---

## Roadmap

- [x] 20-level single-player campaign
- [x] Gesture control integration
- [x] Joystick/touch controls
- [x] Procedural audio system
- [ ] **Online Multiplayer** (In Progress — lobby system planned)
- [ ] Additional characters with unique abilities
- [ ] Mobile deployment (Android/iOS)

---

## Contributing

Contributions welcome! Areas of interest:
- Mobile/touch optimization
- Additional gesture commands
- Multiplayer networking
- Level editor

Please open an issue or submit a pull request.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

- **Engine**: Pygame
- **Computer Vision**: Google MediaPipe
- **Audio Synthesis**: NumPy
- **Font**: Segoe UI (system font fallback)

---

**Made with neon, code, and caffeine.**

---
