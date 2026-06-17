# 🗡️ StickForce AI: Gesture Battle Arena

A fast-paced, neon-themed 2D stick-figure fighting game built entirely in **Python** using **Pygame**. This application is unique due to its **zero-asset architecture** (all graphics and audio are procedurally generated via code) and its advanced **Computer Vision control system**, allowing players to fight using real-time hand gestures via their webcam!

---

## 🚀 Key Features

### 🎮 Gameplay
* **20 Unique Levels:** Progress through increasingly difficult arenas with different neon color themes.
* **Smart AI Rival:** Fight against an AI that adapts its speed, damage, and aggression based on the level.
* **Dynamic Arenas:** Navigate platforms, avoid spikes, and dodge laser hazards in later levels.
* **Combat Mechanics:** Master attacks, shields, dashes, and chain hits for combo multipliers.
* **Progression System:** Earn up to 3 stars per level based on your remaining health and completion time.

### 🕹️ Triple Control System
Switch between three control methods on the fly by pressing **`G`**:
1. **Keyboard:** Classic WASD/Arrow keys + Action keys.
2. **Virtual Joystick:** Touch/Mouse-friendly on-screen joystick and buttons.
3. **Gesture Control (MediaPipe):** Use your webcam!
   * *Right Hand:* Controls movement and jumping.
   * *Left Hand:* Controls attacks, shields, and dashes.

### 🎨 Technical Highlights
* **100% Procedural Assets:** No external `.png` or `.wav` files needed. All visuals (neon glows, particles, stick figures) and audio (SFX and background music) are generated mathematically using `NumPy` and `Pygame`.
* **Juicy Game Feel:** Includes screen shake, hit-stop (freeze frames on impact), particle bursts, and glowing trails.
* **Real-time CV:** Multi-threaded webcam processing using Google's MediaPipe for low-latency hand tracking without dropping frames.

---

## 🛠️ Technologies Used

| Technology | Purpose |
| :--- | :--- |
| **Python** | Core Programming Language |
| **Pygame** | Game Engine & GUI Rendering |
| **NumPy** | Procedural Audio & Math Calculations |
| **OpenCV** | Webcam Capture & Image Processing |
| **MediaPipe** | Real-time Hand Gesture Tracking |
| **Threading** | Non-blocking Computer Vision Loop |

---

## 📂 Project Modules / Features
1. 🏠 **Main Menu** – Continue, Level Select, Online Lobby, AI Training, Exit
2. 🗺️ **Level Select** – 20 unique levels with star progression system
3. ⚔️ **Duel Mode** – Real-time combat against AI with HUD, combos, and hazards
4. 🖐️ **Gesture Training** – Live webcam preview with hand landmark visualization
5. 🕹️ **Joystick Mode** – On-screen touch/mouse controls for mobile-friendly play
6. 🌐 **Online Lobby** – Placeholder for future multiplayer integration
7. 🎵 **Procedural Audio Engine** – Dynamically generated SFX and background music

---

## 🎮 How to Play

### Default Controls (Keyboard)
| Action | Key |
| :--- | :--- |
| **Move** | `A` / `D` or `Left` / `Right` Arrows |
| **Jump** | `W`, `Up Arrow`, or `Space` |
| **Attack** | `F` |
| **Shield** | `E` |
| **Dash** | `Left Shift` or `Right Shift` |
| **Toggle Control Mode** | `G` |
| **Retry Level** | `R` |
| **Next Level** | `N` (After winning) |
| **Back to Menu** | `Esc` |

### 🖐️ Gesture Controls (Press 'G' to enable)
*Stand in front of your webcam. The game mirrors the feed for a natural mirror effect.*

**Right Hand (Movement):**
* ☝️ **Index finger only:** Move Right
* ✌️ **Index + Middle fingers:** Move Left
* 👍 **Thumb pointing up:** Jump

**Left Hand (Actions):**
* ✊ **Closed fist (0-1 fingers):** Attack
* 🖐️ **Open palm (4+ fingers):** Shield
* ✌️ **Two fingers:** Dash

---

## ⚙️ Installation & Setup

### Prerequisites
* **Python 3.8 or higher**
* A working **webcam** (for Gesture Control mode)
* **pip** package manager

### Steps to Run
1. **Clone the repository:**
   git clone https://github.com/your-username/StickForce-AI.git
   cd StickForce-AI

2. **Install dependencies:**
   pip install pygame opencv-python mediapipe numpy

3. **Run the game:**
   python stickforce_ai.py

*(Note: Apple Silicon M1/M2/M3 users may need to install `mediapipe-silicon` or use a Rosetta virtual environment.)*

---

## 🎯 Future Enhancements
* [ ] Local 2-player split-screen mode
* [ ] Online multiplayer lobby using WebSockets/WebRTC
* [ ] More complex AI behaviors (parrying, dodging, blocking)
* [ ] Epic Boss Fight at Level 20
* [ ] Mobile touch-swipe gesture support
* [ ] Custom character skins and weapon unlocks
* [ ] Leaderboard and cloud save system

---

## 🧠 Technical Architecture
* **Procedural Audio Engine:** The `make_sound()` and `make_music()` functions use `numpy` to generate sine/square waves and noise, applying ADSR envelopes to create retro-sounding SFX and a looping background track without loading a single audio file.
* **Multithreading:** The `GestureController` runs OpenCV and MediaPipe on a separate daemon thread to ensure the Pygame main loop maintains a stable 60 FPS.
* **State Machine:** The game uses a clean state manager (`menu`, `level_select`, `duel`, `training`, `online`) to handle transitions and UI rendering seamlessly.
* **Object-Oriented Design:** Clean separation of `Fighter`, `Platform`, `Hazard`, and `FX` classes for easy modification and expansion.

---

## 👨‍💻 Developer
Developed as a creative project using **Python**, **Pygame**, and **MediaPipe** to demonstrate real-time computer vision integration, procedural content generation, and advanced game development concepts in a single-file, zero-asset application.

---

## 📜 License
This project is developed for **educational and learning purposes**. Feel free to fork, modify, and use it for your own projects or game jams!
