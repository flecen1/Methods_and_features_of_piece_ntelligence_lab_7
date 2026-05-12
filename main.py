# -*- coding: utf-8 -*-
"""
Точка входу: оптимізація генетичним алгоритмом і опційно побудова графіка.

Приклади:
  python main.py --variant 1 --plot --generations 150
  python main.py --variant 3 --no-show --plot-file out/v3.png
"""

from __future__ import annotations

import argparse
import json

from genetic_algorithm import run_ga
from plotting import plot_variant
from variants import build_variant


def _positive_int(name: str, minimum: int):
    def _coerce(s: str) -> int:
        v = int(s)
        if v < minimum:
            raise argparse.ArgumentTypeError(f"{name} має бути >= {minimum}, отримано {v}")
        return v

    return _coerce


def main() -> None:
    p = argparse.ArgumentParser(description="Лаб. 7: генетичний алгоритм (Python)")
    p.add_argument("--variant", type=int, default=1, choices=range(1, 6), help="Номер варіанту 1..5")
    p.add_argument("--population", type=_positive_int("population", 2), default=40)
    p.add_argument("--generations", type=_positive_int("generations", 1), default=120)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--plot", action="store_true", help="Побудувати графік функції")
    p.add_argument("--plot-file", type=str, default=None, help="Зберегти графік у файл")
    p.add_argument("--no-show", action="store_true", help="Не відкривати вікно matplotlib")
    p.add_argument("--json", action="store_true", help="Вивести результат у JSON")
    args = p.parse_args()

    spec = build_variant(args.variant)
    res = run_ga(
        spec,
        population_size=args.population,
        generations=args.generations,
        seed=args.seed,
    )

    out = {
        "variant": args.variant,
        "name": spec.name,
        "mode": spec.mode,
        "bounds": [list(b) for b in spec.bounds],
        "best_point": res.best_phenotype.tolist(),
        "best_objective": res.best_objective_value,
        "generations": res.generations,
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("Варіант:", spec.id, "-", spec.name)
        print("Режим:", "мінімізація" if spec.mode == "min" else "максимізація")
        print("Межі:", spec.bounds)
        print("Найкраща точка:", res.best_phenotype)
        print("Значення цільової f:", res.best_objective_value)

    if args.plot or args.plot_file:
        try:
            plot_variant(args.variant, out_path=args.plot_file, show=not args.no_show)
        except (OSError, ValueError) as e:
            raise SystemExit(f"Помилка побудови графіка: {e}") from e


if __name__ == "__main__":
    main()
