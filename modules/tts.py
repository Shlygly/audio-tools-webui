import asyncio
import os
import re
import time

from nicegui import ui
import pyttsx3

import utils

TAB_NAME = "Text to speech"
OUTPUT_FOLDER = "tts"

engine = pyttsx3.init()
VOICES = list(engine.getProperty('voices'))


def tts_iteration(text, index, voice, filename, progress_queue=None):
    if progress_queue:
        progress_queue.put_nowait(
            f"Generate text with voice {voice.name} ({100 * (index + 1) // len(VOICES)}%)..."
        )

    engine.setProperty("voice", voice.id)
    engine.save_to_file(text, filename)
    engine.runAndWait()
    return filename


def panel(pool, queue):
    async def run_tts():
        with loading_info:
            output_folder = f"{utils.OUTPUT_PATH}/{OUTPUT_FOLDER}"
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder)

            cleanup_button.disable()
            speak_button.disable()

            audio_outputs.clear()

            speak_button.props("loading")

            queue.put_nowait("Initialize...")

            text_slice = re.sub(r"\W+", "-", text_source.value)

            engine.setProperty("rate", rate_source.value)
            engine.setProperty("volume", volume_source.value)
            if all_voices.value:
                voices = VOICES
            else:
                voices = [VOICES[voice_source.value]]

            output_files = []
            loop = asyncio.get_running_loop()
            for index, voice in enumerate(voices):
                filename = os.path.join(
                    f"{utils.OUTPUT_PATH}/{OUTPUT_FOLDER}",
                    f'{len(os.listdir(f"{utils.OUTPUT_PATH}/{OUTPUT_FOLDER}")):05d}'
                    f'-{int(time.time())}-{text_slice[:127]}-{voice.name}' + '.wav'
                )
                await loop.run_in_executor(
                    pool, tts_iteration, text_source.value, index, voice, filename, queue
                )
                output_files.append(filename)
                audio_outputs.add(filename)

            if all_voices.value:
                queue.put_nowait("Preparing result...")
                zip_path = os.path.join(
                    output_folder,
                    f"{len(os.listdir(f'{utils.OUTPUT_PATH}/{OUTPUT_FOLDER}')):05d}-{int(time.time())}"
                    f"-{text_slice[:127]}.zip"
                )
                utils.create_zip(zip_path, output_files, progress_queue=queue)
                audio_outputs.add_global_link("Zip Archive", zip_path)

            ui.notify(f"{len(output_files)} file(s) generated !", type="positive")

            speak_button.props(remove="loading")

            cleanup_button.enable()
            speak_button.enable()

            queue.put_nowait("Done !")

    with ui.row().classes("flex gap-4"):
        with ui.column().classes("flex-1 flex items-stretch"):
            with ui.row().classes("flex items-center gap-4"):
                voice_source = ui.select(
                    {index: voice.name for index, voice in enumerate(VOICES)},
                    value=0,
                    label="Voice"
                ).classes("flex-1")
                all_voices = ui.switch(
                    "Speak with all available voices",
                    value=False
                )
                all_voices.bind_value_to(voice_source, "enabled", lambda v: not v)
            text_source = ui.textarea(
                label="Text to read"
            ).props("outlined").classes("h-full")
        with ui.column().classes("items-center gap-0"):
            ui.label("Rate")
            ui.label("words per second").classes("text-xs")
            rate_source = ui.slider(
                min=1.0,
                max=500.0,
                value=float(engine.getProperty("rate"))
            ).props("label vertical reverse").classes("my-2")
        with ui.column().classes("items-center gap-0"):
            ui.label("Volume")
            ui.label("%").classes("text-xs")
            volume_source = ui.slider(
                min=0.0,
                max=1.0,
                value=1.0
            ).props("label vertical reverse").classes("my-2")
    with ui.row().classes("grid grid-cols-4 gap-4"):
        audio_outputs = utils.ui_audio_list().classes("col-span-4")
        ui.element()
        cleanup_button = utils.ui_cleanup_button(OUTPUT_FOLDER)
        speak_button = ui.button("Speak")
        ui.element()
        loading_info = utils.ui_loading_info(queue)

    speak_button.on("click", run_tts)
