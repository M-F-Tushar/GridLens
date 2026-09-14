from __future__ import annotations

from ui.gradio_app import build_app

demo = build_app()

if __name__ == "__main__":
    demo.launch()