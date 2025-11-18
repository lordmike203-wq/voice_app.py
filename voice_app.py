import flet as ft
import requests
import time

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
        ft.Text("Upload a sample, then type to speak.", size=16, color="white70"),
        ft.Divider(),
    ])

    status_text = ft.Text("Waiting for voice sample...", color="yellow")
    
    # FIXED: Autoplay is OFF so it doesn't crash on start. 
    # It will only play when we tell it to later.
    audio_player = ft.Audio(src="", autoplay=False)
    page.overlay.append(audio_player)

    # --- LOGIC ---
    def pick_files_result(e: ft.FilePickerResultEvent):
        nonlocal voice_file_path
        if e.files:
            voice_file_path = e.files[0].path
            status_text.value = f"Selected: {e.files[0].name}"
            status_text.color = "green"
            clone_btn.disabled = False
            page.update()

    def clone_voice(e):
        if not voice_file_path: return
        status_text.value = "Learning voice... please wait."
        status_text.color = "blue"
        page.update()

        url = "https://api.elevenlabs.io/v1/voice-cloning/instant-voice-cloning"
        headers = {"xi-api-key": API_KEY}
        try:
            files = {'files': (open(voice_file_path, 'rb'))}
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
        page.update()

    def generate_speech(e):
        if not cloned_voice_id or not prompt_input.value: return
        status_text.value = "Generating Audio..."
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
                # Save file with a unique name so browser doesn't cache it
                filename = f"output_{int(time.time())}.mp3"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                status_text.value = "Playing Audio..."
                
                # FIXED: Now we give it the file and tell it to play
                audio_player.src = filename
                audio_player.autoplay = True
                audio_player.update()
            else:
                status_text.value = f"Error: {response.text}"
        except Exception as err:
             status_text.value = f"Error: {err}"
        page.update()

    # --- LAYOUT ---
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)
    
    upload_btn = ft.ElevatedButton("1. Upload Voice", on_click=lambda _: file_picker.pick_files())
    clone_btn = ft.ElevatedButton("2. Learn Voice", disabled=True, on_click=clone_voice)
    
    prompt_input = ft.TextField(label="What should I say?")
    speak_btn = ft.ElevatedButton("3. Speak", on_click=generate_speech)
    input_area = ft.Column([prompt_input, speak_btn], visible=False)

    page.add(header, upload_btn, clone_btn, status_text, input_area)

ft.app(target=main)


