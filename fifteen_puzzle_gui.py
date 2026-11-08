
import heapq
import random
from collections import deque
from functools import lru_cache
from time import perf_counter


GOAL = (1, 2, 3, 4,
        5, 6, 7, 8,
        9, 10, 11, 12,
        13, 14, 15, 0)

DIRECTIONS = ((-1, 0, 'atas'), (1, 0, 'bawah'), (0, -1, 'kiri'), (0, 1, 'kanan'))


def neighbors(state):
    blank = state.index(0)
    row, col = divmod(blank, 4)
    result = []
    for d_row, d_col, direction in DIRECTIONS:
        new_row, new_col = row + d_row, col + d_col
        if 0 <= new_row < 4 and 0 <= new_col < 4:
            target = new_row * 4 + new_col
            board = list(state)
            tile = board[target]
            board[blank], board[target] = board[target], board[blank]
            result.append((tuple(board), direction, tile))
    return result


def is_solvable(state, goal=GOAL):
    def parity(board):
        tiles = [v for v in board if v]
        inversions = sum(1 for i in range(len(tiles)) for j in range(i + 1, len(tiles))
                         if tiles[i] > tiles[j])
        return (inversions + board.index(0) // 4) % 2
    return parity(state) == parity(goal)


def validate_state(state):
    return len(state) == 16 and set(state) == set(range(16))


def show(state):
    for row in range(4):
        print(' '.join(f'{v:2d}' if v else ' _' for v in state[4 * row:4 * row + 4]))


def make_scramble(steps=20, seed=0):
    rng = random.Random(seed)
    state, previous = GOAL, None
    for _ in range(steps):
        options = [s for s, _, _ in neighbors(state) if s != previous]
        previous, state = state, rng.choice(options)
    return state


DEMO_1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0, 13, 14, 15)
DEMO_2 = (1, 2, 3, 4, 5, 0, 6, 8, 9, 10, 7, 12, 13, 14, 11, 15)
DEMO_3 = (9, 12, 0, 11, 14, 6, 10, 8, 2, 15, 3, 4, 5, 13, 1, 7)

assert all(validate_state(s) and is_solvable(s) for s in (GOAL, DEMO_1, DEMO_2, DEMO_3))

class Heuristic:
    def __init__(self, target):
        self.pos = {v: divmod(i, 4) for i, v in enumerate(target) if v}
        self.wd_rows = self._build_table(target, transpose=False)
        self.wd_cols = self._build_table(target, transpose=True)

    def md(self, state):
        return sum(abs(i // 4 - self.pos[v][0]) + abs(i % 4 - self.pos[v][1])
                   for i, v in enumerate(state) if v)

    @staticmethod
    def _lis(seq):
        best = [1] * len(seq)
        for i in range(len(seq)):
            for j in range(i):
                if seq[j] < seq[i]:
                    best[i] = max(best[i], best[j] + 1)
        return max(best) if seq else 0

    def lc(self, state):
        total = 0
        for r in range(4):
            goal_cols = [self.pos[state[4 * r + c]][1] for c in range(4)
                         if state[4 * r + c] and self.pos[state[4 * r + c]][0] == r]
            total += 2 * (len(goal_cols) - self._lis(goal_cols))
        for c in range(4):
            goal_rows = [self.pos[state[4 * r + c]][0] for r in range(4)
                         if state[4 * r + c] and self.pos[state[4 * r + c]][1] == c]
            total += 2 * (len(goal_rows) - self._lis(goal_rows))
        return total

    def _abstract(self, state, transpose):
        counts = [[0] * 4 for _ in range(4)]
        blank_line = None
        for i, v in enumerate(state):
            line, col = divmod(i, 4)
            if transpose:
                line, col = col, line
            if v == 0:
                blank_line = line
            else:
                counts[line][self.pos[v][1] if transpose else self.pos[v][0]] += 1
        return tuple(map(tuple, counts)), blank_line

    def _build_table(self, target, transpose):
        root = self._abstract(target, transpose)
        table = {root: 0}
        queue = deque([root])
        while queue:
            counts, blank = queue.popleft()
            dist = table[(counts, blank)]
            for line in (blank - 1, blank + 1):
                if 0 <= line < 4:
                    for goal_line in range(4):
                        if counts[line][goal_line] > 0:
                            new_counts = [list(row) for row in counts]
                            new_counts[line][goal_line] -= 1
                            new_counts[blank][goal_line] += 1
                            key = (tuple(map(tuple, new_counts)), line)
                            if key not in table:
                                table[key] = dist + 1
                                queue.append(key)
        return table

    def wd(self, state):
        return (self.wd_rows[self._abstract(state, False)] +
                self.wd_cols[self._abstract(state, True)])

    def hh(self, state):
        return self.md(state) / 3 + self.wd(state) + self.lc(state)


@lru_cache(maxsize=None)
def heuristic_for(target):
    return Heuristic(target)


goal_heuristic = heuristic_for(GOAL)


class Side:
    def __init__(self, code, origin, target):
        self.code = code
        self.h = heuristic_for(target)
        self.target = target
        self.open_list = [(self.h.hh(origin), 0, origin)]
        self.closed_list = {origin: (0, None)}
        self.order = [origin]
        self.expanded = 0
        self.generated = 1


class Namer:
    def __init__(self, start, goal):
        self.names = {start: 'S', goal: 'Goal'}

    def __call__(self, state):
        if state not in self.names:
            idx = len(self.names) - 2
            self.names[state] = chr(ord('A') + idx) if idx < 26 else f'N{idx}'
        return self.names[state]


def build_path(forward, backward, meeting):
    forward_part, state = [], meeting
    while state is not None:
        forward_part.append(state)
        state = forward.closed_list[state][1]
    backward_part, state = [], meeting
    while state is not None:
        backward_part.append(state)
        state = backward.closed_list[state][1]
    return forward_part[::-1] + backward_part[1:]


def print_init(forward, backward, start, goal):
    print('=== Iterasi 1: Inisialisasi ===')
    for side, state, label in ((forward, start, 'Forward (S, target Goal)'),
                               (backward, goal, 'Backward (Goal, target Start)')):
        h = side.h
        print(f'{label}: g=0, MD={h.md(state)}, WD={h.wd(state)}, LC={h.lc(state)}, '
              f'HH={h.hh(state):.2f}, F={h.hh(state):.2f}')
    print()


def print_lists(forward, backward, name_of):
    for side in (forward, backward):
        items = ', '.join(f'{name_of(s)} ({f:.2f})' for f, _, s in sorted(side.open_list))
        print(f'  OpenList_{side.code}: {items or "-"}')
        print(f'  ClosedList_{side.code}: {", ".join(name_of(s) for s in side.order)}')
    print()


class Recorder:
    """Merekam jejak iterasi BA* secara hemat memori: N iterasi pertama + N iterasi terakhir."""
    def __init__(self, head_limit=200, tail_limit=200):
        self.head, self.tail = [], deque(maxlen=tail_limit)
        self.head_limit, self.count = head_limit, 0

    def add(self, rec):
        self.count += 1
        (self.head if len(self.head) < self.head_limit else self.tail).append(rec)

    def items(self):
        hidden = self.count - len(self.head) - len(self.tail)
        gap = [{'kind': 'gap', 'count': hidden}] if hidden > 0 else []
        return self.head + gap + list(self.tail)


def bidirectional_astar(start, goal=GOAL, first_limit=75_000, cycle_limit=15_000,
                        trace=False, max_expansions=2_000_000, recorder=None):
    t0 = perf_counter()
    forward, backward = Side('f', start, goal), Side('b', goal, start)
    name_of = Namer(start, goal)
    if trace:
        print_init(forward, backward, start, goal)
    if recorder is not None:
        def hv(side, state):
            h = side.h
            return (h.md(state), h.wd(state), h.lc(state), h.hh(state))
        recorder.add({'kind': 'init', 'forward': hv(forward, start), 'backward': hv(backward, goal)})

    def snap(rec):
        if rec is not None:
            rec['open'] = (len(forward.open_list), len(backward.open_list))
            rec['closed'] = (len(forward.closed_list), len(backward.closed_list))

    def make_result(meeting):
        path = build_path(forward, backward, meeting)
        return {'solved': True, 'path': path, 'solution_length': len(path) - 1,
                'generated': forward.generated + backward.generated,
                'expanded': forward.expanded + backward.expanded,
                'expanded_f': forward.expanded, 'expanded_b': backward.expanded,
                'meeting': meeting, 'names': name_of.names,
                'runtime_sec': perf_counter() - t0}

    turn, budget, iteration = forward, first_limit, 1
    while True:
        own = turn
        other = backward if own is forward else forward
        for _ in range(budget):
            if not own.open_list or forward.expanded + backward.expanded >= max_expansions:
                return {'solved': False, 'path': None, 'solution_length': None,
                        'generated': forward.generated + backward.generated,
                        'expanded': forward.expanded + backward.expanded,
                        'runtime_sec': perf_counter() - t0}
            f_cost, _, current = heapq.heappop(own.open_list)
            own.expanded += 1
            iteration += 1
            g_current = own.closed_list[current][0]
            if trace:
                label = 'Forward' if own is forward else 'Backward'
                print(f'=== Iterasi {iteration}: {label}, ekspansi {name_of(current)} '
                      f'(g={g_current}, F={f_cost:.2f}) ===')
                show(current)
            rec = None
            if recorder is not None:
                rec = {'kind': 'expand', 'iter': iteration,
                       'side': 'Forward' if own is forward else 'Backward',
                       'state': current, 'name': name_of(current), 'g': g_current, 'f': f_cost,
                       'target': own.target, 'children': []}
                recorder.add(rec)
            if current == own.target:
                snap(rec)
                if rec is not None:
                    rec['via'] = 'target'
                return make_result(current)
            for neighbor, move, _ in neighbors(current):
                if neighbor in own.closed_list:
                    if trace:
                        print(f'  blank ke {move:5s} -> {name_of(neighbor)}: sudah di ClosedList, dilewati')
                    if rec is not None:
                        rec['children'].append({'move': move, 'name': name_of(neighbor), 'skip': True})
                    continue
                g = g_current + 1
                hh = own.h.hh(neighbor)
                own.closed_list[neighbor] = (g, current)
                own.generated += 1
                own.order.append(neighbor)
                heapq.heappush(own.open_list, (g + hh, own.generated, neighbor))
                if rec is not None:
                    rec['children'].append({'move': move, 'name': name_of(neighbor), 'g': g,
                                            'md': own.h.md(neighbor), 'wd': own.h.wd(neighbor),
                                            'lc': own.h.lc(neighbor), 'hh': hh, 'f': g + hh})
                if trace:
                    print(f'  blank ke {move:5s} -> {name_of(neighbor)}: g={g}, MD={own.h.md(neighbor)}, '
                          f'WD={own.h.wd(neighbor)}, LC={own.h.lc(neighbor)}, HH={hh:.2f}, F={g + hh:.2f}')
                if neighbor in other.closed_list:
                    if trace:
                        print(f'  {name_of(neighbor)} sudah ada di ClosedList lawan: titik temu')
                    if rec is not None:
                        rec['via'], rec['meeting'] = 'child', name_of(neighbor)
                    snap(rec)
                    return make_result(neighbor)
            snap(rec)
            if trace:
                print_lists(forward, backward, name_of)
        turn, budget = other, cycle_limit

def validate_path(path, start, goal=GOAL):
    return (bool(path) and path[0] == start and path[-1] == goal and
            all(b in {s for s, _, _ in neighbors(a)} for a, b in zip(path, path[1:])))


def print_path(path):
    for step, (a, b) in enumerate(zip(path, path[1:]), 1):
        for state, direction, tile in neighbors(a):
            if state == b:
                print(f'Langkah {step}: blank ke {direction} (tile {tile})')


def summarize(name, result, start):
    return {'Algorithm': name, 'Solved': result['solved'],
            'Valid': validate_path(result['path'], start) if result['solved'] else None,
            'Solution length': result['solution_length'],
            'Generated': result['generated'], 'Expanded': result['expanded'],
            'Runtime (s)': round(result['runtime_sec'], 3)}



# ===================== GUI (RINGAN) =====================
import threading
import tkinter as tk
from tkinter import messagebox, ttk

MAX_EXPANSIONS = 400_000   # batas pencarian supaya tidak terlalu berat
CELL, CELL_S = 70, 44      # ukuran kotak papan solusi / papan proses
WARNA_BENAR, WARNA_SALAH, WARNA_GERAK = '#22c55e', '#cbd5e1', '#f59e0b'
BG_NETRAL, BG_FWD, BG_BWD = '#f1f5f9', '#dbeafe', '#f3e8ff'
BALIK = {'atas': 'bawah', 'bawah': 'atas', 'kiri': 'kanan', 'kanan': 'kiri'}


def teks_event(e):
    """Ubah satu rekaman iterasi BA* menjadi teks penjelasan."""
    if e['kind'] == 'init':
        lines = ['Iterasi 1: Inisialisasi', '']
        for label, key in (('Forward  (S -> Goal)', 'forward'), ('Backward (Goal -> S)', 'backward')):
            md, wd, lc, hh = e[key]
            lines.append(f'{label}: g=0, MD={md}, WD={wd}, LC={lc}, HH={hh:.2f}, F={hh:.2f}')
        return '\n'.join(lines)
    if e['kind'] == 'gap':
        return f"... {e['count']:,} iterasi di tengah tidak ditampilkan agar ringan ...\n\n" \
               "Langkah berikutnya adalah iterasi-iterasi terakhir sebelum solusi ditemukan."
    lines = [f"Iterasi {e['iter']}: {e['side']}",
             f"Ekspansi {e['name']} (g={e['g']}, F={e['f']:.2f})", '']
    if e.get('via') == 'target':
        lines.append('State ini sama dengan target arahnya: pencarian selesai.')
    else:
        lines.append('Anak yang dihasilkan:')
        for c in e['children']:
            if c.get('skip'):
                lines.append(f" - blank ke {c['move']}: {c['name']} sudah di ClosedList, dilewati")
            else:
                lines.append(f" - blank ke {c['move']}: {c['name']}  g={c['g']}, MD={c['md']}, WD={c['wd']}, "
                             f"LC={c['lc']}, HH={c['hh']:.2f}, F={c['f']:.2f}")
        if not e['children']:
            lines.append(' (tidak ada)')
        if e.get('via') == 'child':
            lines += ['', f"{e['meeting']} sudah ada di ClosedList lawan: TITIK TEMU, solusi ditemukan."]
    lines += ['', f"OpenList f/b   : {e['open'][0]} / {e['open'][1]}",
              f"ClosedList f/b : {e['closed'][0]} / {e['closed'][1]}"]
    return '\n'.join(lines)


class App:
    def __init__(self, root):
        self.root = root
        root.title('Fifteen Puzzle BA* - Step by Step')
        self.path, self.idx, self.playing, self.hasil, self.moves = [], 0, False, None, []
        self.events, self.eidx, self.playing2, self.recorder = [], 0, False, None
        self.start = GOAL
        kiri = tk.Frame(root)
        kiri.grid(row=0, column=0, padx=10, pady=10, sticky='n')
        kanan = tk.Frame(root)
        kanan.grid(row=0, column=1, padx=(0, 10), pady=10, sticky='ns')

        # ---- kiri: input + papan solusi ----
        tk.Label(kiri, text='Input puzzle (kosong / 0 = blank)').pack()
        grid = tk.Frame(kiri)
        grid.pack(pady=4)
        self.vars = [tk.StringVar() for _ in range(16)]
        for i, v in enumerate(self.vars):
            tk.Entry(grid, textvariable=v, width=4, justify='center',
                     font=('Arial', 14)).grid(row=i // 4, column=i % 4, padx=2, pady=2)
        bar = tk.Frame(kiri)
        bar.pack(pady=4)
        tk.Button(bar, text='Contoh', command=self.contoh).pack(side='left', padx=2)
        tk.Button(bar, text='Acak', command=self.acak).pack(side='left', padx=2)
        tk.Button(bar, text='Selesaikan', command=self.selesaikan, bg='#2563eb', fg='white').pack(side='left', padx=2)

        self.canvas = tk.Canvas(kiri, width=CELL * 4, height=CELL * 4, bg=BG_NETRAL, highlightthickness=0)
        self.canvas.pack(pady=6)
        ctl = tk.Frame(kiri)
        ctl.pack()
        tk.Button(ctl, text='|<', command=self.awal).pack(side='left')
        tk.Button(ctl, text='< Mundur', command=lambda: self.pindah(self.idx - 1)).pack(side='left')
        self.btn_play = tk.Button(ctl, text='Putar', command=self.toggle, width=7)
        self.btn_play.pack(side='left')
        tk.Button(ctl, text='Maju >', command=lambda: self.pindah(self.idx + 1)).pack(side='left')
        self.speed = tk.Scale(kiri, from_=100, to=1000, orient='horizontal', label='Jeda antar langkah (ms)', length=250)
        self.speed.set(400)
        self.speed.pack()
        self.status = tk.Label(kiri, text='Isi puzzle lalu klik Selesaikan', wraplength=280, justify='left')
        self.status.pack(pady=4)

        # ---- kanan: dua tab ----
        nb = ttk.Notebook(kanan)
        nb.pack(fill='both', expand=True)
        tab_sol, tab_proc = tk.Frame(nb), tk.Frame(nb)
        nb.add(tab_sol, text='Langkah solusi')
        nb.add(tab_proc, text='Proses pencarian BA*')

        self.lb = tk.Listbox(tab_sol, width=34, height=24, exportselection=False)
        self.lb.pack(side='left', fill='y')
        sb = tk.Scrollbar(tab_sol, command=self.lb.yview)
        sb.pack(side='left', fill='y')
        self.lb.config(yscrollcommand=sb.set)
        self.lb.bind('<<ListboxSelect>>', self.klik_daftar)

        self.lbl_event = tk.Label(tab_proc, text='Belum ada proses. Klik Selesaikan dulu.')
        self.lbl_event.pack(pady=(6, 0))
        self.canvas2 = tk.Canvas(tab_proc, width=CELL_S * 4, height=CELL_S * 4, bg=BG_NETRAL, highlightthickness=0)
        self.canvas2.pack(pady=4)
        ctl2 = tk.Frame(tab_proc)
        ctl2.pack()
        tk.Button(ctl2, text='|<', command=lambda: self.stop2(0)).pack(side='left')
        tk.Button(ctl2, text='< Mundur', command=lambda: self.stop2(self.eidx - 1)).pack(side='left')
        self.btn_play2 = tk.Button(ctl2, text='Putar', command=self.toggle2, width=7)
        self.btn_play2.pack(side='left')
        tk.Button(ctl2, text='Maju >', command=lambda: self.stop2(self.eidx + 1)).pack(side='left')
        tk.Button(ctl2, text='>|', command=lambda: self.stop2(len(self.events) - 1)).pack(side='left')
        self.detail = tk.Text(tab_proc, width=52, height=15, wrap='word', font=('Consolas', 9), state='disabled')
        self.detail.pack(padx=4, pady=6)

        self.contoh()
        self.gambar(self.canvas, CELL, tuple(range(1, 16)) + (0,), None)

    # ---------- input ----------
    def baca(self):
        nilai = []
        for v in self.vars:
            t = v.get().strip().replace('_', '0')
            nilai.append(0 if t == '' else int(t))
        return tuple(nilai)

    def isi(self, state):
        for v, x in zip(self.vars, state):
            v.set('' if x == 0 else str(x))

    def contoh(self):
        self.isi(DEMO_2)

    def acak(self):
        self.isi(make_scramble(random.randint(15, 40), seed=random.randint(0, 10**6)))

    # ---------- gambar ----------
    def gambar(self, canvas, cell, state, tile_gerak, target=GOAL, bg=BG_NETRAL):
        canvas.config(bg=bg)
        canvas.delete('all')
        if state is None:
            return
        font = ('Arial', 20 if cell >= CELL else 12, 'bold')
        for i, v in enumerate(state):
            if v == 0:
                continue
            r, c = divmod(i, 4)
            warna = WARNA_GERAK if v == tile_gerak else (WARNA_BENAR if v == target[i] else WARNA_SALAH)
            canvas.create_rectangle(c * cell + 2, r * cell + 2, (c + 1) * cell - 2, (r + 1) * cell - 2,
                                    fill=warna, outline='')
            canvas.create_text(c * cell + cell / 2, r * cell + cell / 2, text=str(v), font=font, fill='#1e293b')

    # ---------- solve ----------
    def selesaikan(self):
        try:
            state = self.baca()
        except ValueError:
            messagebox.showerror('Input salah', 'Isi hanya dengan angka 0-15.')
            return
        if len(set(state)) != 16 or set(state) != set(range(16)):
            messagebox.showerror('Input salah', 'Harus ada angka 0-15 masing-masing satu kali (kosong = blank).')
            return
        if not is_solvable(state):
            messagebox.showerror('Tidak solvable', 'Puzzle ini tidak bisa diselesaikan. Coba tukar dua tile.')
            return
        if state == GOAL:
            messagebox.showinfo('Info', 'Puzzle sudah sama dengan Goal.')
            return
        self.playing = self.playing2 = False
        self.btn_play.config(text='Putar')
        self.btn_play2.config(text='Putar')
        self.status.config(text='Mencari solusi... (puzzle sulit bisa agak lama)')
        self.hasil, self.start, self.recorder = None, state, Recorder()
        threading.Thread(target=self.hitung, args=(state, self.recorder), daemon=True).start()
        self.root.after(150, self.cek)

    def hitung(self, state, recorder):
        try:
            self.hasil = bidirectional_astar(state, max_expansions=MAX_EXPANSIONS, recorder=recorder)
        except Exception as exc:   # supaya GUI tidak menggantung bila ada error
            self.hasil = {'solved': False, 'error': str(exc)}

    def cek(self):
        if self.hasil is None:
            self.root.after(150, self.cek)
            return
        r = self.hasil
        if r.get('error'):
            self.status.config(text=f"Terjadi error: {r['error']}")
            return
        if not r['solved']:
            self.status.config(text=f'Belum ketemu dalam {MAX_EXPANSIONS:,} ekspansi. Coba puzzle yang lebih mudah.')
            return
        self.path = r['path']
        self.moves = []
        for a, b in zip(self.path, self.path[1:]):
            d = b.index(0) - a.index(0)
            self.moves.append(({-4: 'atas', 4: 'bawah', -1: 'kiri', 1: 'kanan'}[d], a[b.index(0)]))
        self.lb.delete(0, 'end')
        self.lb.insert('end', '0. Posisi awal')
        for k, (arah, tile) in enumerate(self.moves, 1):
            self.lb.insert('end', f'{k}. tile {tile} geser ke {BALIK[arah]}')
        self.events = self.recorder.items()
        ditampilkan = sum(1 for e in self.events if e['kind'] == 'expand')
        self.status.config(text=f"Selesai: {r['solution_length']} langkah | ekspansi f/b = "
                                f"{r['expanded_f']}/{r['expanded_b']} | {r['runtime_sec']:.2f} s\n"
                                f"Tab proses menampilkan {ditampilkan} dari {r['expanded']} iterasi.")
        self.pindah(0)
        self.tampil_event(0)

    # ---------- tab solusi ----------
    def pindah(self, k):
        if not self.path:
            return
        self.idx = max(0, min(len(self.path) - 1, k))
        tile = self.moves[self.idx - 1][1] if self.idx > 0 else None
        self.gambar(self.canvas, CELL, self.path[self.idx], tile)
        self.lb.selection_clear(0, 'end')
        self.lb.selection_set(self.idx)
        self.lb.see(self.idx)

    def awal(self):
        self.playing = False
        self.btn_play.config(text='Putar')
        self.pindah(0)

    def klik_daftar(self, _):
        s = self.lb.curselection()
        if s:
            self.playing = False
            self.btn_play.config(text='Putar')
            self.pindah(s[0])

    def toggle(self):
        if not self.path:
            return
        self.playing = not self.playing
        self.btn_play.config(text='Jeda' if self.playing else 'Putar')
        if self.playing:
            if self.idx >= len(self.path) - 1:
                self.pindah(0)
            self.langkah_otomatis()

    def langkah_otomatis(self):
        if not self.playing:
            return
        if self.idx >= len(self.path) - 1:
            self.playing = False
            self.btn_play.config(text='Putar')
            return
        self.pindah(self.idx + 1)
        self.root.after(self.speed.get(), self.langkah_otomatis)

    # ---------- tab proses pencarian ----------
    def tampil_event(self, k):
        if not self.events:
            return
        self.eidx = max(0, min(len(self.events) - 1, k))
        e = self.events[self.eidx]
        self.lbl_event.config(text=f'Langkah proses {self.eidx + 1} / {len(self.events)}')
        if e['kind'] == 'init':
            self.gambar(self.canvas2, CELL_S, self.start, None)
        elif e['kind'] == 'gap':
            self.gambar(self.canvas2, CELL_S, None, None)
        else:
            bg = BG_FWD if e['side'] == 'Forward' else BG_BWD
            self.gambar(self.canvas2, CELL_S, e['state'], None, target=e['target'], bg=bg)
        self.detail.config(state='normal')
        self.detail.delete('1.0', 'end')
        self.detail.insert('1.0', teks_event(e))
        self.detail.config(state='disabled')

    def stop2(self, k):
        self.playing2 = False
        self.btn_play2.config(text='Putar')
        self.tampil_event(k)

    def toggle2(self):
        if not self.events:
            return
        self.playing2 = not self.playing2
        self.btn_play2.config(text='Jeda' if self.playing2 else 'Putar')
        if self.playing2:
            if self.eidx >= len(self.events) - 1:
                self.tampil_event(0)
            self.langkah_otomatis2()

    def langkah_otomatis2(self):
        if not self.playing2:
            return
        if self.eidx >= len(self.events) - 1:
            self.playing2 = False
            self.btn_play2.config(text='Putar')
            return
        self.tampil_event(self.eidx + 1)
        self.root.after(self.speed.get(), self.langkah_otomatis2)


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
