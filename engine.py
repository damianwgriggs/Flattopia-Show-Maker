# engine.py (SMART VERSION)
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
# 1. ROBUST DOWNLOADER + FALLBACK
# ==========================================
def generate_fallback_sfx(filepath, phrase):
    try:
        aux_engine = pyttsx3.init()
        aux_engine.setProperty('rate', 200) 
        aux_engine.save_to_file(phrase, filepath)
        aux_engine.runAndWait()
        del aux_engine
    except: pass

def download_file(url, filepath, fallback_phrase):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        print(f"[SETUP] Downloading SFX: {filepath}")
        urllib.request.urlretrieve(url, filepath)
        return True
    except:
        generate_fallback_sfx(filepath, fallback_phrase)
        return False

def ensure_sfx_exist():
    assets = {
        "laugh.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/e/ee/Laugh_track_-_Audience_laughter.ogg/Laugh_track_-_Audience_laughter.ogg.mp3", "Hahahaha."), 
        "boo.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/3/3b/Crowd_Boo.wav/Crowd_Boo.wav.mp3", "Booooo."),
        "clap.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/6/62/Applause_-_enthusiastic.ogg/Applause_-_enthusiastic.ogg.mp3", "Clap clap clap."),
        "cricket.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/e/e9/Crickets_chirping.ogg/Crickets_chirping.ogg.mp3", "Chirp.")
    }
    for filename, (url, phrase) in assets.items():
        filepath = os.path.join(SFX_DIR, filename)
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
            
            # Skip special tags
            if text.startswith("[") and text.endswith("]"): continue
                
            audio_path = os.path.join(AUDIO_DIR, f"line_{i}.wav")
            
            if "CARL" in speaker and len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            else:
                engine.setProperty('voice', voices[0].id)
                
            engine.save_to_file(text, audio_path)
            
        engine.runAndWait()
        print("[SETUP] Audio complete.")
        return True
    except:
        return False

ensure_sfx_exist()
pre_render_voice_lines()

# ==========================================
# 3. THE SHAPE FACTORY (NEW!)
# ==========================================
def get_manim_color(color_name):
    # Default to WHITE if color not found
    try:
        return getattr(sys.modules["manim"], color_name.upper())
    except:
        return WHITE

def create_actor_shape(shape_name, color_name):
    """Builds a VGroup based on text input"""
    color = get_manim_color(color_name)
    shape_name = shape_name.upper()

    # Define the body
    if shape_name == "CIRCLE":
        body = Circle(color=color, fill_opacity=1).scale(1.5)
    elif shape_name == "TRIANGLE":
        body = Triangle(color=color, fill_opacity=1).scale(2.0).shift(DOWN*0.3)
    elif shape_name == "STAR":
        body = Star(color=color, fill_opacity=1).scale(1.8)
    elif shape_name == "HEXAGON":
        body = RegularPolygon(n=6, color=color, fill_opacity=1).scale(1.5)
    else: # Default to SQUARE
        body = Square(color=color, fill_opacity=1).scale(1.5)

    # Eyes (Positioned generically to fit most shapes)
    eye_l = Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.4 + LEFT*0.4)
    eye_r = Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.4 + RIGHT*0.4)
    pupil_l = Dot(color=BLACK, radius=0.12).shift(UP*0.4 + LEFT*0.4)
    pupil_r = Dot(color=BLACK, radius=0.12).shift(UP*0.4 + RIGHT*0.4)

    return VGroup(body, eye_l, eye_r, pupil_l, pupil_r)

# ==========================================
# 4. MAIN SCENE
# ==========================================
SFX_MAP = {
    "LAUGH": (os.path.join(SFX_DIR, "laugh.wav"), 4),
    "BOO": (os.path.join(SFX_DIR, "boo.wav"), 3),
    "CLAP": (os.path.join(SFX_DIR, "clap.wav"), 5),
    "CRICKET": (os.path.join(SFX_DIR, "cricket.wav"), 2),
    "SILENCE": (None, 2)
}

class FlatlandEpisode(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#111111" 
        with open("temp_script.json", "r") as f:
            script_data = json.load(f)

        # --- STEP 1: PARSE CONFIGURATION ---
        # Defaults
        profile = {
            "BARRY": {"shape": "SQUARE", "color": "RED"},
            "CARL": {"shape": "CIRCLE", "color": "BLUE"}
        }

        # Scan script for [CONFIG: NAME, SHAPE, COLOR]
        for item in script_data:
            text = item["text"].strip()
            if text.startswith("[CONFIG:"):
                # Clean format: [CONFIG: BARRY, TRIANGLE, GREEN] -> "BARRY, TRIANGLE, GREEN"
                content = text.replace("[CONFIG:", "").replace("]", "")
                parts = [p.strip().upper() for p in content.split(",")]
                
                if len(parts) >= 3:
                    name, shape, color = parts[0], parts[1], parts[2]
                    profile[name] = {"shape": shape, "color": color}
                    print(f"[ACTION] Configured {name} as {color} {shape}")

        # --- STEP 2: BUILD ACTORS ---
        barry = create_actor_shape(profile["BARRY"]["shape"], profile["BARRY"]["color"])
        barry.shift(LEFT * 3)

        carl = create_actor_shape(profile["CARL"]["shape"], profile["CARL"]["color"])
        carl.shift(RIGHT * 3)

        self.add(barry, carl)

        # --- STEP 3: PLAY SCENE ---
        for i, item in enumerate(script_data):
            speaker = item["speaker"].upper()
            text = item["text"]
            
            clean_text = text.strip()
            
            # Skip Config lines so they don't break flow
            if clean_text.startswith("[CONFIG:"):
                continue

            # SFX Handler
            if clean_text.startswith("[") and clean_text.endswith("]"):
                tag = clean_text[1:-1].upper()
                if tag in SFX_MAP:
                    filename, duration = SFX_MAP[tag]
                    if filename and os.path.exists(filename): self.add_sound(filename)
                    self.wait(duration)
                    continue 

            # Camera Move
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

            # Audio
            audio_path = os.path.join(AUDIO_DIR, f"line_{i}.wav")
            if os.path.exists(audio_path): self.add_sound(audio_path)

            duration = max(1.5, len(text) / 14)

            self.play(
                ApplyMethod(actor.shift, UP * 0.5),
                run_time=0.25,
                rate_func=there_and_back
            )
            self.wait(duration - 0.25)
        
        self.play(FadeOut(barry), FadeOut(carl), run_time=2)

if __name__ == "__main__":
    sys.exit(0)
