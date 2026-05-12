# -*- coding: utf-8 -*-
"""Побудова графіків цільових функцій для звіту."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from variants import build_variant


def plot_variant(variant_id: int, *, out_path: Optional[str] = None, show: bool = True) -> None:
    import matplotlib

    if not show:
        matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    spec = build_variant(variant_id)
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = None
    try:
        if spec.n_vars == 1:
            a, b = spec.bounds[0]
            xs = np.linspace(a, b, 800)
            ys = np.array([spec.objective(np.array([x])) for x in xs], dtype=float)
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot(xs, ys, lw=2, color="#1f77b4")
            ax.set_title(f"Варіант {variant_id}: {spec.name}\n{spec.latex_hint}")
            ax.set_xlabel("x")
            ax.set_ylabel("y(x)" if variant_id in (1, 2, 4) else "f(x)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
        else:
            a1, b1 = spec.bounds[0]
            a2, b2 = spec.bounds[1]
            n = 120
            x = np.linspace(a1, b1, n)
            y = np.linspace(a2, b2, n)
            X, Y = np.meshgrid(x, y)
            flat = np.stack([X.ravel(), Y.ravel()], axis=1)
            Z = np.array([spec.objective(flat[i]) for i in range(flat.shape[0])], dtype=float).reshape(X.shape)
            fig = plt.figure(figsize=(9, 5))
            ax = fig.add_subplot(111, projection="3d")
            surf = ax.plot_surface(X, Y, Z, cmap="viridis", linewidth=0, antialiased=True, alpha=0.95)
            ax.set_title(f"Варіант {variant_id}: {spec.name}")
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z(x,y)")
            fig.colorbar(surf, shrink=0.55, aspect=18, pad=0.08)
            fig.tight_layout()

        if out_path:
            dest = Path(out_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(str(dest), dpi=150)
        if show:
            plt.show()
    finally:
        if fig is not None:
            plt.close(fig)
