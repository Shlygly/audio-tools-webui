import os
import shutil
import zipfile
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi.responses import StreamingResponse
from nicegui import ui, app
from nicegui.element import Element
from nicegui.elements.mixins.text_element import TextElement
from yt_dlp import YoutubeDL


OUTPUT_PATH = "./outputs/"


@app.get("/download/{path:path}")
def route_download_file(path):
    return StreamingResponse(open(os.path.join(OUTPUT_PATH, path), "rb"))


class Title(TextElement):
    def __init__(self, text: str = '', level=1) -> None:
        super().__init__(tag=f'h{level}', text=text)


def ui_cleanup_button(folder):
    path = os.path.join(OUTPUT_PATH, folder)

    async def show():
        try:
            files_to_delete = []
            directories_to_delete = []
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if not filename.startswith(".git") and (os.path.isfile(file_path) or os.path.islink(file_path)):
                    files_to_delete.append(file_path)
                elif os.path.isdir(file_path):
                    directories_to_delete.append(file_path)
            dialog_label.set_text(
                f"You're going to permanently delete {len(files_to_delete)} file(s) and"
                f" {len(directories_to_delete)} directorie(s)."
            )
            if len(files_to_delete) > 0 or len(directories_to_delete) > 0:
                if await dialog:
                    for file_path in files_to_delete:
                        os.unlink(file_path)
                    for dir_path in directories_to_delete:
                        shutil.rmtree(dir_path)
                    ui.notify(
                        f'{len(files_to_delete) + len(directories_to_delete)} file(s) and directorie(s) deleted !',
                        type="positive"
                    )
                else:
                    ui.notify('Aborted !')
            else:
                ui.notify("There's nothing to delete...", type="warning")
        except:
            ui.notify("An error has occured !", type="negative")

    with ui.dialog() as dialog, ui.card():
        Title("Delete old files", level=2).classes("text-2xl")
        dialog_label = ui.label('...')
        ui.label('Do you want to continue ?')
        with ui.row():
            ui.button('Yes, delete everything', on_click=lambda: dialog.submit(True)).props("color=negative")
            ui.button('Cancel', on_click=lambda: dialog.submit(False)).props("color=secondary")

    button = ui.button("Delete all files").props("color=secondary")
    button.on("click", show)
    return button


def ui_audio_list(audio_paths=None):
    class AudioListElement(Element):
        def __init__(self, initial_paths=None):
            super().__init__()
            self.classes("flex")
            self.paths = []
            with self:
                self.ui_waiting_label = ui.label("Waiting for audio...").classes("italic text-center")
                self.ui_list = ui.column().classes("w-full gap-2")
            if initial_paths:
                for path in initial_paths:
                    self.add(path)

        def add(self, path, name=None):
            self.paths.append(path)
            self.ui_waiting_label.set_visibility(False)
            with self.ui_list:
                with ui.card().classes("flex flex-row items-stretch w-full p-0 border shadow-none"):
                    with ui.column().classes("flex-1 gap-1 p-2"):
                        ui.label(name if name else os.path.basename(path)).classes("italic")
                        ui.audio(path).classes("w-full")
                    ui.button(
                        icon="file_download",
                        on_click=lambda: ui.download(f"/download/{os.path.relpath(path, OUTPUT_PATH)}")
                    )

        def add_many(self, paths):
            for path in paths:
                self.add(path)

        def add_global_link(self, text, path):
            with self.ui_list:
                with ui.row().classes("flex justify-center w-full"):
                    ui.button(
                        text,
                        on_click=lambda: ui.download(f"/download/{os.path.relpath(path, OUTPUT_PATH)}")
                    )

        def clear(self):
            self.paths = []
            self.ui_waiting_label.set_visibility(True)
            self.ui_list.clear()

    return AudioListElement(audio_paths if audio_paths else [])


def ui_loading_info(queue):
    class LoadingInfo:
        def __init__(self, q):
            self.info_timer = ui.timer(
                0.1, callback=lambda: self.info_text.set_text(q.get() if not q.empty() else self.info_text.text)
            )
            self.info_text = ui.label(
                "..."
            ).classes(
                "col-span-4 italic text-center text-info"
            ).bind_visibility_to(
                self.info_timer, 'active'
            )
            self.info_text.set_visibility(False)

        def __enter__(self):
            self.info_text.set_visibility(True)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.info_text.set_visibility(False)

    return LoadingInfo(queue)


def simple_ydl(urls, output_format, audio_format="wav", audio_quality="best", progress_queue=None):
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
        if progress_queue is not None:
            ydl.add_progress_hook(
                lambda p: progress_queue.put_nowait(
                    f"Downloading {os.path.basename(p['filename'])}"
                    f" ({int(100 * p['downloaded_bytes'] / p['total_bytes']) if 'total_bytes' in p else '???'}%)..."
                )
            )
        ydl.add_post_hook(lambda filename: output_paths.append(filename))
        error_code = ydl.download(urls)

    return output_paths, error_code


def create_zip(zip_path, files, progress_queue=None):
    zip_file = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
    if progress_queue:
        progress_queue.put_nowait("Creating zip file...")
    for filename in files:
        zip_file.write(filename, arcname=os.path.basename(filename))
    zip_file.close()


def proceed_spleeter(input_path, output_path, model_descriptor, use_mwf=False, progress_queue=None):
    progress_queue.put_nowait("Initializing spleeter...")
    from spleeter.separator import Separator

    progress_queue.put_nowait("Create separator...")
    separator = Separator(f'spleeter:{model_descriptor}', use_mwf)

    progress_queue.put_nowait("Run Spleeter algorithm...")
    separator.separate_to_file(input_path, output_path)
