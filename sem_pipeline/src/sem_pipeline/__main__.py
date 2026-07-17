"""SEM pipeline CLI entry point.

Usage
-----
  python -m sem_pipeline              batch-process all images
  python -m sem_pipeline --image 01   process single image
  python -m sem_pipeline cumulative   generate cumulative ECD plot
"""

from __future__ import annotations

import sys

from .pipeline import run_pipeline
from .cumulative import plot_cumulative


def main() -> None:
    args = sys.argv[1:]

    if not args:
        run_pipeline()
    elif args[0] == "--image":
        image = args[1] if len(args) > 1 else None
        if image and not image.endswith(".jpg"):
            image += ".jpg"
        run_pipeline(image_filter=image)
    elif args[0] == "cumulative":
        plot_cumulative()
    else:
        print("Usage: python -m sem_pipeline [--image NAME | cumulative]")
        sys.exit(1)


if __name__ == "__main__":
    main()
