"""Kern: Boarding-Zeit einer Warteschlange. Zwei unabhängig geschriebene Rechenwege mit demselben Modell, dazu untere Schranken.

Modell (alle Zahlen Annahmen): ein Gang mit den Zellen 1 bis R, niemand überholt. Ein Fahrgast legt eine Zelle je Takt zurück, wenn die nächste frei ist. Ein neuer
Fahrgast betritt den Gang höchstens alle `e` Takte und nur, wenn die erste Zelle frei ist. Am Ziel verweilt er die Verstauzeit `stow` plus `sh` Takte je Mitreisendem,
der zwischen Gang und eigenem Platz schon sitzt (Platzwechsel); in dieser Zeit blockiert er den Gang.

* `tick_sim`   : taktweise Simulation (liefert auf Wunsch den Zustand zu einem Takt für die Ansicht),
* `recursion`  : Zeit-Gitter-Rekursion; da niemand überholt, hängt jede Ankunftszeit nur vom Vordermann je Zelle ab (anderer Rechenweg, Orakel),
* `lower_bounds`: gültige untere Schranken (Eintritt, Reihe, Kette)."""

import brd_constants as C


def _tick(order, row, side, pos, stow, rows, e, sh, stop_at=None):
    """Taktschleife. Rückgabe: (T, Wartezeit je Fahrgast, Zellenbelegung, Menge der Sitzenden, aktueller Takt).

    Wartezeit = Takte, in denen ein Fahrgast stehen bleiben musste, weil die nächste Zelle belegt war. Mit `stop_at` endet die Schleife nach diesem Takt."""
    n = len(order)
    cell = [-1] * (rows + 2)
    occ = {}                      # (Reihe, Seite) -> [sitzt Fenster, sitzt Mitte, sitzt Gang]
    rem = {}                      # verbleibende Verweiltakte am Ziel
    cur = {}                      # aktuelle Zelle
    wait = {}
    active = []                   # Fahrgäste im Gang, vorderster zuerst
    nxt = 0
    last_entry = 1 - e
    seated = set()
    t = 0
    total = 0

    def arrive(p):
        r, s, q = row[p], side[p], pos[p]
        o = occ.setdefault((r, s), [False, False, False])
        return stow[p] + sh * sum(1 for qq in range(q + 1, 3) if o[qq])

    def seat(p):
        occ.setdefault((row[p], side[p]), [False, False, False])[pos[p]] = True
        seated.add(p)

    while len(seated) < n:
        if stop_at is not None and t >= stop_at:
            break
        t += 1
        if t > C.MAX_TICKS:
            raise RuntimeError("keine Terminierung")
        still = []
        for p in active:
            c = cur[p]
            if c == row[p]:                      # arbeitet am Zielplatz
                rem[p] -= 1
                if rem[p] <= 0:
                    seat(p)
                    cell[c] = -1
                    total = t
                else:
                    still.append(p)
            elif cell[c + 1] == -1:              # nächste Zelle frei: weiter
                cell[c] = -1
                cell[c + 1] = p
                cur[p] = c + 1
                if c + 1 == row[p]:
                    w = arrive(p)
                    if w == 0:
                        seat(p)
                        cell[c + 1] = -1
                        total = t
                    else:
                        rem[p] = w
                        still.append(p)
                else:
                    still.append(p)
            else:                                # blockiert
                wait[p] = wait.get(p, 0) + 1
                still.append(p)
        active = still
        if nxt < n and t - last_entry >= e and cell[1] == -1:
            p = order[nxt]
            nxt += 1
            last_entry = t
            cell[1] = p
            cur[p] = 1
            if row[p] == 1:
                w = arrive(p)
                if w == 0:
                    seat(p)
                    cell[1] = -1
                    total = t
                else:
                    rem[p] = w
                    active.append(p)
            else:
                active.append(p)
    return total, [wait.get(p, 0) for p in order], cell, seated, t


def tick_sim(order, row, side, pos, stow, rows, e=2, sh=3):
    """Taktweise Simulation. Rückgabe: (T, Wartezeit im Gang je Fahrgast in Reihenfolge `order`)."""
    total, waits, _, _, _ = _tick(order, row, side, pos, stow, rows, e, sh)
    return total, waits


def tick_state(order, row, side, pos, stow, rows, e=2, sh=3, t_stop=0):
    """Zustand nach `t_stop` Takten: (Zellenbelegung Zelle 1..R als Fahrgast oder None, Menge der Sitzenden, Gepäck verstauende Fahrgäste)."""
    if t_stop <= 0:
        return [None] * rows, set(), set()
    _, _, cell, seated, _ = _tick(order, row, side, pos, stow, rows, e, sh, stop_at=t_stop)
    occupants = [cell[c] if cell[c] != -1 else None for c in range(1, rows + 1)]
    working = {p for c, p in enumerate(occupants, start=1) if p is not None and row[p] == c}
    return occupants, set(seated), working


def recursion(order, row, side, pos, stow, rows, e=2, sh=3):
    """Unabhängiger Rechenweg: A_c(p) = max(A_{c-1}(p) + 1, L_c) mit L_c = Abgangszeit der Zelle c. Rückgabe wie `tick_sim`."""
    leave = [0] * (rows + 2)
    occ = {}
    prev_entry = 1 - e
    total = 0
    waits = []
    for p in order:
        r = row[p]
        a = max(prev_entry + e, leave[1], 1)
        prev_entry = a
        a1 = a
        for c in range(1, r):
            a2 = max(a + 1, leave[c + 1])
            leave[c] = a2
            a = a2
        o = occ.setdefault((r, side[p]), [False, False, False])
        w = stow[p] + sh * sum(1 for qq in range(pos[p] + 1, 3) if o[qq])
        o[pos[p]] = True
        end = a + w
        leave[r] = end
        total = max(total, end)
        waits.append((a - a1) - (r - 1))
    return total, waits


def lower_bounds(order, row, stow, rows, e=2):
    """Gültige untere Schranken: (Eintritt, Reihe, Kette, größte der beiden einfachen).

    Eintritt: der letzte Fahrgast betritt den Gang frühestens bei 1 + (N - 1) e und braucht mindestens eine Zelle.
    Reihe: Summe der Verstauzeiten einer Reihe plus der Weg bis zu ihr (die Fahrgäste einer Reihe blockieren dieselbe Zelle nacheinander).
    Kette: längster Weg über Vordermänner, die nicht weiter hinten sitzen."""
    n = len(order)
    entry_bound = 1 + (n - 1) * e
    per_row = {}
    for p in order:
        per_row[row[p]] = per_row.get(row[p], 0) + stow[p]
    row_bound = max(r + s for r, s in per_row.items())
    ends = []
    chain = 0
    for k, p in enumerate(order):
        best = 1 + k * e + row[p] - 1 + stow[p]
        for j in range(k):
            q = order[j]
            if row[q] <= row[p]:
                best = max(best, ends[j] + (row[p] - row[q]) + stow[p])
        ends.append(best)
        chain = max(chain, best)
    return entry_bound, row_bound, chain, max(entry_bound, row_bound)
