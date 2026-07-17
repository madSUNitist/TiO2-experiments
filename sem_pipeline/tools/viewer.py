"""逐个浏览 output/corrected/ 下的 *_corrected.jpg 图像。"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

_PKG = Path(__file__).resolve().parent.parent
IMAGE_DIR = _PKG / "output" / "corrected"

files = sorted(IMAGE_DIR.glob("*_corrected.jpg"))
if not files:
    raise SystemExit(f"No *_corrected.jpg found in {IMAGE_DIR}")

idx = 0
total = len(files)

fig, ax = plt.subplots()
fig.canvas.manager.set_window_title("Corrected Image Viewer")


def show(i: int) -> None:
    ax.clear()
    img = mpimg.imread(files[i])
    ax.imshow(img, cmap="gray" if img.ndim == 2 else None)
    ax.set_title(f"[{i + 1}/{total}] {files[i].name}", fontsize=12)
    ax.axis("off")
    fig.canvas.draw_idle()


def on_key(event) -> None:
    global idx
    if event.key in ("right", "down", "n", " "):
        idx = (idx + 1) % total
    elif event.key in ("left", "up", "p", "backspace"):
        idx = (idx - 1) % total
    elif event.key in ("q", "escape"):
        plt.close(fig)
        return
    show(idx)


fig.canvas.mpl_connect("key_press_event", on_key)
show(0)
plt.show()
