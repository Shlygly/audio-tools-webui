import os.path
import time

import gradio as gr

import utils

TAB_NAME = "Downloader"
OUTPUT_PATH = "./outputs/downloader"


def run_download(links_data, audio_format, audio_quality, export_zip, progress=gr.Progress()):
    links = [link.strip() for link in links_data.split("\n") if link.strip()]

    if len(links) > 1:
        output_format = f'{OUTPUT_PATH}/%(epoch)010d-%(video_autonumber)02d-%(title)s'
    else:
        output_format = f'{OUTPUT_PATH}/%(epoch)010d-%(title)s'

    audio_quality = None if audio_quality.lower() == "default" else audio_quality.lower()

    output_paths, error_code = utils.simple_ydl(
        links,
        output_format,
        audio_format=audio_format,
        audio_quality=audio_quality,
        progress=progress
    )

    audio_list_html = utils.make_audio_list(output_paths)

    if export_zip and len(output_paths) > 1:
        zip_path = os.path.join(OUTPUT_PATH, f"{int(time.time())}-Archive.zip")
        utils.create_zip(zip_path, output_paths, progress=progress)
        output_paths.append(zip_path)

    return output_paths, audio_list_html


def ui():
    with gr.Blocks():
        with gr.Column(variant="compact"):
            with gr.Row(variant="compact"):
                with gr.Column(scale=3):
                    links_input = gr.Textbox(
                        label="Link(s)",
                        placeholder="A link per line",
                        lines=7
                    )
                with gr.Column(variant="compact", scale=1):
                    audio_format_select = gr.Dropdown(
                        ["acc", "m4a", "mp3", "ogg", "wav"],
                        value="mp3",
                        label="Format"
                    )
                    audio_quality_select = gr.Dropdown(
                        ["Default", "32k", "96k", "128k", "160k", "192k", "256k", "320k", "Best"],
                        value="192k",
                        label="Quality"
                    )
            with gr.Row(variant="compact"):
                export_zip = gr.Checkbox(
                    label="Create a zip file (only if there's multiple audio files)",
                    value=True
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
                download_button = gr.Button("Download", variant="primary")

        download_button.click(
            fn=run_download,
            inputs=[links_input, audio_format_select, audio_quality_select, export_zip],
            outputs=[output_files, audio_preview]
        )
