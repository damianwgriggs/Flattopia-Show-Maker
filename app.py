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
st.title("Flatland Sitcom Generator (Diagnostic Mode)")

# 2. INPUT
default_script = """BARRY: Test line one.
CARL: Test line two.
[LAUGH]"""

user_input = st.text_area("Script Input", value=default_script, height=200)

def cleanup_temp_files():
    # Clean audio
    if os.path.exists(TEMP_AUDIO):
        files = glob.glob(os.path.join(TEMP_AUDIO, "*.wav"))
        for f in files:
            try: os.remove(f)
            except: pass
    
    # Clean previous partial videos
    video_search = os.path.join(PROJECT_ROOT, "media", "**", "*.mp4")
    old_videos = glob.glob(video_search, recursive=True)
    for v in old_videos:
        try: os.remove(v)
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

    # 2. Verify engine.py exists
    if not os.path.exists(os.path.join(PROJECT_ROOT, "engine.py")):
        st.error(f"CRITICAL: engine.py not found in {PROJECT_ROOT}")
        st.stop()

    # 3. Execution with Real-Time Logging
    st.info("Step 2: Starting Manim Engine...")
    
    log_container = st.empty()
    logs = []
    
    # We use -v INFO to make sure Manim talks to us
    command = f"manim -pql --media_dir \"{PROJECT_ROOT}\" -v INFO --disable_caching engine.py FlatlandEpisode"
    
    # Start the process non-blocking
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, # Merge errors into standard output
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Read output line by line
    st.markdown("### 📜 Real-Time Execution Logs:")
    console_box = st.code("Initializing...", language="bash")
    
    full_log_text = ""
    
    while True:
        # Read a line
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
            
        if line:
            # Clean up line
            line = line.strip()
            if line:
                full_log_text += line + "\n"
                # Update the UI with the last 20 lines to keep it readable
                display_log = "\n".join(full_log_text.splitlines()[-20:])
                console_box.code(display_log, language="bash")

    # 4. Final Check
    if process.returncode == 0:
        st.success("Render process finished.")
        
        # Look for the video
        # Note: Manim puts videos in /media/videos/engine/480p15/FlatlandEpisode.mp4 usually
        search_path = os.path.join(PROJECT_ROOT, "media", "**", "*.mp4")
        files = glob.glob(search_path, recursive=True)
        
        if files:
            newest_file = max(files, key=os.path.getmtime)
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
            st.warning("Process finished 0, but no MP4 found. Check the full logs below.")
            with st.expander("Full Execution Log"):
                st.text(full_log_text)
    else:
        st.error("RENDER CRASHED.")
        st.write("Full crash log:")
        st.code(full_log_text)
