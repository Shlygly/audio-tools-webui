import asyncio
import os.path
import time

from nicegui import ui

import utils

TAB_NAME = "Downloader"
OUTPUT_FOLDER = "downloader"


def panel(pool, queue):
    async def run_download():
        with loading_info:
            queue.put_nowait("Start downloading...")

            cleanup_button.disable()
            download_button.disable()

            audio_outputs.clear()

            download_button.props("loading")

            links = [link.strip() for link in links_input.value.split("\n") if link.strip()]

            if len(links) > 1:
                output_format = f'{utils.OUTPUT_PATH}/{OUTPUT_FOLDER}/%(epoch)010d-%(video_autonumber)02d-%(title)s'
            else:
                output_format = f'{utils.OUTPUT_PATH}/{OUTPUT_FOLDER}/%(epoch)010d-%(title)s'

            audio_quality = None if audio_quality_select.value.lower() == "default" else audio_quality_select.value.lower()

            loop = asyncio.get_running_loop()
            output_paths, error_code = await loop.run_in_executor(
                pool, utils.simple_ydl, links, output_format, audio_format_select.value.lower(), audio_quality, queue
            )

            for path in output_paths:
                audio_outputs.add(path)

            if export_zip and len(output_paths) > 1:
                zip_path = os.path.join(utils.OUTPUT_PATH, OUTPUT_FOLDER, f"{int(time.time())}-Archive.zip")
                await loop.run_in_executor(
                    pool, utils.create_zip, zip_path, output_paths, queue
                )
                audio_outputs.add_global_link("Zip Archive", zip_path)

            ui.notify(f"{len(output_paths)} file(s) downloaded !", type="positive")

            download_button.props(remove="loading")

            cleanup_button.enable()
            download_button.enable()

            queue.put_nowait("Done !")

    with ui.row().classes("grid grid-cols-4 gap-4"):
        links_input = ui.textarea(
            label="Link(s)",
            placeholder="A link per line"
        ).props("outlined").classes("col-span-3 row-span-3 h-full")
        audio_format_select = ui.select(
            ["acc", "m4a", "mp3", "ogg", "wav"],
            value="mp3",
            label="Format"
        )
        audio_quality_select = ui.select(
            ["Default", "32k", "96k", "128k", "160k", "192k", "256k", "320k", "Best"],
            value="192k",
            label="Quality"
        )
        export_zip = ui.switch(
            "Create a zip file (only if there's multiple audio files)",
            value=True
        )
        audio_outputs = utils.ui_audio_list().classes("col-span-4")
        ui.element()
        cleanup_button = utils.ui_cleanup_button(OUTPUT_FOLDER)
        download_button = ui.button("Download")
        ui.element()
        loading_info = utils.ui_loading_info(queue)

    download_button.on("click", run_download)
