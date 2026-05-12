# -*- coding: utf-8 -*-
"""
Графічний інтерфейс для запуску ГА та перегляду графіків.

Параметри популяції, поколінь, сід, варіант — у формі; після «Запустити ГА»
показуються результат і графіки: поверхня/крива функції та хід збіжності.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from genetic_algorithm import run_ga
from variants import build_variant


class Lab7GUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Лаб. 7 — генетичний алгоритм (Python)")
        self.root.geometry("1100x640")

        frm = ttk.Frame(self.root, padding=8)
        frm.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(frm, text="Варіант (1–5)").grid(row=0, column=0, sticky="w")
        self.var_variant = tk.IntVar(value=1)
        ttk.Spinbox(frm, from_=1, to=5, textvariable=self.var_variant, width=6).grid(row=0, column=1)

        ttk.Label(frm, text="Розмір популяції").grid(row=1, column=0, sticky="w", pady=4)
        self.var_pop = tk.IntVar(value=40)
        ttk.Entry(frm, textvariable=self.var_pop, width=8).grid(row=1, column=1)

        ttk.Label(frm, text="Поколінь").grid(row=2, column=0, sticky="w", pady=4)
        self.var_gen = tk.IntVar(value=120)
        ttk.Entry(frm, textvariable=self.var_gen, width=8).grid(row=2, column=1)

        ttk.Label(frm, text="Сід (опційно)").grid(row=3, column=0, sticky="w", pady=4)
        self.var_seed = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.var_seed, width=8).grid(row=3, column=1)
        hint = ttk.Label(
            frm,
            text="Порожній сід → кожен запуск інший (так і має бути у ГА).\n"
            "Той самий сід → той самий результат.",
            wraplength=220,
            font=("Segoe UI", 8),
            foreground="#555",
        )
        hint.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Button(frm, text="Запустити ГА", command=self._run).grid(row=5, column=0, columnspan=2, pady=(8, 4), sticky="ew")

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        ttk.Button(btn_row, text="Очистити графіки", command=self._clear_plots).grid(row=0, column=0, padx=(0, 2), sticky="ew")
        ttk.Button(btn_row, text="Очистити журнал", command=self._clear_log).grid(row=0, column=1, padx=(2, 0), sticky="ew")
        ttk.Button(frm, text="Очистити все", command=self._clear_all).grid(row=7, column=0, columnspan=2, pady=(0, 6), sticky="ew")

        self.txt = tk.Text(frm, width=42, height=20, wrap="word")
        self.txt.grid(row=8, column=0, columnspan=2, pady=4)

        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.fig = plt.Figure(figsize=(6.5, 6.2))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax1 = None  # type: ignore[assignment]
        self.ax2 = None  # type: ignore[assignment]
        self._recreate_axes()

    def _log(self, s: str) -> None:
        self.txt.insert(tk.END, s + "\n")
        self.txt.see(tk.END)

    def _recreate_axes(self) -> None:
        """Повністю пересоздає осі фігури (colorbar додає окремі axes — clf їх прибирає)."""
        self.fig.clf()
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        self.fig.subplots_adjust(hspace=0.35)

    def _clear_plots(self) -> None:
        self._recreate_axes()
        self.ax1.text(0.5, 0.5, "Натисніть «Запустити ГА»", ha="center", va="center", transform=self.ax1.transAxes, alpha=0.45)
        self.fig.tight_layout()
        self.canvas.draw()

    def _clear_log(self) -> None:
        self.txt.delete("1.0", tk.END)

    def _clear_all(self) -> None:
        self._clear_log()
        self._clear_plots()

    def _run(self) -> None:
        try:
            vid = int(self.var_variant.get())
            pop = int(self.var_pop.get())
            gen = int(self.var_gen.get())
            seed_s = self.var_seed.get().strip()
            seed = int(seed_s) if seed_s else None
        except ValueError:
            messagebox.showerror("Помилка", "Перевірте числові поля.")
            return

        if pop < 2:
            messagebox.showerror("Помилка", "Розмір популяції має бути не менше 2.")
            return
        if gen < 1:
            messagebox.showerror("Помилка", "Кількість поколінь має бути не менше 1.")
            return

        try:
        except Exception as e:
            messagebox.showerror("Помилка", str(e))
            return

        self._log("—" * 28)
        self._log(f"Варіант {vid}: {spec.name} ({spec.mode})")
        try:
            res = run_ga(spec, population_size=pop, generations=gen, seed=seed)
        except Exception as e:
            messagebox.showerror("Помилка ГА", str(e))
            return

        self._log(f"Найкраща точка: {res.best_phenotype}")
        self._log(f"Значення f: {res.best_objective_value:.8g}")
        self._log(f"Внутрішній cost: {res.best_internal_cost:.8g}")

        self._recreate_axes()

        if spec.n_vars == 1:
            a, b = spec.bounds[0]
            xs = np.linspace(a, b, 400)
            ys = np.array([spec.objective(np.array([x])) for x in xs])
            self.ax1.plot(xs, ys, color="#1f77b4", lw=2)
            self.ax1.axvline(res.best_phenotype[0], color="crimson", ls="--", lw=1.2, label="GA точка")
            self.ax1.scatter([res.best_phenotype[0]], [res.best_objective_value], color="crimson", s=40, zorder=5)
            self.ax1.set_title("Цільова функція та знайдена точка")
            self.ax1.set_xlabel("x")
            self.ax1.legend(loc="best")
            self.ax1.grid(True, alpha=0.3)
        else:
            a1, b1 = spec.bounds[0]
            a2, b2 = spec.bounds[1]
            n = 80
            x = np.linspace(a1, b1, n)
            y = np.linspace(a2, b2, n)
            X, Y = np.meshgrid(x, y)
            flat = np.stack([X.ravel(), Y.ravel()], axis=1)
            Z = np.array([spec.objective(flat[i]) for i in range(flat.shape[0])], dtype=float).reshape(X.shape)
            cs = self.ax1.contourf(X, Y, Z, levels=28, cmap="viridis")
            self.fig.colorbar(cs, ax=self.ax1, shrink=0.75)
            self.ax1.scatter(
                [res.best_phenotype[0]],
                [res.best_phenotype[1]],
                c="red",
                s=50,
                marker="*",
                label="GA",
            )
            self.ax1.set_title("Контури z(x,y) та знайдена точка")
            self.ax1.set_xlabel("x")
            self.ax1.set_ylabel("y")
            self.ax1.legend()
            self.ax1.set_aspect("equal", adjustable="box")

        gens = range(1, len(res.history_best_cost) + 1)
        self.ax2.plot(list(gens), res.history_best_cost, label="Найкращий cost", color="#2ca02c")
        self.ax2.plot(list(gens), res.history_mean_cost, label="Середній cost", color="#ff7f0e", alpha=0.85)
        self.ax2.set_title("Збіжність: найкращий і середній cost по поколіннях")
        self.ax2.set_xlabel("Покоління")
        self.ax2.set_ylabel("Мінімізований cost")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc="upper right", fontsize=8)

        self.fig.tight_layout()
        try:
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Помилка графіка", str(e))

    def mainloop(self) -> None:
        self.root.mainloop()


def launch() -> None:
    Lab7GUI().mainloop()


if __name__ == "__main__":
    launch()
