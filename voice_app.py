import flet as ft
import requests
import base64
import os
import time

# --- PASTE YOUR API KEY HERE ---
# CRITICAL: This line reads the secret key from the secure Render environment
# The API Key value is set on the Render Dashboard (ELEVENLABS_API_KEY)
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

def main(page: ft.Page):
    page.title = "AI Voice Cloner"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO

    voice_file_bytes = None
    voice_file_name = None
    cloned_voice_id = None
    current_audio_data = None 

    # --- UI Components (Initialized) ---
    header = ft.Column([
        ft.Text("Voice Clone Studio", size=30, weight=ft.FontWeight.BOLD, color="blue"),
        ft.Text("Cloud Edition: Upload, Speak, Download.", size=16, color="white70"),
        ft.Divider(),
    ])

    status_text = ft.Text("System Ready.", color="yellow")
    # Anti-crash dummy audio source
    audio_player = ft.Audio(src="https://luan.xyz/files/audio/ambient_c_motion.mp3", autoplay=False)
    page.overlay.append(audio_player)

    # --- HANDLER FUNCTIONS ---

    def pick_files_result(e: ft.FilePickerResultEvent):
        nonlocal voice_file_bytes, voice_file_name
        
        # Check API Key availability
        if not API_KEY:
            status_text.value = "ERROR: API Key missing from Render config."
            status_text.color = "red"
            page.update()
            return

        if e.files:
            f = e.files[0]
            voice_file_name = f.name
            
            try:
                # Read the file bytes directly after selection
                with open(f.path, "rb") as file:
                    voice_file_bytes = file.read()
                
                status_text.value = f"Selected: {voice_file_name} ({len(voice_file_bytes) / 1024:.2f} KB)"
                status_text.color = "green"
                clone_btn.disabled = False
            except Exception as read_err:
                status_text.value = f"File Read Error: {read_err}. Try a smaller file."
                status_text.color = "red"
                clone_btn.disabled = True
        else:
            status_text.value = "File selection cancelled."
            status_text.color = "red"
            clone_btn.disabled = True
        page.update()

    def open_picker(e):
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["mp3", "wav", "mpeg"],
        )

    def clone_voice(e):
        nonlocal cloned_voice_id
        if not voice_file_bytes: 
            status_text.value = "No voice file loaded."
            status_text.color = "red"
            page.update()
            return
        
        status_text.value = "Uploading to AI Brain..."
        status_text.color = "blue"
        page.update()

        url = "https://api.elevenlabs.io/v1/voice-cloning/instant-voice-cloning"
        headers = {"xi-api-key": API_KEY}
        
        try:
            voice_name = f"MyClonedVoice_{int(time.time())}" 
            
            files = {"files": (voice_file_name, voice_file_bytes, "audio/mpeg")}
            data = {"name": voice_name}
            
            response = requests.post(url, headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                cloned_voice_id = response.json().get("voice_id")
                status_text.value = "Voice Learned! You can now speak."
                status_text.color = "green"
                input_area.visible = True
            else:
                status_text.value = f"Cloning Error {response.status_code}: {response.text}"
                status_text.color = "red"

        except Exception as err:
            status_text.value = f"Network Error: {err}"
            status_text.color = "red"
        page.update()

    def generate_speech(e):
        nonlocal current_audio_data
        if not cloned_voice_id: 
            status_text.value = "Clone a voice first."
            status_text.color = "red"
            page.update()
            return
            
        if not prompt_input.value.strip():
            status_text.value = "Enter text to speak."
            status_text.color = "red"
            page.update()
            return

        status_text.value = "Generating speech..."
        status_text.color = "blue"
        page.update()

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cloned_voice_id}"
        headers = {"Content-Type": "application/json", "xi-api-key": API_KEY}
        data = {"text": prompt_input.value, "model_id": "eleven_monolingual_v1"}

        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                status_text.value = "Playing..."
                
                current_audio_data = base64.b64encode(response.content).decode("utf-8")
                
                audio_player.src = None
                audio_player.src_base64 = current_audio_data
                audio_player.autoplay = True
                audio_player.update()
                
                download_btn.visible = True
            else:
                status_text.value = f"TTS error {response.status_code}: {response.text}"
        except Exception as err:
             status_text.value = f"Network Error: {err}"
        page.update()
        
    def save_file(e):
        # Trigger the native Save dialog
        save_file_dialog.save_file(file_name="my_cloned_voice.mp3")

    def save_file_result(e: ft.FilePickerResultEvent):
        # Confirmation for file save (this handler is primarily for mobile/desktop builds)
        if e.path:
            status_text.value = f"File Saved!"
            status_text.color = "green"
            page.update()


    # --- UI BUILD ---
    file_picker = ft.FilePicker(on_result=pick_files_result)
    save_file_dialog = ft.FilePicker(on_result=save_file_result)
    page.overlay.extend([file_picker, save_file_dialog])
    
    upload_btn = ft.ElevatedButton("1. Upload Voice", on_click=open_picker)
    clone_btn = ft.ElevatedButton("2. Learn Voice", disabled=True, on_click=clone_voice)
    
    prompt_input = ft.TextField(label="What should I say?", multiline=True)
    speak_btn = ft.ElevatedButton("3. Speak", on_click=generate_speech)
    
    download_btn = ft.ElevatedButton(
        "Download Audio", 
        icon=ft.icons.DOWNLOAD, 
        on_click=save_file, 
        visible=False,
        bgcolor=ft.colors.GREEN_700, 
        color=ft.colors.WHITE
    )
    
    input_area = ft.Column([ft.Divider(), prompt_input, speak_btn, ft.Container(height=10), download_btn], visible=False)

    page.add(header, upload_btn, clone_btn, status_text, input_area)

# CRITICAL FIX FOR RENDER: 
# This line creates the 'app' object that the gunicorn Start Command needs.
app = ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.getenv("PORT", 8000)), host="0.0.0.0")

