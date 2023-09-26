from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

from nicegui import ui, app

from modules import downloader, spleeter_module, tts
from utils import Title

modules = [
    downloader,
    spleeter_module,
    tts
]

pool = ProcessPoolExecutor()


@ui.page('/')
def main_page(tab: int = 0):
    queue = Manager().Queue()

    with ui.element("header").classes("w-full flex flex-col items-center"):
        Title("Audio Tools Utility").classes("text-4xl")
        ui.label("Some useful tools for audio management").classes("italic")

    with ui.element("main").classes("w-full xl:px-32 2xl:px-64"):
        modules_tabs = []
        with ui.tabs().classes("w-full") as tabs:
            for module in modules:
                modules_tabs.append(ui.tab(module.TAB_NAME))
        with ui.tab_panels(tabs, value=modules_tabs[tab]).classes("w-full"):
            for tab, module in zip(modules_tabs, modules):
                with ui.tab_panel(tab):
                    module.panel(pool, queue)


app.on_shutdown(pool.shutdown)

# app.native.window_args['resizable'] = False
# app.native.start_args['debug'] = True

ui.run(title="Audio tools", dark=None)
# ui.run(title="Audio tools", dark=None, native=True, window_size=(1000, 700), fullscreen=False)
