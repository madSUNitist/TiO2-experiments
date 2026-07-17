"""Degradation kinetics pipeline CLI entry point.

Usage
-----
  python -m degradation_pipeline
"""

from __future__ import annotations

from .kinetics import plot_degradation_curve, plot_kinetic_fit


def main() -> None:
    plot_degradation_curve()
    print()
    plot_kinetic_fit()


if __name__ == "__main__":
    main()
