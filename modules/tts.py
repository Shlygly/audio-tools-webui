import os
import re
import time

import gradio as gr
import pyttsx3

import utils

TAB_NAME = "Text to speech"
OUTPUT_PATH = "./outputs/tts"


engine = pyttsx3.init()
VOICES = list(engine.getProperty('voices'))


def run_tts(text_source, voice_index, has_all_voices, rate_source, volume_source, progress=gr.Progress()):
    output_folder = f'{OUTPUT_PATH}'
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    progress(0, "Initialize...")

    text_slice = re.sub(r"\W+", "-", text_source)

    engine.setProperty("rate", rate_source)
    engine.setProperty("volume", volume_source)
    if has_all_voices:
        voices = VOICES
    else:
        voices = [VOICES[voice_index]]

    output_files = []
    for index, voice in enumerate(voices):
        progress((index + 1) / len(voices), f"Generate text with voice {voice.name}...")
        filename = os.path.join(
            output_folder,
            f'{len(os.listdir(OUTPUT_PATH)):05d}-{int(time.time())}-{text_slice}-({voice.name})'[:255] + '.wav'
        )
        engine.setProperty("voice", voice.id)
        engine.save_to_file(text_source, filename)
        engine.runAndWait()
        output_files.append(filename)

    zip_path = None
    if has_all_voices:
        progress(1, "Preparing result...")
        zip_path = os.path.join(output_folder, f"{len(os.listdir(OUTPUT_PATH)):05d}-{int(time.time())}-{text_slice}.zip")
        utils.create_zip(zip_path, output_files, progress=progress)

    return [*output_files] + [zip_path] if has_all_voices else [], utils.make_audio_list(output_files)


def ui():
    with gr.Blocks():
        with gr.Column(variant="compact"):
            with gr.Row(variant="compact"):
                with gr.Column(scale=3):
                    text_source = gr.Textbox(
                        label="Text to read",
                        lines=12
                    )
                with gr.Column(scale=1):
                    all_voices = gr.Checkbox(
                        label="Use all voices"
                    )
                    voice_source = gr.Dropdown(
                        choices=[voice.name for voice in VOICES],
                        value=VOICES[0].name,
                        label="Voice",
                        type="index"
                    )
                    rate_source = gr.Slider(
                        minimum=1.0,
                        maximum=500.0,
                        value=float(engine.getProperty("rate")),
                        label="Rate (words per second)"
                    )
                    volume_source = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=1.0,
                        label="Volume"
                    )

        with gr.Column(variant="compact"):
            with gr.Row():
                with gr.Column():
                    audio_preview = utils.init_audio_list()
                with gr.Column():
                    output_files = gr.File(
                        label="Output file(s)"
                    )

        with gr.Row(variant="compact"):
            with gr.Column():
                utils.make_cleanup_button(OUTPUT_PATH)
            with gr.Column():
                generate_button = gr.Button("Generate", variant="primary")

        generate_button.click(
            fn=run_tts,
            inputs=[text_source, voice_source, all_voices, rate_source, volume_source],
            outputs=[output_files, audio_preview]
        )
