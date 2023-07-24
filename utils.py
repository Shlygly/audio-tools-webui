import os
import shutil
import urllib.parse
import zipfile

import gradio as gr
from yt_dlp import YoutubeDL


def make_cleanup_button(path):
    def run_cleanup(button_text):
        if button_text == "Delete all files":
            return "Confirm ?"
        elif button_text == "Confirm ?":
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if not filename.startswith(".git") and (os.path.isfile(file_path) or os.path.islink(file_path)):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            return "Done !"
        else:
            return "Delete all files"

    cleanup_button = gr.Button("Delete all files")
    cleanup_button.click(
        fn=run_cleanup,
        inputs=[cleanup_button],
        outputs=[cleanup_button]
    )
    return cleanup_button


def init_audio_list():
    return gr.HTML(
        '<div class="gradio-container block svelte-faijhx" style="display:flex;flex-direction:column;'
        'justify-content:center;align-items:center;border-style:solid;'
        'border-color:var(--color-border-primary);overflow:visible;padding:8px;gap:4px;'
        'text-align:center;min-height:128px;">'
        '<em>Waiting for audio...</em>'
        '</div>'
    )


def make_audio_list(paths_list):
    html_response = '<div class="gradio-container block svelte-faijhx"' \
                    'style="display:flex;flex-direction:column;align-items:strech;border-style:solid;' \
                    'border-color:var(--color-border-primary);overflow:visible;padding:8px;gap:4px;">'
    html_response += ''.join(
        f"<span>{os.path.basename(path)}</span>"
        f"<audio controls style='border-radius: var(--radius-lg);'><source src='/file={urllib.parse.quote(path)}' /></audio>"
        for path in paths_list
    )
    html_response += '</div>'
    return html_response


def simple_ydl(urls, output_format, audio_format="wav", audio_quality="best", progress=None):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': output_format,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': audio_quality,
        }]
    }

    output_paths = []
    with YoutubeDL(ydl_opts) as ydl:
        infos = [
            ydl.extract_info(link, download=False)
            for link in (progress.tqdm(urls, desc="Extracting info...") if progress is not None else urls)
        ]
        tracks_count = sum(data["playlist_count"] if "playlist_count" in data else 1 for data in infos)
        if progress is not None:
            ydl.add_progress_hook(
                lambda p: progress(
                    (
                            len(output_paths) + (p["downloaded_bytes"] / p["total_bytes"] if "total_bytes" in p else 0)
                    ) / tracks_count,
                    f"Downloading {os.path.basename(p['filename'])}..."
                )
            )
        ydl.add_post_hook(lambda filename: output_paths.append(filename))
        error_code = ydl.download(urls)

    return output_paths, error_code


def create_zip(zip_path, files, progress=None):
    zip_file = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
    iterable = progress.tqdm(files, desc="Creating zip file...") if progress is not None else files
    for filename in iterable:
        zip_file.write(filename, arcname=os.path.basename(filename))
    zip_file.close()
