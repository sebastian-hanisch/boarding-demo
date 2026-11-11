"""Szenario: Zufallsgenerator, Sitzplan mit Gruppen, Boarding-Regeln und die daraus entstehende Warteschlange.

Modell: ein Gang mit den Zellen 1 bis R (Zelle c liegt vor Reihe c), je Reihe zwei Seiten mal drei Plätze (pos 0 = Fenster, 1 = Mitte, 2 = Gang).
Alle Zufallszahlen einer Instanz werden in fester Reihenfolge gezogen, unabhängig von Gruppenanteil, Gepäckanteil, Ungehorsam und Regel: ein kleinerer Anteil
liefert eine Teilmenge der Gruppen bzw. der Ungehorsamen (gemeinsame Zufallszahlen für den Vergleich). Der Generator ist ganzzahlig (SplitMix64) und liefert
auf jeder Plattform dieselben Zahlen."""

MASK = (1 << 64) - 1


class SplitMix64:
    """SplitMix64-Generator (Steele, Lea, Flood 2014); `random()` liefert 53 Bit in [0, 1)."""

    def __init__(self, seed):
        self.s = seed & MASK

    def next_u64(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & MASK
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def random(self):
        return (self.next_u64() >> 11) * (1.0 / (1 << 53))


def seat_index(row, side, pos):
    """Laufende Nummer eines Sitzes (Reihe ab 1, Seite 0/1, Platz 0 = Fenster bis 2 = Gang)."""
    return ((row - 1) * 2 + side) * 3 + pos


class Instance:
    """Eine Instanz: Sitzplan, Verstauzeit je Sitz und die Gruppen mit ihren Zufallszahlen.

    `g` und `delta` sind Anteile in [0, 1], `ell` der Anteil mit Gepäck. `sub` trennt die Zufallsströme der beiden Hälften bei zwei Türen.
    `gtype`: "seite" (Mitglieder nebeneinander in einer Reihenseite), "reihe" (beliebige Sitze derselben Reihe) oder "nachbar" (Reihen r und r + 1).
    """

    def __init__(self, seed, R=30, g=0.0, ell=0.7, smin=3, smax=12, delta=0.0, sub=0, gtype="seite"):
        self.R = R
        self.seed = seed
        self._delta = delta
        rng = SplitMix64(seed * 1000003 + sub * 7919 + 12345)
        types = []                                   # je Reihenseite zwei Zahlen: Gruppenart und Teilung
        for _ in range(R):
            for _ in range(2):
                types.append((rng.random(), rng.random()))
        n = R * 6
        ubag = [rng.random() for _ in range(n)]      # je Sitz: Gepäck ja/nein
        ustow = [rng.random() for _ in range(n)]     # je Sitz: Verstauzeit
        ukey = [rng.random() for _ in range(n)]      # je Sitz (als Gruppenanker): Schlüssel, Ungehorsam, Wiedereinreihung
        udis = [rng.random() for _ in range(n)]
        upos = [rng.random() for _ in range(n)]
        self.N = n
        self.row = [0] * n
        self.side = [0] * n
        self.pos = [0] * n
        for r in range(1, R + 1):
            for s in range(2):
                for p in range(3):
                    i = seat_index(r, s, p)
                    self.row[i], self.side[i], self.pos[i] = r, s, p
        self.stow = [0] * n
        for i in range(n):
            if ubag[i] < ell:
                self.stow[i] = smin + int(ustow[i] * (smax - smin + 1))
        self.groups = []                             # Mitgliederlisten
        self.gkey = []
        self.gdis = []
        self.gpos = []
        if gtype != "seite":
            self._groups_free(rng, ukey, udis, upos, g, gtype)
        else:
            k = 0
            for r in range(1, R + 1):
                for s in range(2):
                    ut, up = types[k]
                    k += 1
                    idx = [seat_index(r, s, p) for p in range(3)]
                    if ut < g / 3.0:
                        parts = [idx]
                    elif ut < g / 3.0 + g:
                        parts = [[idx[0], idx[1]], [idx[2]]] if up < 0.5 else [[idx[0]], [idx[1], idx[2]]]
                    else:
                        parts = [[idx[0]], [idx[1]], [idx[2]]]
                    for part in parts:
                        a = part[0]                  # Anker: der erste Sitz liefert die Zufallszahlen
                        self.groups.append(part)
                        self.gkey.append(ukey[a])
                        self.gdis.append(udis[a] < delta)
                        self.gpos.append(upos[a])
        self.g = g
        self.ngroups = len(self.groups)
        self.grouped_share = sum(len(m) for m in self.groups if len(m) > 1) / n

    def _groups_free(self, rng, ukey, udis, upos, g, gtype):
        """Gruppen mit anderer Geometrie als eine Reihenseite: Anker in fester Zufallsreihenfolge, bis der Anteil g erreicht ist.

        Je Anker werden drei Zufallszahlen gezogen, ob die Gruppe entsteht oder nicht; ein kleineres g liefert daher eine Teilmenge."""
        n, rows = self.N, self.R
        anchors = sorted(range(n), key=lambda i: ukey[i])
        draws = [(rng.random(), rng.random(), rng.random()) for _ in range(n)]
        assigned = [False] * n
        target = g * n
        grouped = 0
        groups = {}
        for a, (u_size, u1, u2) in zip(anchors, draws):
            if assigned[a] or grouped >= target:
                continue
            size = 3 if u_size < 0.25 else 2
            r = self.row[a]
            cand = []
            for rr in ([r] if gtype == "reihe" else [r, r + 1]):
                if rr > rows:
                    continue
                for s in range(2):
                    for p in range(3):
                        i = seat_index(rr, s, p)
                        if i != a and not assigned[i]:
                            cand.append(i)
            if len(cand) < size - 1:
                continue
            picks = []
            for u in (u1, u2)[: size - 1]:
                picks.append(cand.pop(int(u * len(cand))))
            members = [a] + picks
            for i in members:
                assigned[i] = True
            grouped += len(members)
            groups[a] = members
        for i in range(n):
            if not assigned[i]:
                groups[i] = [i]
        for a in sorted(groups):
            self.groups.append(groups[a])
            self.gkey.append(ukey[a])
            self.gdis.append(udis[a] < self._delta)
            self.gpos.append(upos[a])


def rule_batch(rule, row, side, pos, rows):
    """(Block, Unterschlüssel) eines Sitzes unter einer Regel; kleinere Blöcke steigen früher ein.

    `b2f<K>` = Rückwärts in K Blöcken, `b2fRows` = Reihe für Reihe von hinten, `f2b<K>` = Vorwärts, `wilma` = Fenster, Mitte, Gang,
    `steffen` = Fenster vor Mitte vor Gang, innerhalb einer Klasse gerade Reihen von hinten nach vorn, dann ungerade (Rekonstruktion)."""
    if rule == "random":
        return (0, 0)
    if rule.startswith("b2f"):
        k = rows if rule == "b2fRows" else int(rule[3:])
        return (k - 1 - (row - 1) * k // rows, 0)
    if rule.startswith("f2b"):
        k = rows if rule == "f2bRows" else int(rule[3:])
        return ((row - 1) * k // rows, 0)
    if rule == "wilma":
        return (pos, 0)
    if rule == "steffen":
        parity = 0 if row % 2 == 0 else 1
        return (pos * 4 + parity * 2 + side, rows - row)
    raise ValueError(rule)


def make_order(inst, rule, intra="window_first", gmode="min"):
    """Warteschlange (Liste von Sitzindizes). Gruppen steigen zusammen ein, zum Aufruf ihres frühesten (`min`) oder spätesten (`max`) Mitglieds.

    Ungehorsame Gruppen werden an eine gleichverteilt zufällige Stelle der Schlange gesetzt. Innerhalb der Gruppe: Fenster zuerst oder Gang zuerst."""
    rows = inst.R
    keyed = []
    for gi, members in enumerate(inst.groups):
        ks = [rule_batch(rule, inst.row[i], inst.side[i], inst.pos[i], rows) for i in members]
        best = min(ks) if gmode == "min" else max(ks)
        keyed.append((best[0], best[1], inst.gkey[gi], gi))
    keyed.sort()
    count = len(keyed)
    posval = {}
    for rank, kk in enumerate(keyed):
        gi = kk[3]
        posval[gi] = inst.gpos[gi] if inst.gdis[gi] else (rank + 0.5) / count
    order = []
    for gi in sorted(range(count), key=lambda gi: posval[gi]):
        members = inst.groups[gi]
        if intra == "window_first":
            members = sorted(members, key=lambda i: (-inst.row[i], inst.pos[i]))
        else:
            members = sorted(members, key=lambda i: (-inst.row[i], -inst.pos[i]))
        order.extend(members)
    return order
