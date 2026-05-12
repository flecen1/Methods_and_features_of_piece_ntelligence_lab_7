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


def main() -> None:
    p = argparse.ArgumentParser(description="Лаб. 7: генетичний алгоритм (Python)")
    p.add_argument("--variant", type=int, default=1, choices=range(1, 6), help="Номер варіанту 1..5")
    p.add_argument("--population", type=int, default=40)
    p.add_argument("--generations", type=int, default=120)
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
        plot_variant(args.variant, out_path=args.plot_file, show=not args.no_show)


if __name__ == "__main__":
    main()
