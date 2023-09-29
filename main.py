from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

from nicegui import ui, app, native_mode

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

    with ui.element("header").classes("w-full flex flex-col items-center mb-2"):
        with ui.row().classes("self-end flex items-center gap-1"):
            dark_mode = ui.dark_mode(value=True)
            ui.icon("light_mode").props("size=sm")
            ui.switch(value=dark_mode.value).bind_value_to(dark_mode)
            ui.icon("dark_mode").props("size=sm")
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

app.native.window_args['resizable'] = True
app.native.start_args['debug'] = False

ui.run(
    title="Audio tools",
    port=native_mode.find_open_port(),
    dark=None,
    # native=True,
    # window_size=(900, 600),
    # fullscreen=False,
    # reload=False
)
