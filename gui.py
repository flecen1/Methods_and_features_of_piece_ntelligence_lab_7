# -*- coding: utf-8 -*-
"""
Графічний інтерфейс практичної роботи 7 (завдання 4 методички).

Завдання 1–3 — через main.py; у GUI дубльовано для зручності та звіту.
Завдання 4 — робота в цьому вікні (скріншот для звіту).
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from genetic_algorithm import run_ga
from plotting import sample_1d, sample_2d
from variants import build_variant, cli_command, variant_student_summary


class Lab7GUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Практична робота 7 — генетичний алгоритм (Python)")
        self.root.geometry("1180x720")
        self.root.minsize(960, 600)

        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")

        header = ttk.Frame(self.root, padding=(10, 8))
        header.pack(fill=tk.X)
        ttk.Label(
            header,
            text="Лабораторна робота 7: дослідження ГА на задачі пошуку екстремумів",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Виконуйте завдання 1–3 у консолі (main.py) або кнопками зліва; завдання 4 — скріншот цього вікна.",
            foreground="#444",
        ).pack(anchor="w", pady=(2, 0))

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.Frame(body, padding=4, width=320)
        right = ttk.Frame(body, padding=4)
        body.add(left, weight=0)
        body.add(right, weight=1)

        # --- параметри ---
        params = ttk.LabelFrame(left, text="Параметри ГА", padding=8)
        params.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(params, text="Варіант (1–5):").grid(row=0, column=0, sticky="w")
        self.var_variant = tk.IntVar(value=1)
        sb = ttk.Spinbox(params, from_=1, to=5, textvariable=self.var_variant, width=8, command=self._on_variant_change)
        sb.grid(row=0, column=1, sticky="ew", pady=2)
        sb.bind("<FocusOut>", lambda _e: self._on_variant_change())
        sb.bind("<Return>", lambda _e: self._on_variant_change())

        ttk.Label(params, text="Популяція:").grid(row=1, column=0, sticky="w", pady=2)
        self.var_pop = tk.IntVar(value=40)
        ttk.Entry(params, textvariable=self.var_pop, width=10).grid(row=1, column=1, sticky="ew")

        ttk.Label(params, text="Поколінь:").grid(row=2, column=0, sticky="w", pady=2)
        self.var_gen = tk.IntVar(value=120)
        ttk.Entry(params, textvariable=self.var_gen, width=10).grid(row=2, column=1, sticky="ew")

        ttk.Label(params, text="Сід (опційно):").grid(row=3, column=0, sticky="w", pady=2)
        self.var_seed = tk.StringVar(value="")
        ttk.Entry(params, textvariable=self.var_seed, width=10).grid(row=3, column=1, sticky="ew")
        params.columnconfigure(1, weight=1)

        # --- опис варіанту ---
        info = ttk.LabelFrame(left, text="Ваш варіант (табл. 8.1)", padding=8)
        info.pack(fill=tk.X, pady=(0, 6))
        self.lbl_variant_info = ttk.Label(info, text="", wraplength=280, justify=tk.LEFT)
        self.lbl_variant_info.pack(anchor="w")

        # --- завдання ---
        tasks = ttk.LabelFrame(left, text="Завдання з методички", padding=8)
        tasks.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(tasks, text="1. Оптимізація (скрипт)", command=self._task1).pack(fill=tk.X, pady=2)
        ttk.Button(tasks, text="2. Графік функції", command=self._task2).pack(fill=tk.X, pady=2)
        ttk.Button(tasks, text="3. Серія запусків (3 сид)", command=self._task3).pack(fill=tk.X, pady=2)
        ttk.Button(tasks, text="4. Запуск ГА + графіки (GUI)", command=self._task4).pack(fill=tk.X, pady=2)

        util = ttk.Frame(left)
        util.pack(fill=tk.X, pady=(0, 6))
        util.columnconfigure(0, weight=1)
        util.columnconfigure(1, weight=1)
        ttk.Button(util, text="Очистити графіки", command=self._clear_plots).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(util, text="Очистити журнал", command=self._clear_log).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        ttk.Button(left, text="Очистити все", command=self._clear_all).pack(fill=tk.X, pady=(0, 6))

        log_frame = ttk.LabelFrame(left, text="Журнал (для звіту)", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.txt = tk.Text(log_frame, width=38, height=14, wrap="word", font=("Consolas", 9))
        scroll = ttk.Scrollbar(log_frame, command=self.txt.yview)
        self.txt.configure(yscrollcommand=scroll.set)
        self.txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- графіки ---
        plot_box = ttk.LabelFrame(right, text="Графіки", padding=4)
        plot_box.pack(fill=tk.BOTH, expand=True)
        self.fig = plt.Figure(figsize=(7, 6.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_box)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, plot_box).update()
        self.ax1 = None
        self.ax2 = None
        self._recreate_axes(show_hint=True)

        self.status = ttk.Label(self.root, text="Готово. Оберіть варіант і завдання.", relief=tk.SUNKEN, anchor="w")
        self.status.pack(fill=tk.X, padx=8, pady=(0, 6))

        self._on_variant_change()
        self._log("Лабораторна робота 7 — Python. Клонуйте репозиторій з GitHub (див. README).")

    def _set_status(self, text: str) -> None:
        self.status.config(text=text)

    def _log(self, s: str) -> None:
        self.txt.insert(tk.END, s + "\n")
        self.txt.see(tk.END)

    def _on_variant_change(self) -> None:
        try:
            vid = int(self.var_variant.get())
            if vid < 1 or vid > 5:
                raise ValueError
        except ValueError:
            return
        self.lbl_variant_info.config(text=variant_student_summary(vid))

    def _read_params(self) -> tuple[int, int, int, int | None]:
        vid = int(self.var_variant.get())
        pop = int(self.var_pop.get())
        gen = int(self.var_gen.get())
        seed_s = self.var_seed.get().strip()
        seed = int(seed_s) if seed_s else None
        if pop < 2:
            raise ValueError("Розмір популяції має бути не менше 2.")
        if gen < 1:
            raise ValueError("Кількість поколінь має бути не менше 1.")
        if vid < 1 or vid > 5:
            raise ValueError("Варіант має бути від 1 до 5.")
        return vid, pop, gen, seed

    def _recreate_axes(self, *, show_hint: bool = False) -> None:
        self.fig.clf()
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        self.fig.subplots_adjust(hspace=0.38)
        if show_hint:
            self.ax1.text(
                0.5, 0.55, "Завдання 2 — графік функції",
                ha="center", va="center", transform=self.ax1.transAxes, fontsize=11, alpha=0.55,
            )
            self.ax1.text(
                0.5, 0.38, "Завдання 1 / 4 — оптимізація + збіжність",
                ha="center", va="center", transform=self.ax2.transAxes, fontsize=10, alpha=0.45,
            )

    def _clear_plots(self) -> None:
        self._recreate_axes(show_hint=True)
        self.fig.tight_layout()
        self.canvas.draw()
        self._set_status("Графіки очищено.")

    def _clear_log(self) -> None:
        self.txt.delete("1.0", tk.END)

    def _clear_all(self) -> None:
        self._clear_log()
        self._clear_plots()

    def _draw_function(self, spec, res=None) -> None:
        if spec.n_vars == 1:
            xs, ys = sample_1d(spec, 400)
            self.ax1.plot(xs, ys, color="#2563eb", lw=2)
            self.ax1.set_title(f"Завдання 2: графік функції (варіант {spec.id})")
            self.ax1.set_xlabel("x")
            self.ax1.set_ylabel("y(x)")
            self.ax1.grid(True, alpha=0.3)
            if res is not None:
                self.ax1.axvline(res.best_phenotype[0], color="#dc2626", ls="--", lw=1.2, label="GA")
                self.ax1.scatter(
                    [res.best_phenotype[0]], [res.best_objective_value], color="#dc2626", s=45, zorder=5,
                )
                self.ax1.legend(loc="best")
        else:
            X, Y, Z = sample_2d(spec, 80)
            cf = self.ax1.contourf(X, Y, Z, levels=28, cmap="viridis")
            self.fig.colorbar(cf, ax=self.ax1, shrink=0.78, pad=0.02)
            self.ax1.set_title(f"Завдання 2: z(x,y), варіант {spec.id}")
            self.ax1.set_xlabel("x")
            self.ax1.set_ylabel("y")
            if res is not None:
                self.ax1.scatter(
                    [res.best_phenotype[0]], [res.best_phenotype[1]],
                    c="#dc2626", s=60, marker="*", label="GA", zorder=5,
                )
                self.ax1.legend(loc="upper right")
            self.ax1.set_aspect("equal", adjustable="box")

    def _draw_convergence(self, res) -> None:
        gens = range(1, len(res.history_best_cost) + 1)
        self.ax2.plot(list(gens), res.history_best_cost, label="Найкращий cost", color="#16a34a", lw=1.8)
        self.ax2.plot(list(gens), res.history_mean_cost, label="Середній cost", color="#ea580c", alpha=0.85)
        self.ax2.set_title("Збіжність ГА (best / mean fitness)")
        self.ax2.set_xlabel("Покоління")
        self.ax2.set_ylabel("Мінімізований cost")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc="upper right", fontsize=8)

    def _refresh_canvas(self) -> None:
        self.fig.tight_layout()
        self.canvas.draw()

    def _run_ga_safe(self, vid: int, pop: int, gen: int, seed: int | None):
        spec = build_variant(vid)
        res = run_ga(spec, population_size=pop, generations=gen, seed=seed)
        return spec, res

    def _task1(self) -> None:
        try:
            vid, pop, gen, seed = self._read_params()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        cmd = cli_command(vid, pop, gen, seed)
        self._log("\n=== ЗАВДАННЯ 1: оптимізація (скрипт) ===")
        self._log(f"Команда для звіту: {cmd}")
        try:
            spec, res = self._run_ga_safe(vid, pop, gen, seed)
        except Exception as e:
            messagebox.showerror("Помилка ГА", str(e))
            return
        self._log(f"Найкраща точка: {res.best_phenotype}")
        self._log(f"Значення f: {res.best_objective_value:.8g}")
        self._recreate_axes()
        self._draw_convergence(res)
        self.ax1.text(
            0.5, 0.5, "Завдання 1 — лише числовий результат\n(графік — у завданні 2 або 4)",
            ha="center", va="center", transform=self.ax1.transAxes, alpha=0.6,
        )
        self._refresh_canvas()
        self._set_status("Завдання 1 виконано. Скопіюйте команду та результати у звіт.")

    def _task2(self) -> None:
        try:
            vid, _, _, _ = self._read_params()
            spec = build_variant(vid)
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log("\n=== ЗАВДАННЯ 2: графік функції ===")
        self._log(cli_command(vid, int(self.var_pop.get()), int(self.var_gen.get()), None, plot=True))
        self._recreate_axes()
        self._draw_function(spec)
        self.ax2.text(
            0.5, 0.5, "Нижній графік — для завдань 1 і 4",
            ha="center", va="center", transform=self.ax2.transAxes, alpha=0.45,
        )
        out = Path("figures") / f"variant{vid}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(out, dpi=150)
        self._log(f"Збережено: {out}")
        self._refresh_canvas()
        self._set_status(f"Завдання 2: графік збережено у {out}")

    def _task3(self) -> None:
        try:
            vid, pop, gen, _ = self._read_params()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        seeds = [1, 7, 42]
        self._log("\n=== ЗАВДАННЯ 3: серія запусків (параметри ГА) ===")
        self._log(f"{'seed':<6} {'population':<12} {'generations':<12} {'точка':<28} {'f'}")
        self._log("-" * 72)
        for s in seeds:
            try:
                _, res = self._run_ga_safe(vid, pop, gen, s)
                pt = np.array2string(res.best_phenotype, precision=4, separator=", ")
                self._log(f"{s:<6} {pop:<12} {gen:<12} {pt:<28} {res.best_objective_value:.6g}")
            except Exception as e:
                self._log(f"seed={s}: помилка — {e}")
        self._log("Поясніть у звіті, чому результати можуть відрізнятися (стохастичність ГА).")
        self._set_status("Завдання 3: таблиця у журналі — вставте у звіт.")

    def _task4(self) -> None:
        try:
            vid, pop, gen, seed = self._read_params()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log("\n=== ЗАВДАННЯ 4: оптимізація через GUI ===")
        self._log("Зробіть скріншот цього вікна з графіками для звіту.")
        try:
            spec, res = self._run_ga_safe(vid, pop, gen, seed)
        except Exception as e:
            messagebox.showerror("Помилка ГА", str(e))
            return
        self._log(f"Найкраща точка: {res.best_phenotype}")
        self._log(f"Значення f: {res.best_objective_value:.8g}")
        self._recreate_axes()
        self._draw_function(spec, res)
        self._draw_convergence(res)
        self._refresh_canvas()
        self._set_status("Завдання 4 виконано. Збережіть скріншот вікна.")

    def mainloop(self) -> None:
        self.root.mainloop()


def launch() -> None:
    Lab7GUI().mainloop()


if __name__ == "__main__":
    launch()
