"""
main.py  –  Solveur de Problèmes de Transport  (interface graphique tkinter)

Utilisation :
    python main.py

Fonctionnalités :
  • Charger n'importe quel fichier .txt sans redémarrer
  • Choisir entre la proposition initiale Nord-Ouest et Balas-Hammer
  • Trace complète étape par étape dans une console défilante à largeur fixe
  • Sauvegarder la trace dans un fichier .txt
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import traceback as _tb

import transport


# ══════════════════════════════════════════════════════════════════════════════
# Application
# ══════════════════════════════════════════════════════════════════════════════

class TransportApp:
    def __init__(self, root):
        self.root     = root
        self.problem  = None
        self.filepath = None

        self.root.title("Solveur de Problèmes de Transport  –  Efrei S6 RO")
        self.root.minsize(960, 640)
        self._build_ui()
        self._status("Prêt.  Chargez un fichier .txt pour commencer.")

    # ── Construction de l'interface ───────────────────────────────────────────

    def _build_ui(self):
        # ── Barre d'outils supérieure ─────────────────────────────────────────
        toolbar = tk.Frame(self.root, bg="#2d2d2d", pady=6, padx=8)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        def btn(parent, text, cmd, bg="#555", fg="white"):
            return tk.Button(parent, text=text, command=cmd,
                             bg=bg, fg=fg, activebackground="#888",
                             font=("Segoe UI", 10, "bold"),
                             relief=tk.FLAT, padx=10, pady=3,
                             cursor="hand2")

        btn(toolbar, "📂  Charger fichier .txt", self._load_file,
            bg="#4CAF50").pack(side=tk.LEFT, padx=(0, 10))

        self.file_lbl = tk.Label(toolbar, text="Aucun fichier chargé",
                                 fg="#aaa", bg="#2d2d2d",
                                 font=("Segoe UI", 9, "italic"))
        self.file_lbl.pack(side=tk.LEFT, padx=(0, 20))

        # Sélection de l'algorithme
        tk.Label(toolbar, text="Algorithme initial :", fg="white",
                 bg="#2d2d2d", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.algo_var = tk.StringVar(value="NW")
        for text, val in [("Nord-Ouest", "NW"), ("Balas-Hammer", "BH")]:
            tk.Radiobutton(toolbar, text=text, variable=self.algo_var, value=val,
                           bg="#2d2d2d", fg="white", selectcolor="#2d2d2d",
                           activebackground="#2d2d2d", activeforeground="white",
                           font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=4)

        tk.Frame(toolbar, bg="#2d2d2d", width=20).pack(side=tk.LEFT)  # espaceur

        btn(toolbar, "▶  Résoudre",        self._solve,      bg="#2196F3").pack(side=tk.LEFT, padx=(0, 6))
        btn(toolbar, "💾  Sauvegarder",    self._save_trace, bg="#FF9800").pack(side=tk.LEFT, padx=(0, 6))
        btn(toolbar, "🗑  Effacer",         self._clear,      bg="#757575").pack(side=tk.LEFT)

        # ── Zone de texte principale ──────────────────────────────────────────
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 0))

        self.text = scrolledtext.ScrolledText(
            frame,
            font=("Courier New", 10),
            bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.NONE,
            padx=8, pady=6,
            undo=True,
        )
        self.text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Barre de défilement horizontale
        hbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL,
                            command=self.text.xview)
        self.text.configure(xscrollcommand=hbar.set)
        hbar.pack(fill=tk.X, padx=4, pady=(0, 2))

        # Balises de couleur pour la mise en évidence
        self.text.tag_config("section",  foreground="#569cd6", font=("Courier New", 10, "bold"))
        self.text.tag_config("ok",       foreground="#4ec9b0")
        self.text.tag_config("warn",     foreground="#dcdcaa")
        self.text.tag_config("improve",  foreground="#ce9178")
        self.text.tag_config("optimal",  foreground="#4ec9b0", font=("Courier New", 10, "bold"))

        # ── Barre d'état ──────────────────────────────────────────────────────
        self.status_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.status_var,
                 bd=1, relief=tk.SUNKEN, anchor=tk.W,
                 font=("Segoe UI", 9), padx=6,
                 bg="#333", fg="#ccc").pack(fill=tk.X, side=tk.BOTTOM)

    # ── Gestionnaires d'événements ────────────────────────────────────────────

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Charger un problème de transport",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "problems"),
        )
        if not path:
            return
        try:
            prob = transport.read_problem(path)
        except Exception as e:
            messagebox.showerror("Erreur de lecture",
                                 f"Impossible de lire le fichier :\n{e}")
            return

        self.problem  = prob
        self.filepath = path
        name = os.path.basename(path)
        self.file_lbl.config(text=name, fg="white")
        self._status(f"Fichier chargé : {name}   "
                     f"({prob.n} fournisseurs × {prob.m} clients)   "
                     f"Total provisions = {sum(prob.supply)}   "
                     f"Total commandes = {sum(prob.demand)}")

        # Afficher la matrice des coûts immédiatement
        self._clear()
        self._w(f"Fichier : {path}\n")
        self._w(f"Dimensions : {prob.n} fournisseurs × {prob.m} clients\n")
        balanced = sum(prob.supply) == sum(prob.demand)
        self._w(f"Problème {'équilibré ✓' if balanced else '⚠ NON ÉQUILIBRÉ'}\n")
        self._w(transport.display_cost_matrix(prob) + "\n\n")

    def _solve(self):
        if self.problem is None:
            messagebox.showwarning("Aucun fichier",
                                   "Veuillez d'abord charger un fichier .txt.")
            return

        method = self.algo_var.get()
        mname  = "Nord-Ouest" if method == "NW" else "Balas-Hammer"

        self._clear()
        self._w("╔" + "═" * 62 + "╗\n", "section")
        self._w(f"  RÉSOLUTION  –  {os.path.basename(self.filepath)}\n", "section")
        self._w(f"  Algorithme initial : {mname}\n", "section")
        self._w("╚" + "═" * 62 + "╝\n\n", "section")
        self._w(transport.display_cost_matrix(self.problem) + "\n")

        self._status(f"Résolution en cours… (algorithme : {mname})")
        self.root.update()

        try:
            for step in transport.solve(self.problem, method):
                self._render_step(step)
                self.root.update()
        except Exception as e:
            self._w(f"\n[ERREUR]\n{_tb.format_exc()}", "warn")
            messagebox.showerror("Erreur de résolution",
                                 f"Une erreur s'est produite :\n{e}")
            return

        self._status("Résolution terminée.")

    def _render_step(self, step):
        n, m = self.problem.n, self.problem.m

        # ── Proposition initiale ──────────────────────────────────────────────
        if step["type"] == "initial":
            for line in step["log"]:
                tag = "warn" if "⚠" in line else None
                self._w(line + "\n", tag)
            self._w(
                transport.display_allocation_table(
                    self.problem, step["allocation"], step["basic_cells"],
                    f"PROPOSITION INITIALE ({step['method_name']})"
                ) + "\n\n"
            )

        # ── Itération pas-à-pas ───────────────────────────────────────────────
        elif step["type"] == "iteration":
            bar = "━" * 64
            self._w(f"\n{bar}\n", "section")
            self._w(f"  ITÉRATION {step['iteration']}\n", "section")
            self._w(f"{bar}\n", "section")

            # Vérification de la dégénérescence (avant correction)
            nb_pre = len(step["pre_basic_cells"])
            needed = n + m - 1
            if nb_pre < needed:
                self._w(f"\n  ⚠ Proposition dégénérée avant correction : "
                        f"{nb_pre}/{needed} cellules de base\n", "warn")

            # Corrections du graphe (le cas échéant)
            if step["fix_log"]:
                self._w("\n  [Correction du graphe de transport]\n", "warn")
                for line in step["fix_log"]:
                    tag = "warn" if ("⚠" in line or "Cycle" in line or "Connexité" in line) else None
                    self._w(line + "\n", tag)

            nb_post = len(step["basic_cells"])
            if nb_post == needed:
                self._w(f"\n  Proposition non-dégénérée : {nb_post}/{needed} cellules ✓\n", "ok")
            else:
                self._w(f"\n  ⚠ Toujours dégénérée : {nb_post}/{needed} cellules\n", "warn")

            # Tableau d'allocation + coût
            self._w(
                transport.display_allocation_table(
                    self.problem, step["allocation"], step["basic_cells"]
                ) + "\n"
            )

            # Tableau des potentiels
            self._w(
                transport.display_potential_table(
                    self.problem, step["basic_cells"], step["u"], step["v"]
                ) + "\n"
            )

            # Tableau des coûts marginaux
            self._w(
                transport.display_marginal_table(
                    self.problem, step["basic_cells"], step["marginal"],
                    step["improving_edge"]
                ) + "\n"
            )

            # Conclusion
            if step["improving_edge"] is None:
                self._w(f"\n  ✅  Solution OPTIMALE  –  Coût = {step['cost']}\n", "optimal")
            else:
                ei, ej  = step["improving_edge"]
                mv      = step["marginal"][ei][ej]
                self._w(f"\n  Arête améliorante détectée : (P{ei+1}, C{ej+1})"
                        f"   [coût marginal = {mv}]\n", "improve")

        # ── Maximisation sur le cycle ─────────────────────────────────────────
        elif step["type"] == "improvement":
            ei, ej  = step["edge"]
            cycle   = step["cycle"]
            plus_c  = [cycle[k] for k in range(0, len(cycle), 2)]
            minus_c = [cycle[k] for k in range(1, len(cycle), 2)]
            c_str   = " → ".join(f"(P{i+1},C{j+1})" for (i, j) in cycle) \
                      + f" → (P{cycle[0][0]+1},C{cycle[0][1]+1})"

            self._w(f"\n  Ajout de (P{ei+1},C{ej+1}) dans la base\n", "improve")
            self._w(f"  Cycle : {c_str}\n")
            self._w(f"  (+) : {[f'(P{i+1},C{j+1})' for i,j in plus_c]}\n")
            self._w(f"  (-) : {[f'(P{i+1},C{j+1})' for i,j in minus_c]}\n")
            self._w(f"  δ   = {step['delta']}\n")
            if step["removed"]:
                self._w(f"  Arête retirée : "
                        f"{[f'(P{i+1},C{j+1})' for i,j in step['removed']]}\n", "warn")

    def _save_trace(self):
        content = self.text.get("1.0", tk.END)
        if not content.strip():
            messagebox.showinfo("Rien à sauvegarder", "La zone de texte est vide.")
            return

        initial = ""
        if self.filepath:
            base   = os.path.splitext(os.path.basename(self.filepath))[0]
            method = "no" if self.algo_var.get() == "NW" else "bh"
            initial = f"{base}-{method}.txt"

        path = filedialog.asksaveasfilename(
            title="Sauvegarder la trace d'exécution",
            defaultextension=".txt",
            initialfile=initial,
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
        )
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            self._status(f"Trace sauvegardée : {os.path.basename(path)}")

    def _clear(self):
        self.text.delete("1.0", tk.END)

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _w(self, text, tag=None):
        """Ajoute *text* à la console (avec balise de couleur optionnelle)."""
        self.text.insert(tk.END, text, tag or "")
        self.text.see(tk.END)

    def _status(self, msg):
        self.status_var.set(msg)


# ══════════════════════════════════════════════════════════════════════════════
# Point d'entrée
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x750")
    try:
        # Sensibilisation DPI Windows (texte net sur écrans haute résolution)
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = TransportApp(root)
    root.mainloop()
