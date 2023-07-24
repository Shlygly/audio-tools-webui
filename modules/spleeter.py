import glob
import importlib.resources as loader
import os
import shutil
import time

import gradio as gr
from scipy.io import wavfile

import utils
from spleeter import resources
from spleeter.separator import Separator

TAB_NAME = "Spleeter"
OUTPUT_PATH = "./outputs/spleeter"

SPLEETER_MODELS_DESCRIPTOR = sorted(
    list(
        filename[:-5]
        for filename in loader.contents(resources)
        if filename.endswith('.json')
    ),
    key=lambda f: (-1 if f[0].isdigit() else 1) * 1 / len(f)
)


def input_type_change(input_type):
    if input_type == "URL":
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)


def run_spleeter(input_type, link, link_format, link_quality, file, model_descriptor, use_mwf,
                 progress=gr.Progress()):
    output_folder = f'{OUTPUT_PATH}/{time.time()}'
    os.makedirs(output_folder)

    if input_type == "URL":
        audio_input_path = f'{output_folder}/source'
        download_paths, error_code = utils.simple_ydl(
            [link],
            audio_input_path,
            audio_format=link_format,
            audio_quality=link_quality,
            progress=progress
        )
        if len(download_paths) > 1:
            raise Exception(f"Error : too many audio on the link {link}")
        audio_input_path = download_paths[0]
    else:
        audio_input_path = f'{output_folder}/source.wav'
        sample_rate, audio_data = file
        wavfile.write(audio_input_path, sample_rate, audio_data)

    progress(0, "Create separator...")
    separator = Separator(f'spleeter:{model_descriptor}', use_mwf)

    progress(0.5, "Run Spleeter algorithm...")
    separator.separate_to_file(audio_input_path, output_folder)

    progress(1, "Preparing result...")
    output_paths = [audio_input_path]
    for filename in glob.glob(f'{output_folder}/source/*.wav'):
        output_paths.append(filename)

    zip_path = os.path.join(output_folder, f"{int(time.time())}-Archive.zip")
    utils.create_zip(zip_path, output_paths, progress=progress)

    return [*output_paths, zip_path], utils.make_audio_list(output_paths)


def ui():
    with gr.Blocks():
        with gr.Row():
            with gr.Box():
                with gr.Row(variant="compact"):
                    with gr.Column(variant="compact"):
                        input_type = gr.Radio(
                            ["URL", "Local file"],
                            value="URL",
                            label="Input type"
                        )
                        model_descriptor = gr.Radio(
                            SPLEETER_MODELS_DESCRIPTOR,
                            value=SPLEETER_MODELS_DESCRIPTOR[0],
                            label="Model descriptor"
                        )
                        use_mwf = gr.Checkbox(
                            label="Use Multichannel Wiener Filtering",
                            value=False
                        )
                    with gr.Column(variant="compact") as input_url_group:
                        input_link = gr.Textbox(
                            label="Link",
                            placeholder="From Youtube, Soundcloud, etc...",
                            lines=1,
                            max_lines=1
                        )
                        input_format = gr.Dropdown(
                            ["acc", "m4a", "mp3", "ogg", "wav"],
                            value="wav",
                            label="Format"
                        )
                        input_quality = gr.Dropdown(
                            ["Default", "32k", "96k", "128k", "160k", "192k", "256k", "320k", "Best"],
                            value="Best",
                            label="Quality"
                        )
                    with gr.Column(variant="compact", visible=False) as input_file_group:
                        input_file = gr.Audio(
                            label="Audio file"
                        )
                    input_type.change(
                        fn=input_type_change,
                        inputs=[input_type],
                        outputs=[input_url_group, input_file_group]
                    )
                with gr.Row(variant="compact"):
                    with gr.Column():
                        utils.make_cleanup_button(OUTPUT_PATH)
                    with gr.Column():
                        run_button = gr.Button("Run", variant="primary")
            with gr.Box():
                audio_preview = utils.init_audio_list()
                output_files = gr.File(
                    label="Output file(s)"
                )

        run_button.click(
            fn=run_spleeter,
            inputs=[input_type, input_link, input_format, input_quality, input_file, model_descriptor, use_mwf],
            outputs=[output_files, audio_preview]
        )
