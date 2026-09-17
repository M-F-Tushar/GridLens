from __future__ import annotations

import gradio as gr
from ui.gradio_app import build_app

demo = build_app()

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())