# 🟦 Flatopia: The Open Source Sitcom Generator

**Turn text into fully animated, voiced, geometric sitcom episodes.**

Flatopia is a Python-based animation engine that uses **Manim**, **Streamlit**, and **pyttsx3** to generate 2D cartoons. You write the script, and the engine handles the casting, voice acting, animation, and editing.

---

## ✨ Features

* **Script-to-Video:** Paste a text script, get an MP4.
* **Auto-Voicing:** Automatically generates distinct voices for different characters.
* **Smart Casting:** Define character shapes (Stars, Hexagons, Triangles) and colors via config tags.
* **Scene Management:** Instantly switch backgrounds using the "Flatopia Color Legend."
* **Built-in SFX:** Includes Laugh tracks, Boos, Claps, and awkward Crickets.
* **Robust Rendering:** Handles asset downloads and fallback error checking.

---

## 🛠️ Installation

### 1. Prerequisites
You need **FFMPEG** installed on your system for Manim to render video.
* [Download FFMPEG here](https://ffmpeg.org/download.html)
* Make sure FFMPEG is added to your system PATH.

### 2. Clone and Install
```bash
git clone [https://github.com/yourusername/flatopia.git](https://github.com/yourusername/flatopia.git)
cd flatopia
pip install -r requirements.txt
