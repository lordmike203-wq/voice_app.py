import flet as ft
import requests
import base64

# --- PASTE YOUR API KEY HERE ---
API_KEY = "sk_d53c89a985520a9804e13f05be17687ef79d72362d309748"

def main(page: ft.Page):
    page.title = "AI Voice Cloner"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    
    # instead of path, store bytes and filename
    voice_file_bytes = None
    voice_file_name = None
    cloned_voice_id = None
    
    # --- UI COMPONENTS ---
    header = ft.Column(
        [
            ft.Text(
                "Voice Clone Studio",
                size=30,
                weight=ft.FontWeight.BOLD,
                color="blue",
            ),
            ft.Text("Upload a sample, then type to speak.", size=16, color="white70"),
            ft.Divider(),
        ]
    )

    status_text = ft.Text("System Ready.", color="yellow")
    
    audio_player = ft.Audio(
        src="https://luan.xyz/files/audio/ambient_c_motion.mp3",
        autoplay=False,
    )
    page.overlay.append(audio_player)

    # --- LOGIC ---
    def pick_files_result(e: ft.FilePickerResultEvent):
        nonlocal voice_file_bytes, voice_file_name

        if e.files:
            # On web, path is usually not usable. Use bytes instead.
            f = e.files[0]
            voice_file_bytes = f.bytes      # <-- IMPORTANT
            voice_file_name = f.name

            if voice_file_bytes is None:
                status_text.value = (
                    "Could not read file bytes. Try again or use a smaller file."
                )
                status_text.color = "red"
                clone_btn.disabled = True
            else:
                status_text.value = f"Selected: {voice_file_name}"
                status_text.color = "green"
                clone_btn.disabled = True if API_KEY == "" else False
        else:
            status_text.value = "Cancelled or blocked. Try again."
            status_text.color = "red"
            clone_btn.disabled = True

        page.update()

    def open_picker_fast(e):
        file_picker.pick_files(allow_multiple=False)

    def clone_voice(e):
        nonlocal cloned_voice_id, voice_file_bytes, voice_file_name

        if not voice_file_bytes:
            status_text.value = "No voice file loaded yet."
            status_text.color = "red"
            page.update()
            return

        if API_KEY == "":
            status_text.value = "Missing API key! Set API_KEY first."
            status_text.color = "red"
            page.update()
            return
        
        status_text.value = "Uploading to ElevenLabs..."
        status_text.color = "blue"
        page.update()

        url = "https://api.elevenlabs.io/v1/voice-cloning/instant-voice-cloning"
        headers = {"xi-api-key": API_KEY}

        try:
            # Build multipart file from bytes
            files = {
                "files": (
                    voice_file_name or "voice_sample.wav",
                    voice_file_bytes,
                    "audio/wav",  # or audio/mpeg depending on your file
                )
            }
            data = {"name": "MyClonedVoice"}

            response = requests.post(url, headers=headers, data=data, files=files)

            if response.status_code == 200:
                cloned_voice_id = response.json().get("voice_id")
                if cloned_voice_id:
                    status_text.value = "Voice learned! Type below."
                    status_text.color = "green"
                    input_area.visible = True
                else:
                    status_text.value = "No voice_id in response."
                    status_text.color = "red"
            else:
                status_text.value = f"Error from API: {response.text}"
                status_text.color = "red"

        except Exception as err:
            status_text.value = f"Error: {err}"
            status_text.color = "red"

        page.update()

    def generate_speech(e):
        nonlocal cloned_voice_id

        if not cloned_voice_id:
            status_text.value = "Clone a voice first."
            status_text.color = "red"
            page.update()
            return

        if API_KEY == "":
            status_text.value = "Missing API key! Set API_KEY first."
            status_text.color = "red"
            page.update()
            return

        if not prompt_input.value.strip():
            status_text.value = "Enter some text to speak."
            status_text.color = "red"
            page.update()
            return

        status_text.value = "Generating speech..."
        status_text.color = "blue"
        page.update()

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cloned_voice_id}"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": API_KEY,
        }
        data = {
            "text": prompt_input.value,
            "model_id": "eleven_monolingual_v1",
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                status_text.value = "Playing..."
                status_text.color = "green"

                # response.content is raw audio bytes
                audio_data = base64.b64encode(response.content).decode("utf-8")
                audio_player.src = None
                audio_player.src_base64 = audio_data
                audio_player.autoplay = True
                audio_player.update()
            else:
                status_text.value = f"TTS error: {response.text}"
                status_text.color = "red"
        except Exception as err:
            status_text.value = f"Error: {err}"
            status_text.color = "red"

        page.update()

    # --- LAYOUT ---
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)
    
    upload_btn = ft.ElevatedButton("1. Upload Voice", on_click=open_picker_fast)
    clone_btn = ft.ElevatedButton("2. Learn Voice", disabled=True, on_click=clone_voice)
    
    prompt_input = ft.TextField(label="What should I say?", multiline=True)
    speak_btn = ft.ElevatedButton("3. Speak", on_click=generate_speech)
    # start hidden until voice is cloned
    input_area = ft.Column([ft.Divider(), prompt_input, speak_btn], visible=False)

    page.add(header, upload_btn, clone_btn, status_text, input_area)

ft.app(target=main)
