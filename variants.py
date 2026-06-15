# -*- coding: utf-8 -*-
"""
П’ять варіантів цільових функцій і меж пошуку для практичної роботи з ГА.

За потреби змініть вирази в цьому модулі за вказівкою викладача.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Tuple

import numpy as np

ObjectiveMode = Literal["min", "max"]


@dataclass(frozen=True)
class VariantSpec:
    id: int
    name: str
    n_vars: int
    bounds: Tuple[Tuple[float, float], ...]
    mode: ObjectiveMode
    objective: Callable[[np.ndarray], float]
    latex_hint: str


def _safe_rational_y(x: float) -> float:
    """
    y(x) = -6/(x-3) + 2/(x-1) + 8 (варіанти 2 і 4 у таблиці).

    На відрізку [-4; 8] є полюси x=1 та x=3. Для стійкої оптимізації додаємо
    великий штраф у малих околах полюсів (щоб уникнути числових збоїв).
    """
    eps = 0.08
    if abs(x - 1.0) < eps or abs(x - 3.0) < eps:
        return 1e9
    return -6.0 / (x - 3.0) + 2.0 / (x - 1.0) + 8.0


def _poly_variant1(x: float) -> float:
    """y(x) = 3x^3 - 4x^2 + 2x - 8, варіант 1 — максимум."""
    return 3.0 * x**3 - 4.0 * x**2 + 2.0 * x - 8.0


def _z_variant35(xy: np.ndarray) -> float:
    """
    z(x, y) = x^2 + y^2 - x*y*exp(-(x+y)) — типова форма для «z ... xe» у таблиці.

    Варіант 3: мінімум; варіант 5: максимум (через мінімізацію -z у обгортці).
    """
    x, y = float(xy[0]), float(xy[1])
    return x * x + y * y - x * y * np.exp(-(x + y))


def build_variant(vid: int) -> VariantSpec:
    if vid == 1:

        def obj(p: np.ndarray) -> float:
            return _poly_variant1(float(p[0]))

        return VariantSpec(
            1,
            "Поліном 1D: максимум",
            1,
            ((-6.0, -2.0),),
            "max",
            obj,
            r"y(x)=3x^3-4x^2+2x-8,\; x\in[-6,-2]",
        )
    if vid == 2:

        def obj(p: np.ndarray) -> float:
            return _safe_rational_y(float(p[0]))

        return VariantSpec(
            2,
            "Раціональна 1D: мінімум",
            1,
            ((-4.0, 8.0),),
            "min",
            obj,
            r"y(x)=-\frac{6}{x-3}+\frac{2}{x-1}+8",
        )
    if vid == 3:

        def obj(p: np.ndarray) -> float:
            return _z_variant35(p)

        return VariantSpec(
            3,
            "Двовимірна z: мінімум",
            2,
            ((-2.0, 2.0), (-2.0, 2.0)),
            "min",
            obj,
            r"z=x^2+y^2-xy\,e^{-(x+y)}",
        )
    if vid == 4:

        def obj(p: np.ndarray) -> float:
            return _safe_rational_y(float(p[0]))

        return VariantSpec(
            4,
            "Раціональна 1D: максимум",
            1,
            ((-4.0, 8.0),),
            "max",
            obj,
            r"y(x)=-\frac{6}{x-3}+\frac{2}{x-1}+8",
        )
    if vid == 5:

        def obj(p: np.ndarray) -> float:
            return _z_variant35(p)

        return VariantSpec(
            5,
            "Двовимірна z: максимум",
            2,
            ((-2.0, 2.0), (-2.0, 2.0)),
            "max",
            obj,
            r"z=x^2+y^2-xy\,e^{-(x+y)}",
        )
    raise ValueError("Невідомий варіант; оберіть 1..5")


def fitness_cost(spec: VariantSpec, pheno: np.ndarray) -> float:
    """
    Скаляр для мінімізації в ГА: для mode='min' це значення f,
    для mode='max' — -f(x).
    """
    v = spec.objective(np.asarray(pheno, dtype=float))
    return v if spec.mode == "min" else -v


def interpret_result(spec: VariantSpec, pheno: np.ndarray, best_cost: float) -> Tuple[float, float]:
    """Повертає (значення цільової f на знайденій точці, best_cost внутрішній)."""
    fval = spec.objective(np.asarray(pheno, dtype=float))
    return fval, best_cost


def variant_student_summary(vid: int) -> str:
    """Короткий опис варіанту для студента (табл. 8.1)."""
    spec = build_variant(vid)
    mode = "максимум" if spec.mode == "max" else "мінімум"
    bounds = ", ".join(f"[{a}; {b}]" for a, b in spec.bounds)
    return (
        f"Варіант {vid}: {spec.name}\n"
        f"Функція: {spec.latex_hint}\n"
        f"Область: {bounds}\n"
        f"Знайти: {mode}"
    )


def cli_command(variant: int, population: int, generations: int, seed: int | None, *, plot: bool = False) -> str:
    """Рядок команди для звіту (завдання 1–2 методички)."""
    parts = [
        "python main.py",
        f"--variant {variant}",
        f"--population {population}",
        f"--generations {generations}",
    ]
    if seed is not None:
        parts.append(f"--seed {seed}")
    if plot:
        parts.append("--plot")
        parts.append(f"--plot-file figures\\variant{variant}.png")
        parts.append("--no-show")
    return " ".join(parts)
