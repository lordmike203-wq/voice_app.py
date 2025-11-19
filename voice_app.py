import flet as ft
import requests
import base64
import os

# --- PASTE YOUR API KEY HERE ---
API_KEY = "sk_d53c89a985520a9804e13f05be17687ef79d72362d309748"

def main(page: ft.Page):
    page.title = "AI Voice Cloner"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO

    voice_file_bytes = None
    voice_file_name = None
    cloned_voice_id = None
    current_audio_data = None # Store audio to allow download

    header = ft.Column([
        ft.Text("Voice Clone Studio", size=30, weight=ft.FontWeight.BOLD, color="blue"),
        ft.Text("Cloud Edition: Upload, Clone, Speak, Download.", size=16, color="white70"),
        ft.Divider(),
    ])

    status_text = ft.Text("System Ready.", color="yellow")
    audio_player = ft.Audio(src="https://luan.xyz/files/audio/ambient_c_motion.mp3", autoplay=False)
    page.overlay.append(audio_player)

    def pick_files_result(e: ft.FilePickerResultEvent):
        nonlocal voice_file_bytes, voice_file_name
        if e.files:
            f = e.files[0]
            voice_file_bytes = f.bytes
            voice_file_name = f.name
            status_text.value = f"Selected: {voice_file_name}"
            status_text.color = "green"
            clone_btn.disabled = False
        else:
            status_text.value = "Cancelled."
            status_text.color = "red"
        page.update()

    def open_picker(e):
        file_picker.pick_files(allow_multiple=False)

    def clone_voice(e):
        nonlocal cloned_voice_id
        if not voice_file_bytes: return

        status_text.value = "Uploading to AI..."
        status_text.color = "blue"
        page.update()

        url = "https://api.elevenlabs.io/v1/voice-cloning/instant-voice-cloning"
        headers = {"xi-api-key": API_KEY}
        try:
            files = {"files": (voice_file_name, voice_file_bytes, "audio/mpeg")}
            data = {"name": "MyClonedVoice"}
            response = requests.post(url, headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                cloned_voice_id = response.json().get("voice_id")
                status_text.value = "Voice Learned! Type below."
                status_text.color = "green"
                input_area.visible = True
            else:
                status_text.value = f"Error: {response.text}"
        except Exception as err:
            status_text.value = f"Error: {err}"
        page.update()

    def generate_speech(e):
        nonlocal current_audio_data
        if not cloned_voice_id: return
        status_text.value = "Generating..."
        page.update()

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cloned_voice_id}"
        headers = {"Content-Type": "application/json", "xi-api-key": API_KEY}
        data = {"text": prompt_input.value, "model_id": "eleven_monolingual_v1"}

        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                status_text.value = "Playing..."
                
                # Store the audio data for downloading
                current_audio_data = base64.b64encode(response.content).decode("utf-8")
                
                audio_player.src = None
                audio_player.src_base64 = current_audio_data
                audio_player.autoplay = True
                audio_player.update()
                
                # Show the Download Button now
                download_btn.visible = True
                page.update()
            else:
                status_text.value = f"Error: {response.text}"
        except Exception as err:
             status_text.value = f"Error: {err}"
        page.update()
        
    def save_file(e):
        # This opens a save dialog on the user's phone/computer
        save_file_dialog.save_file(file_name="my_cloned_voice.mp3")

    def save_file_result(e: ft.FilePickerResultEvent):
        # This actually writes the file when the user picks a location
        if e.path and current_audio_data:
            import base64
            with open(e.path, "wb") as f:
                f.write(base64.b64decode(current_audio_data))
            status_text.value = "File Saved!"
            status_text.color = "green"
            page.update()

    # --- LAYOUT & COMPONENTS ---
    
    file_picker = ft.FilePicker(on_result=pick_files_result)
    save_file_dialog = ft.FilePicker(on_result=save_file_result)
    page.overlay.extend([file_picker, save_file_dialog])
    
    upload_btn = ft.ElevatedButton("1. Upload Voice", on_click=open_picker)
    clone_btn = ft.ElevatedButton("2. Learn Voice", disabled=True, on_click=clone_voice)
    
    prompt_input = ft.TextField(label="What should I say?", multiline=True)
    speak_btn = ft.ElevatedButton("3. Speak", on_click=generate_speech)
    
    # NEW: Download Button (Hidden until audio is ready)
    download_btn = ft.ElevatedButton(
        "Download Audio", 
        icon=ft.icons.DOWNLOAD, 
        on_click=save_file, 
        visible=False,
        bgcolor="green", color="white"
    )
    
    input_area = ft.Column([ft.Divider(), prompt_input, speak_btn, ft.Container(height=10), download_btn], visible=False)

    page.add(header, upload_btn, clone_btn, status_text, input_area)

# CLOUD CONFIGURATION
app_port = int(os.getenv("PORT", 8000))
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=app_port, host="0.0.0.0")


