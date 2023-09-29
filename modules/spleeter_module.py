import asyncio
import glob
import importlib.resources as loader
import os
import time

from nicegui import ui

import utils
from spleeter import resources

TAB_NAME = "Spleeter"
OUTPUT_FOLDER = "spleeter"

SPLEETER_MODELS_DESCRIPTOR = sorted(
    list(
        filename[:-5]
        for filename in loader.contents(resources)
        if filename.endswith('.json')
    ),
    key=lambda f: (-1 if f[0].isdigit() else 1) * 1 / len(f)
)

INPUT_TYPES = {
    0: "URL",
    1: "Local file"
}


def panel(pool, queue):
    async def run_spleeter():
        with loading_info:
            try:
                queue.put_nowait("Start downloading...")

                cleanup_button.disable()
                split_button.disable()

                audio_outputs.clear()

                split_button.props("loading")

                output_folder = os.path.join(utils.OUTPUT_PATH, OUTPUT_FOLDER, f'{time.time()}')
                os.makedirs(output_folder)

                if input_type.value == 0:
                    if not len(input_link.value):
                        raise Exception(f"Link is empty !")
                    audio_input_path = os.path.join(output_folder, "source")
                    loop = asyncio.get_running_loop()
                    download_paths, error_code = await loop.run_in_executor(
                        pool, utils.simple_ydl, input_link.value, audio_input_path, audio_format_select.value.lower(),
                        audio_quality_select.value, queue
                    )
                    if len(download_paths) > 1:
                        raise Exception(f"Too many audio on the link {input_link.value} !")
                    audio_input_path = download_paths[0]
                else:
                    if not input_file_data:
                        raise Exception(f"No file has been uploaded !")
                    audio_input_path = f'{output_folder}/{input_file_data.name}'
                    with open(audio_input_path, "wb") as audio_file_pointer:
                        audio_file_pointer.write(input_file_data.content.read())

                await loop.run_in_executor(
                    pool, utils.proceed_spleeter, audio_input_path, output_folder, model_descriptor.value, use_mwf.value,
                    queue
                )

                queue.put_nowait("Preparing result...")
                output_paths = [audio_input_path]
                for filename in glob.glob(f'{output_folder}/source/*.wav'):
                    output_paths.append(filename)
                    audio_outputs.add(filename)

                zip_path = os.path.join(output_folder, f"{int(time.time())}-Archive.zip")
                await loop.run_in_executor(
                    pool, utils.create_zip, zip_path, output_paths, queue
                )
                audio_outputs.add_global_link("Zip Archive", zip_path)

                ui.notify("Audio generated !", type="positive")
            except Exception as ex:
                ui.notify(f"Error : {ex}", type="negative")
            finally:
                split_button.props(remove="loading")

                cleanup_button.enable()
                split_button.enable()

                queue.put_nowait("Done !")

    def set_input_file_data(data):
        nonlocal input_file_data
        input_file_data = data

    input_file_data = None
    with ui.row().classes("grid grid-cols-4 gap-4"):
        with ui.row().classes("col-span-3 row-span-2 h-full flex items-center"):
            input_type = ui.radio(INPUT_TYPES, value=0)
            with ui.row().classes("flex-1 flex items-center") as input_url:
                input_link = ui.input(
                    label="Link",
                    placeholder="From Youtube, Soundcloud, etc..."
                ).classes("flex-1")
                audio_format_select = ui.select(
                    ["acc", "m4a", "mp3", "ogg", "wav"],
                    value="wav",
                    label="Format"
                ).classes("w-32")
                audio_quality_select = ui.select(
                    ["Default", "32k", "96k", "128k", "160k", "192k", "256k", "320k", "Best"],
                    value="Default",
                    label="Quality"
                ).classes("w-32")
            input_file = ui.upload(
                label="Audio file",
                auto_upload=True,
                on_upload=lambda e: set_input_file_data(e)
            ).classes("flex-1")
            input_type.bind_value_to(input_url, "visible", lambda value: value == 0)
            input_type.bind_value_to(input_file, "visible", lambda value: value == 1)
        model_descriptor = ui.select(
            SPLEETER_MODELS_DESCRIPTOR,
            value=SPLEETER_MODELS_DESCRIPTOR[0],
            label="Model descriptor"
        )
        use_mwf = ui.switch(
            "Use Multichannel Wiener Filtering",
            value=False
        )
        audio_outputs = utils.ui_audio_list().classes("col-span-4")
        ui.element()
        cleanup_button = utils.ui_cleanup_button(OUTPUT_FOLDER)
        split_button = ui.button("Split")
        ui.element()
        loading_info = utils.ui_loading_info(queue)

    split_button.on("click", run_spleeter)
