"""Train a simple classifier to score homography quad candidates.

Uses the hand-labeled candidates.csv as training data.
Output: a JSON model file with the logistic regression coefficients.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# feature engineering
# ---------------------------------------------------------------------------

def _extract_features(r: dict) -> np.ndarray:
    """Extract 8 geometric features from a candidate row."""
    w_img = 4032 if r["image"][:2] <= "03" else 5712
    h_img = 2268 if r["image"][:2] <= "03" else 3213

    tl = np.array([r["TL_x"], r["TL_y"]])
    tr = np.array([r["TR_x"], r["TR_y"]])
    br = np.array([r["BR_x"], r["BR_y"]])
    bl = np.array([r["BL_x"], r["BL_y"]])

    top_len = float(np.linalg.norm(tr - tl))
    bot_len = float(np.linalg.norm(br - bl))
    lft_len = float(np.linalg.norm(bl - tl))
    rgt_len = float(np.linalg.norm(br - tr))

    mean_w = (top_len + bot_len) / 2.0
    mean_h = (lft_len + rgt_len) / 2.0
    ar = mean_w / max(mean_h, 1.0)

    cx = (tl[0] + tr[0] + br[0] + bl[0]) / 4.0 / w_img
    cy = (tl[1] + tr[1] + br[1] + bl[1]) / 4.0 / h_img

    top_dir = (tr - tl) / max(float(np.linalg.norm(tr - tl)), 1.0)
    lft_dir = (bl - tl) / max(float(np.linalg.norm(bl - tl)), 1.0)
    rgt_dir = (br - tr) / max(float(np.linalg.norm(br - tr)), 1.0)

    ortho = float(abs(np.dot(top_dir, lft_dir)))
    v_parallel = float(abs(np.dot(lft_dir, rgt_dir)))
    h_ratio = max(top_len, bot_len) / max(min(top_len, bot_len), 1.0)

    return np.array([
        r["blue_pct"],
        r["area_pct"],
        ar,
        cx,
        cy,
        ortho,
        v_parallel,
        h_ratio,
    ], dtype=np.float64)


FEATURE_NAMES = [
    "blue_pct", "area_pct", "ar", "cx", "cy",
    "ortho", "v_parallel", "h_ratio",
]


# ---------------------------------------------------------------------------
# training
# ---------------------------------------------------------------------------

def train(csv_path: str | Path, model_path: str | Path) -> None:
    """Train and save the model."""
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            s = r["score"].strip()
            if not s:
                continue
            r["score"] = float(s)
            for k in [
                "TL_x", "TL_y", "TR_x", "TR_y",
                "BR_x", "BR_y", "BL_x", "BL_y",
                "blue_pct", "area_pct",
            ]:
                r[k] = float(r[k])
            rows.append(r)

    X = np.array([_extract_features(r) for r in rows])
    y = np.array([r["score"] for r in rows])
    y_bin = (y == 1.0).astype(int)

    print(f"Samples: {len(X)}  (good={y_bin.sum()}, bad={len(y_bin)-y_bin.sum()})")

    # --- Level 1: Logistic Regression ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(C=0.1, max_iter=1000)
    model.fit(X_scaled, y_bin)
    y_pred = model.predict(X_scaled)

    acc = accuracy_score(y_bin, y_pred)
    print(f"\nLogisticRegression (C=0.1): accuracy = {acc:.1%}")
    print("\nFeature weights (sorted by importance):")
    weights = sorted(
        zip(FEATURE_NAMES, model.coef_[0]),
        key=lambda x: -abs(x[1]),
    )
    for name, w in weights:
        print(f"  {name:>12s}: {w:+.4f}")

    print("\n" + classification_report(y_bin, y_pred, target_names=["bad", "good"]))

    # Check for underfitting
    if acc < 0.85 or (y_bin == 1).sum() > 0 and (y_bin[y_bin == 1] == y_pred[y_bin == 1]).mean() < 0.90:
        print("[UNDERFIT] trying slightly stronger regularisation …")
        model = LogisticRegression(C=1.0, max_iter=1000)
        model.fit(X_scaled, y_bin)
        y_pred = model.predict(X_scaled)
        acc = accuracy_score(y_bin, y_pred)
        print(f"LogisticRegression (C=1.0): accuracy = {acc:.1%}")
        print(classification_report(y_bin, y_pred, target_names=["bad", "good"]))

    # --- save ---
    model_data = {
        "coef": model.coef_[0].tolist(),
        "intercept": model.intercept_[0],
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "feature_names": FEATURE_NAMES,
    }
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(model_path).write_text(json.dumps(model_data, indent=2), encoding="utf-8")
    print(f"\nModel saved → {model_path}")


def score_candidate(corners: list, image_name: str,
                    blue_pct: float, area_pct: float,
                    model_path: str | Path) -> float:
    """Predict probability of 'good' (score=1) for a quad candidate."""
    model_data = json.loads(Path(model_path).read_text())
    coef = np.array(model_data["coef"])
    intercept = model_data["intercept"]
    mean = np.array(model_data["scaler_mean"])
    scale = np.array(model_data["scaler_scale"])

    # build feature vector from raw data
    feature_names = model_data["feature_names"]
    # We need a dummy dict with the same keys as _extract_features expects
    dummy = {
        "image": image_name,
        "blue_pct": blue_pct,
        "area_pct": area_pct,
        "TL_x": corners[0][0], "TL_y": corners[0][1],
        "TR_x": corners[1][0], "TR_y": corners[1][1],
        "BR_x": corners[2][0], "BR_y": corners[2][1],
        "BL_x": corners[3][0], "BL_y": corners[3][1],
    }
    x = _extract_features(dummy)
    x_scaled = (x - mean) / scale
    logit = float(np.dot(coef, x_scaled) + intercept)
    prob = 1.0 / (1.0 + np.exp(-logit))
    return prob


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    project = Path(__file__).resolve().parent.parent
    csv_path = project / "SEM_results" / "corrected" / "candidates.csv"
    model_path = project / "SEM_results" / "model.json"

    if not csv_path.exists():
        print(f"Training data not found: {csv_path}")
        print("Please run the candidate generation step first.")
        sys.exit(1)

    train(csv_path, model_path)
