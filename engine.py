# engine.py
from manim import *
import pyttsx3
import json
import os
import urllib.request
import sys
import shutil

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 0. DIRECTORY SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")
SFX_DIR = os.path.join(BASE_DIR, "sfx")

def setup_directories():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
    if not os.path.exists(SFX_DIR):
        os.makedirs(SFX_DIR)

setup_directories()

# ==========================================
# 1. ROBUST DOWNLOADER
# ==========================================
def download_file(url, filepath):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        print(f"[SETUP] Downloading SFX: {filepath}")
        urllib.request.urlretrieve(url, filepath)
        return True
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False

def ensure_sfx_exist():
    urls = {
        "laugh.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/e/ee/Laugh_track_-_Audience_laughter.ogg/Laugh_track_-_Audience_laughter.ogg.mp3",
        "boo.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/3/3b/Crowd_Boo.wav/Crowd_Boo.wav.mp3",
        "clap.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/6/62/Applause_-_enthusiastic.ogg/Applause_-_enthusiastic.ogg.mp3",
        "cricket.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/e/e9/Crickets_chirping.ogg/Crickets_chirping.ogg.mp3"
    }
    for filename, url in urls.items():
        filepath = os.path.join(SFX_DIR, filename)
        if not os.path.exists(filepath) or os.path.getsize(filepath) < 100:
            download_file(url, filepath)

# ==========================================
# 2. AUDIO PRE-GENERATION (THE FIX)
# ==========================================
def pre_render_voice_lines():
    """Generates all .wav files BEFORE Manim starts to prevent crashing."""
    print("[SETUP] Pre-rendering voice lines...")
    
    try:
        with open("temp_script.json", "r") as f:
            script_data = json.load(f)
            
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        voices = engine.getProperty('voices')
        
        # Queue up ALL lines at once
        for i, item in enumerate(script_data):
            text = item["text"]
            speaker = item["speaker"].upper()
            
            # Skip SFX lines
            if text.startswith("[") and text.endswith("]"):
                continue
                
            audio_path = os.path.join(AUDIO_DIR, f"line_{i}.wav")
            
            # Set voice based on speaker
            if "CARL" in speaker and len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            else:
                engine.setProperty('voice', voices[0].id)
                
            print(f"[SETUP] Queuing Audio: {text[:20]}...")
            engine.save_to_file(text, audio_path)
            
        # Run the engine ONCE for the whole batch
        print("[SETUP] Processing Audio Queue...")
        engine.runAndWait()
        print("[SETUP] Audio generation complete.")
        return True
        
    except Exception as e:
        print(f"[ERROR] Audio Generation Failed: {e}")
        return False

# RUN SETUP TASKS NOW
ensure_sfx_exist()
pre_render_voice_lines()

# ==========================================
# 3. MANIM SCENE (PURE ANIMATION ONLY)
# ==========================================
SFX_MAP = {
    "LAUGH":   (os.path.join(SFX_DIR, "laugh.wav"), 4),
    "BOO":     (os.path.join(SFX_DIR, "boo.wav"), 3),
    "CLAP":    (os.path.join(SFX_DIR, "clap.wav"), 5),
    "CRICKET": (os.path.join(SFX_DIR, "cricket.wav"), 2),
    "SILENCE": (None, 2)
}

class FlatlandEpisode(MovingCameraScene):
    def construct(self):
        print("[ACTION] Scene Started. Using pre-rendered audio.")
        self.camera.background_color = "#111111" 

        with open("temp_script.json", "r") as f:
            script_data = json.load(f)

        # Build Cast
        barry = VGroup(
            Square(color=RED, fill_opacity=1).scale(1.5),
            Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.5 + LEFT*0.4), 
            Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.5 + RIGHT*0.4),
            Dot(color=BLACK, radius=0.12).shift(UP*0.5 + LEFT*0.4), 
            Dot(color=BLACK, radius=0.12).shift(UP*0.5 + RIGHT*0.4) 
        ).shift(LEFT * 3)

        carl = VGroup(
            Circle(color=BLUE, fill_opacity=1).scale(1.5),
            Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.5 + LEFT*0.4),
            Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.5 + RIGHT*0.4),
            Dot(color=BLACK, radius=0.12).shift(UP*0.5 + LEFT*0.4),
            Dot(color=BLACK, radius=0.12).shift(UP*0.5 + RIGHT*0.4)
        ).shift(RIGHT * 3)

        self.add(barry, carl)

        # Loop
        for i, item in enumerate(script_data):
            speaker = item["speaker"].upper()
            text = item["text"]
            
            # --- SFX LOGIC ---
            clean_text = text.strip()
            if clean_text.startswith("[") and clean_text.endswith("]"):
                tag = clean_text[1:-1].upper()
                if tag in SFX_MAP:
                    filename, duration = SFX_MAP[tag]
                    print(f"[ACTION] Playing SFX: {tag}")
                    if filename and os.path.exists(filename):
                        self.add_sound(filename)
                    self.wait(duration)
                    continue 

            # --- CAMERA LOGIC ---
            target_frame = self.camera.frame
            if "BARRY" in speaker:
                actor = barry
                self.play(target_frame.animate.scale_to_fit_height(8).move_to(barry), run_time=0.5)
            elif "CARL" in speaker:
                actor = carl
                self.play(target_frame.animate.scale_to_fit_height(8).move_to(carl), run_time=0.5)
            else:
                actor = VGroup(barry, carl)
                self.play(target_frame.animate.scale_to_fit_height(14).move_to(ORIGIN), run_time=0.5)

            # --- TALK LOGIC (NO GENERATION, JUST PLAYBACK) ---
            audio_filename = f"line_{i}.wav"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            
            print(f"[ACTION] Playing Audio: {audio_filename}")
            if os.path.exists(audio_path):
                self.add_sound(audio_path)
            else:
                print(f"[WARN] Audio file missing: {audio_path}")

            # Calculate duration based on text length since we can't easily check wav duration in Manim without extra libs
            duration = max(1.5, len(text) / 14)

            self.play(
                ApplyMethod(actor.shift, UP * 0.5),
                run_time=0.25,
                rate_func=there_and_back
            )
            
            remaining_time = duration - 0.25
            if remaining_time > 0:
                self.wait(remaining_time)
        
        self.play(FadeOut(barry), FadeOut(carl), run_time=2)

if __name__ == "__main__":
    sys.exit(0)
