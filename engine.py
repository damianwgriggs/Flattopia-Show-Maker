# engine.py (FLATOPIA EDITION)
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

# We no longer need a 'backgrounds' folder!
def setup_directories():
    for d in [AUDIO_DIR, SFX_DIR]:
        if not os.path.exists(d): os.makedirs(d)

setup_directories()

# ==========================================
# 1. SFX HANDLER (Robust)
# ==========================================
def generate_fallback_sfx(filepath, phrase):
    try:
        aux = pyttsx3.init()
        aux.setProperty('rate', 200) 
        aux.save_to_file(phrase, filepath)
        aux.runAndWait()
    except: pass

def download_file(url, filepath, fallback_phrase=None):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        print(f"[SETUP] Downloading SFX: {os.path.basename(filepath)}")
        urllib.request.urlretrieve(url, filepath)
        return True
    except:
        if fallback_phrase: generate_fallback_sfx(filepath, fallback_phrase)
        return False

def ensure_sfx_exist():
    # Only downloading sounds now, no images
    sfx_assets = {
        "laugh.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/e/ee/Laugh_track_-_Audience_laughter.ogg/Laugh_track_-_Audience_laughter.ogg.mp3", "Hahahaha."), 
        "boo.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/3/3b/Crowd_Boo.wav/Crowd_Boo.wav.mp3", "Booooo."),
        "clap.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/6/62/Applause_-_enthusiastic.ogg/Applause_-_enthusiastic.ogg.mp3", "Clap clap clap."),
        "cricket.wav": ("https://upload.wikimedia.org/wikipedia/commons/transcoded/e/e9/Crickets_chirping.ogg/Crickets_chirping.ogg.mp3", "Chirp.")
    }
    for filename, (url, phrase) in sfx_assets.items():
        filepath = os.path.join(SFX_DIR, filename)
        if not os.path.exists(filepath) or os.path.getsize(filepath) < 1000:
            download_file(url, filepath, phrase)

# ==========================================
# 2. VOICE PRE-RENDER
# ==========================================
def pre_render_voice_lines():
    print("[SETUP] Pre-rendering voice lines...")
    try:
        with open("temp_script.json", "r") as f:
            data = json.load(f)
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        voices = engine.getProperty('voices')
        
        for i, item in enumerate(data):
            text = item["text"]
            speaker = item["speaker"].upper()
            if text.startswith("["): continue 
            
            path = os.path.join(AUDIO_DIR, f"line_{i}.wav")
            if "CARL" in speaker and len(voices) > 1: engine.setProperty('voice', voices[1].id)
            else: engine.setProperty('voice', voices[0].id)
            engine.save_to_file(text, path)
            
        engine.runAndWait()
        print("[SETUP] Audio complete.")
    except: pass

ensure_sfx_exist()
pre_render_voice_lines()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_manim_color(name):
    # Try to find the color in Manim's library, else default to White
    try: return getattr(sys.modules["manim"], name.upper())
    except: return WHITE

def create_actor(shape_name, color_name):
    c = get_manim_color(color_name)
    s = shape_name.upper()
    if s == "CIRCLE": body = Circle(color=c, fill_opacity=1).scale(1.5)
    elif s == "TRIANGLE": body = Triangle(color=c, fill_opacity=1).scale(2.0).shift(DOWN*0.3)
    elif s == "STAR": body = Star(color=c, fill_opacity=1).scale(1.8)
    elif s == "HEXAGON": body = RegularPolygon(n=6, color=c, fill_opacity=1).scale(1.5)
    else: body = Square(color=c, fill_opacity=1).scale(1.5)

    # Eyes
    eye_l = Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.4 + LEFT*0.4)
    eye_r = Circle(color=WHITE, fill_opacity=1, radius=0.3).shift(UP*0.4 + RIGHT*0.4)
    pupil_l = Dot(color=BLACK, radius=0.12).shift(UP*0.4 + LEFT*0.4)
    pupil_r = Dot(color=BLACK, radius=0.12).shift(UP*0.4 + RIGHT*0.4)
    return VGroup(body, eye_l, eye_r, pupil_l, pupil_r)

# ==========================================
# 4. THE FLATOPIA SCENE PALETTE
# ==========================================
# Map your scene names to Manim Colors here
SCENE_PALETTE = {
    "OFFICE": GREY,
    "PARK": GREEN_D,     # Darker green for contrast
    "FOREST": GREEN_E,   # Even darker green
    "HOUSE": LIGHT_GREY, # Pure WHITE might hide the eyes, so we use Light Grey
    "WHITE": WHITE,
    "SPACE": BLACK,
    "VOID": BLACK,
    "HELL": RED_E,
    "SKY": BLUE_C
}

SFX_MAP = {
    "LAUGH": (os.path.join(SFX_DIR, "laugh.wav"), 4),
    "BOO": (os.path.join(SFX_DIR, "boo.wav"), 3),
    "CLAP": (os.path.join(SFX_DIR, "clap.wav"), 5),
    "CRICKET": (os.path.join(SFX_DIR, "cricket.wav"), 2),
    "SILENCE": (None, 2)
}

class FlatlandEpisode(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#111111" # Default Dark Mode
        
        with open("temp_script.json", "r") as f:
            script_data = json.load(f)

        # -- CONFIG --
        profile = {
            "BARRY": {"shape": "SQUARE", "color": "RED"},
            "CARL": {"shape": "CIRCLE", "color": "BLUE"}
        }
        
        for item in script_data:
            t = item["text"].strip()
            if t.startswith("[CONFIG:"):
                parts = t.replace("[CONFIG:", "").replace("]", "").split(",")
                if len(parts) >= 3:
                    profile[parts[0].strip().upper()] = {
                        "shape": parts[1].strip().upper(), 
                        "color": parts[2].strip().upper()
                    }

        barry = create_actor(profile["BARRY"]["shape"], profile["BARRY"]["color"]).shift(LEFT*3)
        carl = create_actor(profile["CARL"]["shape"], profile["CARL"]["color"]).shift(RIGHT*3)
        self.add(barry, carl)

        # -- MAIN LOOP --
        for i, item in enumerate(script_data):
            speaker = item["speaker"].upper()
            text = item["text"]
            clean_text = text.strip()

            # --- 1. SCENE HANDLER (COLOR MODE) ---
            if clean_text.startswith("[SCENE:"):
                scene_name = clean_text.replace("[SCENE:", "").replace("]", "").strip().upper()
                print(f"[ACTION] Setting Background Color: {scene_name}")
                
                # Check Palette first
                if scene_name in SCENE_PALETTE:
                    self.camera.background_color = SCENE_PALETTE[scene_name]
                else:
                    # Try to use it as a raw Manim color (e.g., "BLUE", "RED")
                    try:
                        self.camera.background_color = get_manim_color(scene_name)
                    except:
                        # Fallback to Black if unknown
                        self.camera.background_color = BLACK
                continue

            # Skip Config
            if clean_text.startswith("[CONFIG:"): continue

            # --- 2. SFX ---
            if clean_text.startswith("[") and clean_text.endswith("]"):
                tag = clean_text[1:-1].upper()
                if tag in SFX_MAP:
                    fname, dur = SFX_MAP[tag]
                    if os.path.exists(fname): self.add_sound(fname)
                    self.wait(dur)
                continue 

            # --- 3. ANIMATION ---
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
    
