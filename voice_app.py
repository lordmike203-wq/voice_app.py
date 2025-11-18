import flet as ft
import requests
import time
import base64

# --- PASTE YOUR API KEY HERE ---
API_KEY = "sk_d53c89a985520a9804e13f05be17687ef79d72362d309748"

def main(page: ft.Page):
    page.title = "AI Voice Cloner"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    
    voice_file_path = None
    cloned_voice_id = None
    
    # --- UI COMPONENTS ---
    header = ft.Column([
        ft.Text("Voice Clone Studio", size=30, weight=ft.FontWeight.BOLD, color="blue"),
        ft.Text("Upload audio to clone voice.", size=16, color="white70"),
        ft.Divider(),
    ])

    status_text = ft.Text("System Ready.", color="yellow")
    loading_ring = ft.ProgressRing(visible=False)
    
    audio_player = ft.Audio(
        src="https://luan.xyz/files/audio/ambient_c_motion.mp3", 
        autoplay=False
    )
    page.overlay.append(audio_player)

    # --- LOGIC ---
    def pick_files_result(e: ft.FilePickerResultEvent):
        loading_ring.visible = False
        page.update()
        
        nonlocal voice_file_path
        if e.files:
            voice_file_path = e.files[0].path
            status_text.value = f"Selected: {e.files[0].name}"
            status_text.color = "green"
            clone_btn.disabled = False
        else:
            status_text.value = "Cancelled."
            status_text.color = "red"
        page.update()

    def open_picker(e):
        status_text.value = "Please select a file..."
        loading_ring.visible = True
        page.update()
        file_picker.pick_files(allow_multiple=False)

    def clone_voice(e):
        if not voice_file_path: return
        
        status_text.value = "Uploading to AI..."
        loading_ring.visible = True
        page.update()

        url = "https://api.elevenlabs.io/v1/voice-cloning/instant-voice-cloning"
        headers = {"xi-api-key": API_KEY}
        try:
            with open(voice_file_path, 'rb') as f:
                files = {'files': f}
                data = {'name': 'MyClonedVoice'}
                response = requests.post(url, headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                nonlocal cloned_voice_id
                cloned_voice_id = response.json()['voice_id']
                status_text.value = "Voice Learned! Type below."
                status_text.color = "green"
                input_area.visible = True
            else:
                status_text.value = f"Error: {response.text}"
        except Exception as err:
            status_text.value = f"Error: {err}"
        
        loading_ring.visible = False
        page.update()

    def generate_speech(e):
        if not cloned_voice_id: return
        status_text.value = "Generating Audio..."
        loading_ring.visible = True
        page.update()

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cloned_voice_id}"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": API_KEY
        }
        data = {
            "text": prompt_input.value,
            "model_id": "eleven_monolingual_v1"
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                status_text.value = "Playing Audio..."
                audio_data = base64.b64encode(response.content).decode("utf-8")
                audio_player.src = None
                audio_player.src_base64 = audio_data
                audio_player.autoplay = True
                audio_player.update()
            else:
                status_text.value = f"Error: {response.text}"
        except Exception as err:
             status_text.value = f"Error: {err}"
        
        loading_ring.visible = False
        page.update()

    # --- LAYOUT ---
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)
    
    upload_btn = ft.ElevatedButton("1. Upload Voice", on_click=open_picker)
    clone_btn = ft.ElevatedButton("2. Learn Voice", disabled=True, on_click=clone_voice)
    
    prompt_input = ft.TextField(label="What should I say?", multiline=True)
    speak_btn = ft.ElevatedButton("3. Speak", on_click=generate_speech)
    
    # Important: We make the input area visible=True immediately so you can see it
    input_area = ft.Column([ft.Divider(), prompt_input, speak_btn], visible=True)

    page.add(header, upload_btn, loading_ring, clone_btn, status_text, input_area)

ft.app(target=main)


