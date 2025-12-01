# app.py
import streamlit as st
import json
import subprocess
import os
import glob
import shutil
import time

# 1. PATH SETUP (Absolute Paths Only)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "completed_videos")
TEMP_AUDIO = os.path.join(PROJECT_ROOT, "temp_audio")
SFX_FOLDER = os.path.join(PROJECT_ROOT, "sfx")

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

st.set_page_config(page_title="Flatland Studio", layout="wide")
st.title("Flatland Sitcom Generator (Debug Mode)")

# 2. INPUT
default_script = """BARRY: Test line one.
CARL: Test line two.
[LAUGH]"""

user_input = st.text_area("Script Input", value=default_script, height=300)

def cleanup_temp_files():
    if os.path.exists(TEMP_AUDIO):
        files = glob.glob(os.path.join(TEMP_AUDIO, "*.wav"))
        for f in files:
            try: os.remove(f)
            except: pass

# 3. ACTION
if st.button("ACTION! (Render Video)"):
    st.info("Parsing script...")

    # Check for FFMPEG (Common Manim Error)
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        st.error("CRITICAL ERROR: 'ffmpeg' is not installed or not in your PATH. Manim cannot work without it.")
        st.stop()

    # Parse Script
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
        
    st.info("Rendering animation... This may take a moment.")
    
    # Run Manim with FULL LOGGING
    # --disable_caching helps prevent weird merge errors
    command = f"manim -pql --media_dir \"{PROJECT_ROOT}\" --disable_caching engine.py FlatlandEpisode"
    
    # Capture everything
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # 4. DIAGNOSTICS
    if process.returncode != 0:
        st.error("RENDER FAILED! Here is the detailed error log:")
        st.markdown("### ERROR LOG (Scroll to read):")
        # Display the error in code block
        st.code(process.stderr)
        st.markdown("### STANDARD OUTPUT:")
        st.code(process.stdout)
    else:
        # 5. MOVE AND DISPLAY
        # Look for MP4s in the project folder structure
        search_path = os.path.join(PROJECT_ROOT, "videos", "**", "*.mp4")
        files = glob.glob(search_path, recursive=True)
        
        if files:
            newest_file = max(files, key=os.path.getmtime)
            
            # Move to 'completed_videos'
            timestamp = int(time.time())
            final_filename = f"Sitcom_Episode_{timestamp}.mp4"
            final_path = os.path.join(OUTPUT_FOLDER, final_filename)
            
            try:
                shutil.copy(newest_file, final_path)
                st.success(f"SUCCESS! Video Saved: {final_path}")
                st.video(final_path)
                cleanup_temp_files()
            except Exception as e:
                st.error(f"Video created but failed to move: {e}")
                st.video(newest_file)
        else:
            st.warning("The script finished successfully, but no video file was found.")
            st.markdown("### LOGS:")
            st.code(process.stderr)
