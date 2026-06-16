# -*- coding: utf-8 -*-
"""
Графічний інтерфейс практичної роботи 7 — 4 завдання методички.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from genetic_algorithm import run_ga
from plotting import plot_variant, sample_1d, sample_2d
from variants import build_variant, cli_command, variant_student_summary

# Палітра
SIDEBAR = "#1e293b"
SIDEBAR_TEXT = "#f8fafc"
SIDEBAR_MUTED = "#94a3b8"
BG = "#f1f5f9"
CARD = "#ffffff"
ACCENT = "#6366f1"
ACCENT_DARK = "#4f46e5"
SUCCESS = "#22c55e"
WARN = "#f59e0b"
BORDER = "#e2e8f0"

FONT = ("Segoe UI", 10)
FONT_SM = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 13, "bold")


class Lab7GUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Лаб. 7 — Генетичний алгоритм")
        self.root.geometry("1100x700")
        self.root.minsize(920, 580)
        self.root.configure(bg=BG)

        self._step_labels: list[tk.Label] = []
        self._setup_styles()
        self._build_layout()

        self.ax_fn = None
        self.ax_cv = None
        self._recreate_axes(show_hint=True)
        self._on_variant_change()
        self._log("Крок 1 → 2 → 3 → 4. Результат копіюйте у звіт.")

    def _setup_styles(self) -> None:
        s = ttk.Style()
        if "vista" in s.theme_names():
            s.theme_use("vista")
        s.configure("Sidebar.TSpinbox", fieldbackground="#334155", foreground=SIDEBAR_TEXT)
        s.configure("Sidebar.TEntry", fieldbackground="#334155", foreground=SIDEBAR_TEXT)

    def _build_layout(self) -> None:
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        # --- бічна панель ---
        side = tk.Frame(main, bg=SIDEBAR, width=290)
        side.pack(side=tk.LEFT, fill=tk.Y)
        side.pack_propagate(False)

        tk.Label(side, text="Практична робота 7", bg=SIDEBAR, fg=SIDEBAR_TEXT, font=FONT_TITLE).pack(
            anchor="w", padx=18, pady=(18, 2)
        )
        tk.Label(
            side, text="Генетичний алгоритм", bg=SIDEBAR, fg=SIDEBAR_MUTED, font=FONT_SM,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        # кроки
        steps = tk.Frame(side, bg=SIDEBAR, padx=14)
        steps.pack(fill=tk.X, pady=(0, 12))
        for name in ("1", "2", "3", "4"):
            lbl = tk.Label(
                steps, text=name, bg="#334155", fg=SIDEBAR_MUTED,
                font=("Segoe UI", 9, "bold"), width=3, pady=4,
            )
            lbl.pack(side=tk.LEFT, padx=3)
            self._step_labels.append(lbl)

        # параметри
        pf = tk.Frame(side, bg=SIDEBAR, padx=18)
        pf.pack(fill=tk.X)

        tk.Label(pf, text="Варіант", bg=SIDEBAR, fg=SIDEBAR_MUTED, font=FONT_SM).grid(row=0, column=0, sticky="w")
        self.var_variant = tk.IntVar(value=1)
        sb = tk.Spinbox(
            pf, from_=1, to=5, width=5, textvariable=self.var_variant,
            bg="#334155", fg=SIDEBAR_TEXT, buttonbackground="#475569",
            relief=tk.FLAT, highlightthickness=0, command=self._on_variant_change,
        )
        sb.grid(row=0, column=1, sticky="e", pady=4)
        sb.bind("<FocusOut>", lambda _e: self._on_variant_change())
        sb.bind("<Return>", lambda _e: self._on_variant_change())

        self.lbl_info = tk.Label(
            pf, text="", bg=SIDEBAR, fg="#cbd5e1", justify=tk.LEFT,
            wraplength=250, font=FONT_SM,
        )
        self.lbl_info.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 10))

        self.var_pop = tk.IntVar(value=40)
        self.var_gen = tk.IntVar(value=120)
        self.var_seed = tk.StringVar(value="")
        for r, (label, var) in enumerate(
            [("Популяція", self.var_pop), ("Поколінь", self.var_gen), ("Сід", self.var_seed)],
            start=2,
        ):
            tk.Label(pf, text=label, bg=SIDEBAR, fg=SIDEBAR_MUTED, font=FONT_SM).grid(row=r, column=0, sticky="w", pady=3)
            e = tk.Entry(pf, textvariable=var, width=8, bg="#334155", fg=SIDEBAR_TEXT, relief=tk.FLAT, insertbackground="white")
            e.grid(row=r, column=1, sticky="e", pady=3)
        pf.columnconfigure(1, weight=1)

        # кнопки завдань
        tk.Label(side, text="Завдання", bg=SIDEBAR, fg=SIDEBAR_MUTED, font=FONT_SM).pack(anchor="w", padx=18, pady=(14, 6))
        bf = tk.Frame(side, bg=SIDEBAR, padx=14)
        bf.pack(fill=tk.X)

        tasks = [
            ("1  Оптимізація", self._task1, ACCENT),
            ("2  Графік функції", self._task2, "#818cf8"),
            ("3  Експеримент (3 запуски)", self._task3, "#a78bfa"),
            ("4  GUI для звіту", self._task4, SUCCESS),
        ]
        for text, cmd, color in tasks:
            tk.Button(
                bf, text=text, command=cmd, bg=color, fg="white",
                activebackground=ACCENT_DARK, activeforeground="white",
                font=FONT, relief=tk.FLAT, anchor="w", padx=12, pady=9, cursor="hand2",
            ).pack(fill=tk.X, pady=3)

        # результат
        tk.Label(side, text="Результат", bg=SIDEBAR, fg=SIDEBAR_MUTED, font=FONT_SM).pack(anchor="w", padx=18, pady=(12, 4))
        log_wrap = tk.Frame(side, bg=SIDEBAR, padx=14)
        log_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.txt = tk.Text(
            log_wrap, height=9, wrap="word", font=("Consolas", 9),
            bg="#0f172a", fg="#e2e8f0", relief=tk.FLAT, padx=8, pady=6,
        )
        self.txt.pack(fill=tk.BOTH, expand=True)

        self.status = tk.Label(
            side, text="Почніть з кнопки «1 Оптимізація»", bg="#0f172a", fg=SIDEBAR_MUTED,
            font=FONT_SM, anchor="w", padx=14, pady=8,
        )
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        # --- графіки ---
        plot_area = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        plot_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))

        self.fig = plt.Figure(figsize=(7.2, 6.0), dpi=100, facecolor=CARD)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _mark_step(self, n: int) -> None:
        for i, lbl in enumerate(self._step_labels, start=1):
            if i <= n:
                lbl.config(bg=SUCCESS if i < n else ACCENT, fg="white")
            else:
                lbl.config(bg="#334155", fg=SIDEBAR_MUTED)

    def _set_status(self, text: str) -> None:
        self.status.config(text=text)

    def _log(self, s: str) -> None:
        self.txt.insert(tk.END, s + "\n")
        self.txt.see(tk.END)

    def _on_variant_change(self) -> None:
        try:
            vid = int(self.var_variant.get())
            if 1 <= vid <= 5:
                self.lbl_info.config(text=variant_student_summary(vid))
        except ValueError:
            pass

    def _read_params(self) -> tuple[int, int, int, int | None]:
        vid = int(self.var_variant.get())
        pop = int(self.var_pop.get())
        gen = int(self.var_gen.get())
        s = self.var_seed.get().strip()
        seed = int(s) if s else None
        if pop < 2:
            raise ValueError("Популяція — мінімум 2.")
        if gen < 1:
            raise ValueError("Поколінь — мінімум 1.")
        if not 1 <= vid <= 5:
            raise ValueError("Варіант від 1 до 5.")
        return vid, pop, gen, seed

    def _style_axes(self, ax) -> None:
        ax.set_facecolor("#fafbfc")
        ax.tick_params(colors="#64748b", labelsize=8)
        ax.title.set_color("#334155")
        ax.xaxis.label.set_color("#64748b")
        ax.yaxis.label.set_color("#64748b")
        for spine in ax.spines.values():
            spine.set_color(BORDER)

    def _recreate_axes(self, *, show_hint: bool = False) -> None:
        self.fig.clf()
        self.ax_fn = self.fig.add_subplot(2, 1, 1)
        self.ax_cv = self.fig.add_subplot(2, 1, 2)
        self.fig.subplots_adjust(hspace=0.42, left=0.1, right=0.96)
        for ax in (self.ax_fn, self.ax_cv):
            self._style_axes(ax)
        if show_hint:
            self.ax_fn.text(0.5, 0.5, "Графік функції (завдання 2 і 4)", ha="center", va="center",
                            transform=self.ax_fn.transAxes, color="#94a3b8", fontsize=11)
            self.ax_cv.text(0.5, 0.5, "Збіжність ГА (завдання 1 і 4)", ha="center", va="center",
                            transform=self.ax_cv.transAxes, color="#94a3b8", fontsize=11)

    def _draw_function(self, spec, res=None) -> None:
        if spec.n_vars == 1:
            xs, ys = sample_1d(spec, 400)
            self.ax_fn.plot(xs, ys, color=ACCENT, lw=2.2)
            self.ax_fn.set_title(f"Функція — варіант {spec.id}")
            self.ax_fn.set_xlabel("x")
            self.ax_fn.grid(True, alpha=0.2, color=BORDER)
            if res is not None:
                self.ax_fn.scatter(
                    [res.best_phenotype[0]], [res.best_objective_value],
                    color="#ef4444", s=55, zorder=5, label="знайдена точка",
                )
                self.ax_fn.legend(fontsize=8)
        else:
            X, Y, Z = sample_2d(spec, 70)
            cf = self.ax_fn.contourf(X, Y, Z, levels=24, cmap="plasma")
            self.fig.colorbar(cf, ax=self.ax_fn, shrink=0.82, pad=0.02)
            self.ax_fn.set_title(f"z(x, y) — варіант {spec.id}")
            if res is not None:
                self.ax_fn.scatter(
                    [res.best_phenotype[0]], [res.best_phenotype[1]],
                    c="#ef4444", s=60, marker="*", label="GA", zorder=5,
                )
                self.ax_fn.legend(fontsize=8)
            self.ax_fn.set_aspect("equal", adjustable="box")

    def _draw_convergence(self, res) -> None:
        g = range(1, len(res.history_best_cost) + 1)
        self.ax_cv.plot(list(g), res.history_best_cost, color=SUCCESS, lw=2, label="найкращий")
        self.ax_cv.plot(list(g), res.history_mean_cost, color=WARN, lw=1.5, alpha=0.85, label="середній")
        self.ax_cv.set_title("Збіжність генетичного алгоритму")
        self.ax_cv.set_xlabel("Покоління")
        self.ax_cv.legend(fontsize=8, framealpha=0.9)
        self.ax_cv.grid(True, alpha=0.2, color=BORDER)

    def _refresh(self) -> None:
        self.fig.tight_layout()
        self.canvas.draw()

    def _task1(self) -> None:
        """Завдання 1: сценарій оптимізації (як main.py)."""
        try:
            vid, pop, gen, seed = self._read_params()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log(f"\n── Завдання 1 ──\n{cli_command(vid, pop, gen, seed)}")
        try:
            spec = build_variant(vid)
            res = run_ga(spec, population_size=pop, generations=gen, seed=seed)
        except Exception as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log(f"Точка: {res.best_phenotype}")
        self._log(f"f = {res.best_objective_value:.8g}")
        self._recreate_axes()
        self._draw_convergence(res)
        self._refresh()
        self._mark_step(1)
        self._set_status("Завдання 1 ✓ — скопіюйте команду і результат у звіт.")

    def _task2(self) -> None:
        """Завдання 2: графік функції у figures/variantN.png."""
        try:
            vid, pop, gen, _ = self._read_params()
            spec = build_variant(vid)
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log(f"\n── Завдання 2 ──\n{cli_command(vid, pop, gen, None, plot=True)}")
        out = Path("figures") / f"variant{vid}.png"
        try:
            plot_variant(vid, out_path=str(out), show=False)
        except Exception as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._recreate_axes()
        self._draw_function(spec)
        self._log(f"Збережено: {out}")
        self._refresh()
        self._mark_step(2)
        self._set_status("Завдання 2 ✓ — вставте figures\\variantN.png у звіт.")

    def _task3(self) -> None:
        """Завдання 3: три запуски з різними параметрами ГА (як у методичці)."""
        try:
            vid, pop, gen, _ = self._read_params()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        spec = build_variant(vid)
        runs = [
            (1, pop, gen),
            (7, pop, gen),
            (42, 80, 150),
        ]
        self._log("\n── Завдання 3 ──")
        self._log(f"{'seed':<6} {'pop':<6} {'gen':<6} {'точка':<22} f")
        self._log("-" * 58)
        for seed, p, g in runs:
            try:
                res = run_ga(spec, population_size=p, generations=g, seed=seed)
                pt = str(res.best_phenotype.round(4))
                self._log(f"{seed:<6} {p:<6} {g:<6} {pt:<22} {res.best_objective_value:.6g}")
            except Exception as e:
                self._log(f"seed={seed}: {e}")
        self._log("Поясніть у звіті: чому результати можуть відрізнятися.")
        self._mark_step(3)
        self._set_status("Завдання 3 ✓ — таблиця готова для звіту.")

    def _task4(self) -> None:
        """Завдання 4: оптимізація через GUI + скріншот."""
        try:
            vid, pop, gen, seed = self._read_params()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log("\n── Завдання 4 (GUI) ──")
        self._log("Зробіть скріншот цього вікна для звіту.")
        try:
            spec = build_variant(vid)
            res = run_ga(spec, population_size=pop, generations=gen, seed=seed)
        except Exception as e:
            messagebox.showerror("Помилка", str(e))
            return
        self._log(f"Точка: {res.best_phenotype}")
        self._log(f"f = {res.best_objective_value:.8g}")
        self._recreate_axes()
        self._draw_function(spec, res)
        self._draw_convergence(res)
        self._refresh()
        self._mark_step(4)
        self._set_status("Завдання 4 ✓ — збережіть скріншот вікна.")

    def mainloop(self) -> None:
        self.root.mainloop()


def launch() -> None:
    Lab7GUI().mainloop()


if __name__ == "__main__":
    launch()
