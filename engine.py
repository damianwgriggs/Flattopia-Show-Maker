# engine.py
from manim import *
import pyttsx3
import json
import os
import urllib.request
import sys
import shutil

# ==========================================
# 0. DIRECTORY SETUP
# ==========================================
# Absolute paths to prevent confusion
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
# 1. ROBUST DOWNLOADER (Skips if fails)
# ==========================================
def download_file(url, filepath):
    # Fake a browser to bypass 403 errors
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
    urllib.request.install_opener(opener)
    
    try:
        print(f"Attempting download: {filepath}")
        urllib.request.urlretrieve(url, filepath)
        print(" -> Success")
        return True
    except Exception as e:
        print(f" -> Failed to download {filepath}. Error: {e}")
        return False

def ensure_sfx_exist():
    # Public domain sounds
    urls = {
        "laugh.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/e/ee/Laugh_track_-_Audience_laughter.ogg/Laugh_track_-_Audience_laughter.ogg.mp3",
        "boo.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/3/3b/Crowd_Boo.wav/Crowd_Boo.wav.mp3",
        "clap.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/6/62/Applause_-_enthusiastic.ogg/Applause_-_enthusiastic.ogg.mp3",
        "cricket.wav": "https://upload.wikimedia.org/wikipedia/commons/transcoded/e/e9/Crickets_chirping.ogg/Crickets_chirping.ogg.mp3"
    }

    for filename, url in urls.items():
        filepath = os.path.join(SFX_DIR, filename)
        if not os.path.exists(filepath):
            download_file(url, filepath)

ensure_sfx_exist()

# ==========================================
# 2. SOUND EFFECT MAPPING
# ==========================================
SFX_MAP = {
    "LAUGH":   (os.path.join(SFX_DIR, "laugh.wav"), 4),
    "BOO":     (os.path.join(SFX_DIR, "boo.wav"), 3),
    "CLAP":    (os.path.join(SFX_DIR, "clap.wav"), 5),
    "CRICKET": (os.path.join(SFX_DIR, "cricket.wav"), 2),
    "SILENCE": (None, 2)
}

# ==========================================
# 3. THE MOVIE ENGINE
# ==========================================
class FlatlandEpisode(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#111111" 
        
        # Initialize Voice Engine Safe Mode
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 165)
            voices = engine.getProperty('voices')
            voice_engine_working = True
        except Exception as e:
            print(f"CRITICAL WARNING: Voice engine failed: {e}")
            voice_engine_working = False

        # Load Script
        with open("temp_script.json", "r") as f:
            script_data = json.load(f)

        # --- CAST BUILD ---
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

        # --- EXECUTION LOOP ---
        for i, item in enumerate(script_data):
            speaker = item["speaker"].upper()
            text = item["text"]
            
            # 1. SFX CHECK
            clean_text = text.strip()
            if clean_text.startswith("[") and clean_text.endswith("]"):
                tag = clean_text[1:-1].upper()
                if tag in SFX_MAP:
                    filename, duration = SFX_MAP[tag]
                    # Only play if file actually exists and downloaded correctly
                    if filename and os.path.exists(filename):
                        self.add_sound(filename)
                    self.wait(duration)
                    continue 

            # 2. CAMERA LOGIC
            target_frame = self.camera.frame
            if "BARRY" in speaker:
                actor = barry
                if voice_engine_working: engine.setProperty('voice', voices[0].id)
                self.play(target_frame.animate.scale_to_fit_height(8).move_to(barry), run_time=0.5)
            elif "CARL" in speaker:
                actor = carl
                if voice_engine_working and len(voices) > 1: engine.setProperty('voice', voices[1].id)
                self.play(target_frame.animate.scale_to_fit_height(8).move_to(carl), run_time=0.5)
            else:
                actor = VGroup(barry, carl)
                self.play(target_frame.animate.scale_to_fit_height(14).move_to(ORIGIN), run_time=0.5)

            # 3. TALKING LOGIC
            audio_filename = f"line_{i}.wav"
            # Save to the TEMP folder, not the root
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            
            # Generate Audio
            if voice_engine_working:
                try:
                    engine.save_to_file(text, audio_path)
                    engine.runAndWait()
                except:
                    print(f"Warning: Could not save audio for line {i}")
            
            # Calculate Duration
            duration = max(1.5, len(text) / 14)
            
            # Play Sound & Animation
            if os.path.exists(audio_path):
                self.add_sound(audio_path)
                
            self.play(
                ApplyMethod(actor.shift, UP * 0.5),
                run_time=0.25,
                rate_func=there_and_back
            )
            
            remaining_time = duration - 0.25
            if remaining_time > 0:
                self.wait(remaining_time)
        
        # 4. CLEANUP
        self.play(FadeOut(barry), FadeOut(carl), run_time=2)

if __name__ == "__main__":
    sys.exit(0)
