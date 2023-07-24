import gradio as gr

from modules import downloader, spleeter, tts

modules = [
    downloader,
    spleeter,
    tts
]

with gr.Blocks(title="Audio Tools", css=".gradio-container {min-width: 100%;}") as dashboard:
    dashboard.queue(concurrency_count=20, max_size=5)

    gr.HTML("""
    <header style='text-align: center'>
        <h1 style="margin-bottom: 2px">Audio Tools Utiliy</h1>
        <p style="font-style: italic">Some useful tools for audio management</p>
    </header>
    """)

    for module in modules:
        with gr.Tab(module.TAB_NAME):
            module.ui()

if __name__ == "__main__":
    dashboard.launch(inbrowser=True, server_name="0.0.0.0", share=True)
