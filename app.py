# app.py
import streamlit as st
import json
import subprocess
import os
import glob
import shutil
import time
import sys

# 1. PATH SETUP
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "completed_videos")
TEMP_AUDIO = os.path.join(PROJECT_ROOT, "temp_audio")
SFX_FOLDER = os.path.join(PROJECT_ROOT, "sfx")

# Ensure directories exist
for folder in [OUTPUT_FOLDER, TEMP_AUDIO, SFX_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

st.set_page_config(page_title="Flatland Studio", layout="wide")
st.title("Flatland Sitcom Generator (Final Fix)")

# 2. INPUT
default_script = """BARRY: Test line one.
CARL: Test line two.
[LAUGH]"""

user_input = st.text_area("Script Input", value=default_script, height=200)

def cleanup_temp_files():
    if os.path.exists(TEMP_AUDIO):
        files = glob.glob(os.path.join(TEMP_AUDIO, "*.wav"))
        for f in files:
            try: os.remove(f)
            except: pass
    
    # Aggressive cleanup of old videos to ensure we don't play an old cached one
    for pattern in ["**/*.mp4"]:
        files = glob.glob(os.path.join(PROJECT_ROOT, pattern), recursive=True)
        for f in files:
            if "completed_videos" not in f: # Don't delete our saved history
                try: os.remove(f)
                except: pass

# 3. ACTION
if st.button("ACTION! (Render Video)"):
    cleanup_temp_files()
    
    # 1. Parse Script
    st.info("Step 1: Parsing script...")
    script_data = []
    lines = user_input.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith("[") and line.endswith("]"):
             script_data.append({"speaker": "SFX", "text": line})
             continue
        if ":" in line:
            parts = line.split(":", 1)
            script_data.append({"speaker": parts[0].strip(), "text": parts[1].strip()})
            
    with open("temp_script.json", "w") as f:
        json.dump(script_data, f)

    # 2. Execution
    st.info("Step 2: Starting Manim Engine...")
    
    log_container = st.empty()
    
    # Using the exact command that worked in your logs
    command = f"manim -pql --media_dir \"{PROJECT_ROOT}\" -v INFO --disable_caching engine.py FlatlandEpisode"
    
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    console_box = st.code("Initializing...", language="bash")
    full_log_text = ""
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            line = line.strip()
            if line:
                full_log_text += line + "\n"
                display_log = "\n".join(full_log_text.splitlines()[-20:])
                console_box.code(display_log, language="bash")

    # 3. Finding the Video (IMPROVED SEARCH)
    if process.returncode == 0:
        st.success("Render process finished.")
        
        # Search EVERYWHERE for the MP4
        files = glob.glob(os.path.join(PROJECT_ROOT, "**", "*.mp4"), recursive=True)
        
        # Filter out the one we just made
        valid_files = [f for f in files if "FlatlandEpisode" in f and "partial" not in f]
        
        if valid_files:
            newest_file = max(valid_files, key=os.path.getmtime)
            timestamp = int(time.time())
            final_filename = f"Sitcom_Episode_{timestamp}.mp4"
            final_path = os.path.join(OUTPUT_FOLDER, final_filename)
            
            try:
                shutil.copy(newest_file, final_path)
                st.balloons()
                st.success(f"VIDEO RENDERED SUCCESSFULLY!")
                st.video(final_path)
            except Exception as e:
                st.error(f"Failed to copy video: {e}")
                st.video(newest_file)
        else:
            st.error("Manim finished, but I couldn't find 'FlatlandEpisode.mp4'.")
            st.warning("Debugging info - Files found in folder:")
            st.write(files)
    else:
        st.error("RENDER CRASHED.")
        st.code(full_log_text)
