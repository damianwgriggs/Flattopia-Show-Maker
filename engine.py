# engine.py
from manim import *
import pyttsx3
import json
import os
import urllib.request
import sys
import shutil

# Force unbuffered output
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")
SFX_DIR = os.path.join(BASE_DIR, "sfx")

def setup_directories():
    if not os.path.exists(AUDIO_DIR): os.makedirs(AUDIO_DIR)
    if not os.path.exists(SFX_DIR): os.makedirs(SFX_DIR)

setup_directories()

# ==========================================
# 1. ROBUST DOWNLOADER + FALLBACK GENERATOR
# ==========================================
def generate_fallback_sfx(filepath, phrase):
    """If download fails, the robot will speak the SFX"""
    print(f"[SETUP] Generating fallback SFX for {filepath}")
    try:
        aux_engine = pyttsx3.init()
        aux_engine.setProperty('rate', 200) 
        aux_engine.save_to_file(phrase, filepath)
        aux_engine.runAndWait()
        del aux_engine
    except Exception as e:
        print(f"[ERROR] Fallback generation failed: {e}")

def download_file(url, filepath, fallback_phrase):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    
    try:
        print(f"[SETUP] Downloading SFX: {filepath}")
        urllib.request.urlretrieve(url, filepath)
        return True
    except Exception as e:
        print(f"[WARN] Download failed ({e}). Creating fallback sound.")
        generate_fallback_sfx(filepath, fallback_phrase)
        return False

def ensure_sfx_exist():
    # URL, Fallback Text
    assets = {
        "laugh.wav": ("https://invalid-url-force-fallback.com", "Hahahaha. Hahahaha."), 
        "boo.wav": ("https://invalid-url-force-fallback.com", "Booooo. Booooo."),
        "clap.wav": ("https://invalid-url-force-fallback.com", "Clap clap clap clap."),
        "cricket.wav": ("https://invalid-url-force-fallback.com", "Chirp. Chirp.")
    }

    # I have intentionally set bad URLs above to force the fallback 
    # so you definitely hear sound this time.
    
    for filename, (url, phrase) in assets.items():
        filepath = os.path.join(SFX_DIR, filename)
        # Check if file exists and is valid
        if not os.path.exists(filepath) or os.path.getsize(filepath) < 1000:
            download_file(url, filepath, phrase)

# ==========================================
# 2. AUDIO PRE-GENERATION
# ==========================================
def pre_render_voice_lines():
    print("[SETUP] Pre-rendering voice lines...")
    try:
        with open("temp_script.json", "r") as f:
            script_data = json.load(f)
            
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        voices = engine.getProperty('voices')
        
        for i, item in enumerate(script_data):
            text = item["text"]
            speaker = item["speaker"].upper()
            
            if text.startswith("[") and text.endswith("]"): continue
                
            audio_path = os.path.join(AUDIO_DIR, f"line_{i}.wav")
            
            if "CARL" in speaker and len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            else:
                engine.setProperty('voice', voices[0].id)
                
            engine.save_to_file(text, audio_path)
            
        engine.runAndWait()
        print("[SETUP] Audio generation complete.")
        return True
    except Exception as e:
        print(f"[ERROR] Audio Generation Failed: {e}")
        return False

# RUN SETUP
ensure_sfx_exist()
pre_render_voice_lines()

# ==========================================
# 3. MANIM SCENE
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
        self.camera.background_color = "#111111" 
        with open("temp_script.json", "r") as f:
            script_data = json.load(f)

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

        for i, item in enumerate(script_data):
            speaker = item["speaker"].upper()
            text = item["text"]
            
            clean_text = text.strip()
            if clean_text.startswith("[") and clean_text.endswith("]"):
                tag = clean_text[1:-1].upper()
                if tag in SFX_MAP:
                    filename, duration = SFX_MAP[tag]
                    print(f"[ACTION] Playing SFX: {tag}")
                    self.add_sound(filename)
                    self.wait(duration)
                    continue 

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

            audio_filename = f"line_{i}.wav"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            
            if os.path.exists(audio_path):
                self.add_sound(audio_path)

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
