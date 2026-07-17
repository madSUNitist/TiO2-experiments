"""Custom degradation run with user-provided data.

Two versions: first 5 points, then all 7 points.
"""
from degradation_pipeline.kinetics import plot_degradation_curve, plot_kinetic_fit

# Times relative to 9:38 = t=0
t_all = [0, 2, 17, 63, 108, 136, 157]
A_all = [1.589, 1.623, 1.460, 1.346, 1.206, 0.567, 0.433]

t_5 = t_all[:5]
A_5 = A_all[:5]

# ---- Version 1: first 5 points ----
print("=" * 50)
print("Version 1: First 5 data points")
print("=" * 50)
plot_degradation_curve(t_5, A_5, suffix="_5pts")
print()
plot_kinetic_fit(t_5, A_5, suffix="_5pts")

# ---- Version 2: all 7 points ----
print("\n" + "=" * 50)
print("Version 2: All 7 data points")
print("=" * 50)
plot_degradation_curve(t_all, A_all, suffix="_7pts")
print()
plot_kinetic_fit(t_all, A_all, suffix="_7pts")
