"""
transport.py  –  Transportation Problem Solver
Algorithms: North-West Corner, Balas-Hammer, Stepping-Stone with Potentials (MODI)
"""

from collections import defaultdict, deque


# ══════════════════════════════════════════════════════════════════════════════
# Data structure
# ══════════════════════════════════════════════════════════════════════════════

class TransportProblem:
    """Balanced transportation problem: n suppliers × m clients."""

    def __init__(self, n, m, costs, supply, demand):
        self.n = n           # number of suppliers (rows)
        self.m = m           # number of clients   (columns)
        self.costs  = costs  # list[n][m]  – unit transport costs
        self.supply = supply # list[n]     – provisions Pi
        self.demand = demand # list[m]     – commandes Cj


# ══════════════════════════════════════════════════════════════════════════════
# File I/O
# ══════════════════════════════════════════════════════════════════════════════

def read_problem(filepath):
    """Read a transport problem from a .txt file.

    File format:
        n m
        a11 a12 … a1m  P1
        …
        an1 an2 … anm  Pn
        C1  C2  … Cm
    """
    with open(filepath, "r", encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh if ln.strip()]

    n, m = map(int, lines[0].split())

    costs, supply = [], []
    for i in range(1, n + 1):
        row = list(map(int, lines[i].split()))
        costs.append(row[:m])
        supply.append(row[m])

    demand = list(map(int, lines[n + 1].split()))
    return TransportProblem(n, m, costs, supply, demand)


# ══════════════════════════════════════════════════════════════════════════════
# Display helpers
# ══════════════════════════════════════════════════════════════════════════════

def _col_w(values, min_w=3):
    """Minimum column width that fits every value (plus 1 space padding)."""
    if not values:
        return min_w + 1
    return max(min_w, max(len(str(v)) for v in values if v is not None)) + 1


def display_cost_matrix(problem):
    """Return a nicely formatted string of the cost matrix."""
    n, m = problem.n, problem.m
    flat = (list(problem.supply) + list(problem.demand)
            + [c for row in problem.costs for c in row])
    w  = _col_w(flat)
    lw = max(_col_w([f"P{n}", f"C{m}", "Cj", "Pi"]), w)

    header = f"{'':>{lw}}" + "".join(f"  {'C'+str(j+1):>{w}}" for j in range(m)) \
             + f"  {'Pi':>{w}}"
    sep    = "─" * (lw + (w + 2) * (m + 1))

    rows = ["\n╔══ MATRICE DES COÛTS ══╗", header, sep]
    for i in range(n):
        rows.append(f"{'P'+str(i+1):>{lw}}"
                    + "".join(f"  {problem.costs[i][j]:>{w}}" for j in range(m))
                    + f"  {problem.supply[i]:>{w}}")
    rows += [sep, f"{'Cj':>{lw}}" + "".join(f"  {problem.demand[j]:>{w}}" for j in range(m))]
    return "\n".join(rows)


def display_allocation_table(problem, allocation, basic_cells,
                              title="PROPOSITION DE TRANSPORT"):
    """Return a formatted allocation table (basic cells shown, others blank)."""
    n, m = problem.n, problem.m
    vals = [allocation[i][j] for (i, j) in basic_cells if allocation[i][j] is not None]
    w  = _col_w(list(problem.supply) + list(problem.demand) + vals)
    lw = max(_col_w([f"P{n}", "Cj", "Pi"]), w)

    header = f"{'':>{lw}}" + "".join(f"  {'C'+str(j+1):>{w}}" for j in range(m)) \
             + f"  {'Pi':>{w}}"
    sep    = "─" * (lw + (w + 2) * (m + 1))

    rows = [f"\n╔══ {title} ══╗", header, sep]
    for i in range(n):
        r = f"{'P'+str(i+1):>{lw}}"
        for j in range(m):
            if (i, j) in basic_cells:
                v = allocation[i][j] if allocation[i][j] is not None else 0
                r += f"  {v:>{w}}"
            else:
                r += f"  {'':>{w}}"
        r += f"  {problem.supply[i]:>{w}}"
        rows.append(r)
    rows += [sep,
             f"{'Cj':>{lw}}" + "".join(f"  {problem.demand[j]:>{w}}" for j in range(m))]
    cost = compute_total_cost(problem, allocation)
    rows.append(f"\n  Coût total : {cost}")
    return "\n".join(rows)


def display_potential_table(problem, basic_cells, u, v):
    """Return the potential-cost table  (ui + vj)."""
    n, m = problem.n, problem.m
    pot = [[u[i] + v[j] if (u[i] is not None and v[j] is not None) else None
            for j in range(m)] for i in range(n)]
    flat = [x for x in list(u) + list(v) + [pot[i][j] for i in range(n) for j in range(m)]
            if x is not None]
    w = _col_w(flat)

    # Build column headers:  "C1(v)"
    col_hdrs = [f"C{j+1}({'?' if v[j] is None else v[j]})" for j in range(m)]
    lw = max(_col_w([f"P{n}(u)", "ui\\vj"] + col_hdrs), w)

    rows = ["\n╔══ TABLE DES COÛTS POTENTIELS  (ui + vj) ══╗"]
    u_line = "  Potentiels lignes  : " + "   ".join(
        f"u{i+1}={'?' if u[i] is None else u[i]}" for i in range(n))
    v_line = "  Potentiels colonnes: " + "   ".join(
        f"v{j+1}={'?' if v[j] is None else v[j]}" for j in range(m))
    rows += [u_line, v_line, ""]

    header = f"{'ui\\vj':>{lw}}" + "".join(f"  {h:>{w}}" for h in col_hdrs)
    sep    = "─" * (lw + (w + 2) * m)
    rows  += [header, sep]

    for i in range(n):
        lbl = f"P{i+1}({'?' if u[i] is None else u[i]})"
        r   = f"{lbl:>{lw}}"
        for j in range(m):
            val = pot[i][j]
            r  += f"  {str(val) if val is not None else '?':>{w}}"
        rows.append(r)
    return "\n".join(rows)


def display_marginal_table(problem, basic_cells, marginal, improving_edge=None):
    """Return the marginal-cost table  (aij − ui − vj).
    Basic cells show '---'; the best improving edge is bracketed if provided."""
    n, m = problem.n, problem.m
    flat = [marginal[i][j] for i in range(n) for j in range(m)
            if marginal[i][j] is not None]
    w  = _col_w(flat) if flat else 5
    lw = _col_w([f"P{n}"])

    header = f"{'':>{lw}}" + "".join(f"  {'C'+str(j+1):>{w}}" for j in range(m))
    sep    = "─" * (lw + (w + 2) * m)
    rows   = ["\n╔══ TABLE DES COÛTS MARGINAUX  (aij − ui − vj) ══╗", header, sep]

    for i in range(n):
        r = f"{'P'+str(i+1):>{lw}}"
        for j in range(m):
            if (i, j) in basic_cells:
                r += f"  {'---':>{w}}"
            elif marginal[i][j] is not None:
                s = str(marginal[i][j])
                if improving_edge == (i, j):
                    s = f"[{s}]"
                r += f"  {s:>{w}}"
            else:
                r += f"  {'?':>{w}}"
        rows.append(r)
    return "\n".join(rows)


# ══════════════════════════════════════════════════════════════════════════════
# Cost calculation
# ══════════════════════════════════════════════════════════════════════════════

def compute_total_cost(problem, allocation):
    """Sum of  aij × bij  for all basic cells with positive allocation."""
    total = 0
    for i in range(problem.n):
        for j in range(problem.m):
            v = allocation[i][j]
            if v is not None and v > 0:
                total += problem.costs[i][j] * v
    return total


# ══════════════════════════════════════════════════════════════════════════════
# Initial proposals
# ══════════════════════════════════════════════════════════════════════════════

def north_west(problem):
    """North-West Corner method.
    Returns (allocation, basic_cells, log_lines)."""
    n, m   = problem.n, problem.m
    supply = list(problem.supply)
    demand = list(problem.demand)
    alloc  = [[None] * m for _ in range(n)]
    basic  = set()
    log    = ["\n══ MÉTHODE NORD-OUEST ══"]

    i, j = 0, 0
    while i < n and j < m:
        qty        = min(supply[i], demand[j])
        alloc[i][j] = qty
        basic.add((i, j))
        supply[i] -= qty
        demand[j] -= qty
        log.append(f"  Alloc {qty:>7} → (P{i+1}, C{j+1})"
                   f"    [P{i+1} restant={supply[i]},  C{j+1} restant={demand[j]}]")

        if supply[i] == 0 and demand[j] == 0:
            if i + 1 < n or j + 1 < m:
                log.append(f"  ⚠ Dégénérescence : P{i+1} et C{j+1} épuisés simultanément")
            i += 1
            j += 1
        elif supply[i] == 0:
            i += 1
        else:
            j += 1

    _log_degeneracy(log, basic, n, m)
    return alloc, basic, log


def balas_hammer(problem):
    """Balas-Hammer method.
    Returns (allocation, basic_cells, log_lines)."""
    n, m       = problem.n, problem.m
    supply     = list(problem.supply)
    demand     = list(problem.demand)
    alloc      = [[None] * m for _ in range(n)]
    basic      = set()
    row_active = [True] * n
    col_active = [True] * m
    log        = ["\n══ MÉTHODE BALAS-HAMMER ══"]
    step       = 0

    while True:
        ar = [i for i in range(n) if row_active[i]]
        ac = [j for j in range(m) if col_active[j]]
        if not ar or not ac:
            break

        # Penalties
        rp = {}
        for i in ar:
            c = sorted(problem.costs[i][j] for j in ac)
            rp[i] = (c[1] - c[0]) if len(c) >= 2 else c[0]
        cp = {}
        for j in ac:
            c = sorted(problem.costs[i][j] for i in ar)
            cp[j] = (c[1] - c[0]) if len(c) >= 2 else c[0]

        step += 1
        log.append(f"\n  ── Étape {step} ──")
        log.append("  Pén. lignes   : " + "   ".join(f"P{i+1}={rp[i]}" for i in ar))
        log.append("  Pén. colonnes : " + "   ".join(f"C{j+1}={cp[j]}" for j in ac))

        max_r = max(rp.values())
        max_c = max(cp.values())
        pen   = max(max_r, max_c)

        best_rows = [i for i, p in rp.items() if p == pen]
        best_cols = [j for j, p in cp.items() if p == pen]
        msg = f"  Pénalité max = {pen}  →  "
        if best_rows:
            msg += f"lignes {[f'P{i+1}' for i in best_rows]}"
        if best_cols:
            msg += ("  +  " if best_rows else "") + \
                   f"colonnes {[f'C{j+1}' for j in best_cols]}"
        log.append(msg)

        if max_r >= max_c:
            ri = best_rows[0]
            ci = min(ac, key=lambda j: problem.costs[ri][j])
            log.append(f"  Choix ligne P{ri+1}  → cellule min : "
                       f"(P{ri+1}, C{ci+1})  coût={problem.costs[ri][ci]}")
        else:
            ci = best_cols[0]
            ri = min(ar, key=lambda i: problem.costs[i][ci])
            log.append(f"  Choix colonne C{ci+1}  → cellule min : "
                       f"(P{ri+1}, C{ci+1})  coût={problem.costs[ri][ci]}")

        qty         = min(supply[ri], demand[ci])
        alloc[ri][ci] = qty
        basic.add((ri, ci))
        supply[ri] -= qty
        demand[ci] -= qty
        log.append(f"  Alloc {qty:>7} → (P{ri+1}, C{ci+1})"
                   f"    [P{ri+1} restant={supply[ri]},  C{ci+1} restant={demand[ci]}]")

        degen = supply[ri] == 0 and demand[ci] == 0
        if supply[ri] == 0:
            row_active[ri] = False
        if demand[ci] == 0:
            col_active[ci] = False
        if degen and any(row_active) and any(col_active):
            log.append(f"  ⚠ Dégénérescence : P{ri+1} et C{ci+1} épuisés simultanément")

    _log_degeneracy(log, basic, n, m)
    return alloc, basic, log


def _log_degeneracy(log, basic, n, m):
    needed = n + m - 1
    got    = len(basic)
    log.append(f"\n  → {got} cellules de base  (requis : {needed})")
    if got < needed:
        log.append(f"  ⚠ Solution dégénérée : {needed - got} cellule(s) manquante(s)")


# ══════════════════════════════════════════════════════════════════════════════
# Graph algorithms (BFS)
# ══════════════════════════════════════════════════════════════════════════════

def _adj(basic_cells, n):
    """Adjacency list for the bipartite graph.
    Row i  ↔  node i ;  Column j  ↔  node n+j."""
    g = defaultdict(list)
    for (i, j) in basic_cells:
        g[i].append(n + j)
        g[n + j].append(i)
    return g


def detect_cycle_bfs(basic_cells, n, m):
    """Detect a cycle using BFS on the bipartite graph.
    Returns a list of (row, col) cells forming the cycle, or None."""
    g      = _adj(basic_cells, n)
    parent = {}   # node → parent  (None for BFS root)

    for start in range(n + m):
        if start in parent:
            continue
        parent[start] = None
        queue = deque([start])

        while queue:
            u = queue.popleft()
            for v in g[u]:
                if v not in parent:
                    parent[v] = u
                    queue.append(v)
                elif parent[u] != v:
                    # Back-edge  u — v  found → reconstruct the cycle
                    # 1. Ancestor chains
                    def chain(x):
                        c = []
                        while x is not None:
                            c.append(x)
                            x = parent[x]
                        return c
                    cu, cv   = chain(u), chain(v)
                    set_u    = set(cu)
                    lca      = next(x for x in cv if x in set_u)

                    # 2. Path  lca → … → u
                    pu = []
                    x  = u
                    while x != lca:
                        pu.append(x); x = parent[x]
                    pu.append(lca)
                    pu.reverse()          # [lca, …, u]

                    # 3. Path  v → … → child-of-lca
                    pv = []
                    x  = v
                    while x != lca:
                        pv.append(x); x = parent[x]
                    # pv = [v, …, first node after lca]

                    cycle_nodes = pu + pv
                    L           = len(cycle_nodes)
                    cells       = []
                    for k in range(L):
                        a, b = cycle_nodes[k], cycle_nodes[(k + 1) % L]
                        cells.append((a, b - n) if a < n else (b, a - n))
                    return cells
    return None


def maximize_on_cycle(allocation, basic_cells, cycle_cells):
    """Apply the stepping-stone maximisation on *cycle_cells*.
    cycle_cells[0] is the entering edge (+); alternating signs follow.
    Returns (new_alloc, new_basic, removed_cells, delta)."""
    alloc  = [row[:] for row in allocation]
    basic  = set(basic_cells)

    plus_c  = [cycle_cells[k] for k in range(0, len(cycle_cells), 2)]
    minus_c = [cycle_cells[k] for k in range(1, len(cycle_cells), 2)]

    delta = min((alloc[i][j] or 0) for (i, j) in minus_c)

    for (i, j) in plus_c:
        alloc[i][j] = (alloc[i][j] or 0) + delta
        basic.add((i, j))
    for (i, j) in minus_c:
        alloc[i][j] = (alloc[i][j] or 0) - delta

    # Remove exactly one leaving arc (the last minus cell at 0)
    zeros   = [(i, j) for (i, j) in minus_c if alloc[i][j] == 0]
    removed = []
    if zeros:
        leaving        = zeros[-1]
        basic.discard(leaving)
        alloc[leaving[0]][leaving[1]] = None
        removed = [leaving]

    return alloc, basic, removed, delta


def check_connectivity_bfs(basic_cells, n, m):
    """Return (is_connected, list_of_component_sets) using BFS."""
    g       = _adj(basic_cells, n)
    visited = set()
    comps   = []

    for start in range(n + m):
        if start in visited:
            continue
        comp  = set()
        queue = deque([start])
        visited.add(start)
        comp.add(start)
        while queue:
            u = queue.popleft()
            for v in g[u]:
                if v not in visited:
                    visited.add(v)
                    comp.add(v)
                    queue.append(v)
        comps.append(comp)

    return len(comps) == 1, comps


def fix_graph(problem, allocation, basic_cells):
    """Ensure the transport graph is a spanning tree (acyclic + connected).
    Returns (allocation, basic_cells, log_lines)."""
    n, m  = problem.n, problem.m
    alloc = [row[:] for row in allocation]
    basic = set(basic_cells)
    log   = []

    # ── 1. Remove cycles ────────────────────────────────────────────────────
    nc = 0
    while True:
        cycle = detect_cycle_bfs(basic, n, m)
        if cycle is None:
            break
        nc += 1
        c_str   = " → ".join(f"(P{i+1},C{j+1})" for (i, j) in cycle) \
                  + f" → (P{cycle[0][0]+1},C{cycle[0][1]+1})"
        plus_c  = [cycle[k] for k in range(0, len(cycle), 2)]
        minus_c = [cycle[k] for k in range(1, len(cycle), 2)]

        log.append(f"\n  [Cycle {nc}]  {c_str}")
        log.append(f"     (+) : {[f'(P{i+1},C{j+1})' for i,j in plus_c]}")
        log.append(f"     (-) : {[f'(P{i+1},C{j+1})' for i,j in minus_c]}")

        alloc, basic, removed, delta = maximize_on_cycle(alloc, basic, cycle)
        log.append(f"     δ = {delta}")
        log.append(f"     Arête retirée : {[f'(P{i+1},C{j+1})' for i,j in removed]}")

    if nc:
        log.append(f"\n  → Graphe acyclique  ({nc} cycle(s) supprimé(s))")

    # ── 2. Fix connectivity ─────────────────────────────────────────────────
    added = 0
    while len(basic) < n + m - 1:
        ok, comps = check_connectivity_bfs(basic, n, m)
        if ok:
            break

        def cname(comp):
            rs = [f"P{i+1}" for i in sorted(x for x in comp if x < n)]
            cs = [f"C{j+1}" for j in sorted(x - n for x in comp if x >= n)]
            return "{" + ", ".join(rs + cs) + "}"

        log.append(f"\n  [Connexité]  {len(comps)} composantes : "
                   + "  |  ".join(cname(c) for c in comps))

        cid = {node: k for k, comp in enumerate(comps) for node in comp}

        best, best_c = None, float("inf")
        for i in range(n):
            for j in range(m):
                if (i, j) not in basic and cid[i] != cid[n + j]:
                    if problem.costs[i][j] < best_c:
                        best_c, best = problem.costs[i][j], (i, j)
        if best is None:
            break
        ei, ej      = best
        alloc[ei][ej] = 0
        basic.add(best)
        added += 1
        log.append(f"  → Arête ajoutée (alloc=0) : "
                   f"(P{ei+1},C{ej+1})  coût={problem.costs[ei][ej]}")

    return alloc, basic, log


# ══════════════════════════════════════════════════════════════════════════════
# Potential method  (MODI)
# ══════════════════════════════════════════════════════════════════════════════

def compute_potentials(problem, basic_cells):
    """Compute row potentials u[] and column potentials v[] (MODI / u-v method).
    Sets u[0] = 0 then propagates through the spanning tree via BFS."""
    n, m = problem.n, problem.m
    u    = [None] * n
    v    = [None] * m
    u[0] = 0

    g = defaultdict(list)
    for (i, j) in basic_cells:
        g[("r", i)].append(("c", j))
        g[("c", j)].append(("r", i))

    queue   = deque([("r", 0)])
    visited = {("r", 0)}

    while queue:
        t, idx = queue.popleft()
        for nt, nidx in g[(t, idx)]:
            if (nt, nidx) not in visited:
                visited.add((nt, nidx))
                if t == "r":               # row → column
                    v[nidx] = problem.costs[idx][nidx] - u[idx]
                else:                      # column → row
                    u[nidx] = problem.costs[nidx][idx] - v[idx]
                queue.append((nt, nidx))

    return u, v


def compute_marginal_costs(problem, basic_cells, u, v):
    """Marginal cost for every non-basic cell:  aij − ui − vj."""
    n, m = problem.n, problem.m
    mg   = [[None] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            if (i, j) not in basic_cells and u[i] is not None and v[j] is not None:
                mg[i][j] = problem.costs[i][j] - u[i] - v[j]
    return mg


def find_improving_edge(basic_cells, marginal):
    """Return the non-basic cell with the most negative marginal cost, or None."""
    best, best_v = None, 0
    for i, row in enumerate(marginal):
        for j, val in enumerate(row):
            if val is not None and val < best_v:
                best_v, best = val, (i, j)
    return best


def find_cycle_for_edge(basic_cells, i0, j0, n, m):
    """Find the unique cycle created by adding (i0, j0) to the spanning tree.
    Returns cycle cells with (i0, j0) first (the entering / '+' edge)."""
    g     = _adj(basic_cells, n)
    start = i0
    end   = n + j0

    par = {start: None}
    q   = deque([start])
    while q:
        u = q.popleft()
        if u == end:
            break
        for vv in g[u]:
            if vv not in par:
                par[vv] = u
                q.append(vv)

    # Reconstruct path  start → end
    path = []
    nd   = end
    while nd is not None:
        path.append(nd)
        nd = par.get(nd)
    path.reverse()   # [start=i0, …, n+j0]

    # Entering edge first (gets '+')
    cycle = [(i0, j0)]
    for k in range(len(path) - 1):
        a, b = path[k], path[k + 1]
        cycle.append((a, b - n) if a < n else (b, a - n))
    return cycle


# ══════════════════════════════════════════════════════════════════════════════
# Main solve generator
# ══════════════════════════════════════════════════════════════════════════════

def solve(problem, method="NW"):
    """Generator that yields step-dictionaries for each phase of the solution.

    Step types:
      'initial'     – initial proposal (NW or BH)
      'iteration'   – one stepping-stone iteration (potentials + marginals)
      'improvement' – one cycle maximisation (entering/leaving arcs)
    """
    if method == "NW":
        alloc, basic, init_log = north_west(problem)
        mname = "Nord-Ouest"
    else:
        alloc, basic, init_log = balas_hammer(problem)
        mname = "Balas-Hammer"

    yield {"type": "initial", "method_name": mname,
           "allocation": [r[:] for r in alloc],
           "basic_cells": frozenset(basic), "log": init_log}

    for iteration in range(1, 1001):

        # Save state before fix (for degeneracy display)
        pre_alloc = [r[:] for r in alloc]
        pre_basic = frozenset(basic)
        pre_cost  = compute_total_cost(problem, alloc)

        # Fix graph (cycles + connectivity)
        alloc, basic, fix_log = fix_graph(problem, alloc, basic)

        cost  = compute_total_cost(problem, alloc)
        u, v  = compute_potentials(problem, basic)
        mg    = compute_marginal_costs(problem, basic, u, v)
        edge  = find_improving_edge(basic, mg)

        yield {"type": "iteration", "iteration": iteration,
               "pre_allocation": pre_alloc, "pre_basic_cells": pre_basic,
               "pre_cost": pre_cost,
               "allocation": [r[:] for r in alloc],
               "basic_cells": frozenset(basic), "cost": cost,
               "fix_log": fix_log,
               "u": list(u), "v": list(v),
               "marginal": [r[:] for r in mg],
               "improving_edge": edge}

        if edge is None:
            break   # Optimal

        # Maximise on the cycle formed by the entering edge
        i0, j0  = edge
        cycle   = find_cycle_for_edge(basic, i0, j0, problem.n, problem.m)
        alloc, basic, removed, delta = maximize_on_cycle(alloc, basic, cycle)

        yield {"type": "improvement", "edge": edge,
               "cycle": cycle, "removed": removed, "delta": delta}
