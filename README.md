# 🗡️ StickForce AI: Gesture Battle Arena

**StickForce AI** is a fast-paced, neon-themed 2D stick-figure fighting game built entirely in Python using Pygame. What makes this game unique is its **zero-asset architecture** (all graphics and audio are procedurally generated via code) and its advanced **Computer Vision control system** allowing you to fight using real-time hand gestures via your webcam!

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-CE-orange?logo=pygame)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Computer_Vision-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🎮 Gameplay
* **20 Unique Levels:** Progress through increasingly difficult arenas with different color themes.
* **Smart AI Rival:** Fight against an AI that adapts its speed, damage, and aggression based on the level.
* **Dynamic Arenas:** Navigate platforms, avoid spikes, and dodge laser hazards in later levels.
* **Combat Mechanics:** Master attacks, shields, dashes, and chain hits for combo multipliers.
* **Progression System:** Earn up to 3 stars per level based on your health and completion time.

### 🕹️ Triple Control System
Switch between three control methods on the fly by pressing **`G`**:
1. **Keyboard:** Classic WASD/Arrow keys + Action keys.
2. **Virtual Joystick:** Touch/Mouse-friendly on-screen joystick and buttons.
3. **Gesture Control (MediaPipe):** Use your webcam! 
   * *Right Hand:* Controls movement and jumping.
   * *Left Hand:* Controls attacks, shields, and dashes.

### 🎨 Technical Highlights
* **100% Procedural Assets:** No external `.png` or `.wav` files needed. All visuals (neon glows, particles, stick figures) and audio (SFX and background music) are generated mathematically using `NumPy` and `Pygame`.
* **Game Feel:** Includes screen shake, hit-stop (freeze frames on impact), particle bursts, and glowing trails.
* **Real-time CV:** Multi-threaded webcam processing using Google's MediaPipe for low-latency hand tracking.

---

## 📦 Installation & Requirements

### Prerequisites
Make sure you have Python 3.8 or higher installed. You will also need a webcam if you want to use the Gesture Control mode.

### 1. Clone the Repository
```bash
git clone https://github.com/YourUsername/StickForce-AI.git
cd StickForce-AI
