"""Plotly-Figuren: Vergleich der Regeln, Flugzeugansicht zu einem Takt, Wartezeit je Sitz, Regime-Karte und Experimente. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import brd_constants as C

_LAYOUT = dict(margin=dict(l=50, r=20, t=40, b=45), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=",.")


def _fixed(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_bars(a) -> go.Figure:
    """Boarding-Zeit je Regel (Mittel über die Läufe) mit der Eintrittsschranke als Linie."""
    rules = [r["rule"] for r in a.rows]
    fig = go.Figure(go.Bar(
        name="Boarding-Zeit", showlegend=False, x=[C.RULE_SHORT[r] for r in rules], y=[row["T"] for row in a.rows], marker_color=[C.RULE_COLORS[r] for r in rules],
        text=[f"{row['T']:.0f}" for row in a.rows], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>%{y:.0f} Takte<extra></extra>",
    ))
    labels = [C.RULE_SHORT[r] for r in rules]
    fig.add_trace(go.Scatter(x=labels, y=[a.entry] * len(labels), mode="lines", name=f"Eintrittsschranke ({a.entry:.0f} Takte)", line=dict(color="#333", dash="dash"),
                             hovertemplate="Eintrittsschranke %{y:.0f}<extra></extra>"))
    fig.update_layout(**_LAYOUT, height=340, yaxis_title="Boarding-Zeit (Takte)", showlegend=True, legend=dict(orientation="h", y=1.12, x=0),
                      title=f"Mittlere Boarding-Zeit über {a.n_runs} Läufe")
    fig.update_yaxes(rangemode="tozero")
    return _fixed(fig)


def _seat_xy(row, side, pos):
    """Koordinaten eines Sitzes in der Draufsicht: x = Reihe, y = Abstand vom Gang (Fenster außen)."""
    offset = (3 - pos)                      # Fenster 3, Mitte 2, Gang 1
    return row, (offset if side == 0 else -offset)


def build_plane(inst, occupants, seated, working, t, total) -> go.Figure:
    """Draufsicht: Sitze (besetzt oder frei), Fahrgäste im Gang (laufend oder beim Verstauen) nach `t` Takten."""
    free_x, free_y, taken_x, taken_y = [], [], [], []
    for i in range(inst.N):
        x, y = _seat_xy(inst.row[i], inst.side[i], inst.pos[i])
        (taken_x if i in seated else free_x).append(x)
        (taken_y if i in seated else free_y).append(y)
    walk_x, walk_y, work_x, work_y = [], [], [], []
    for cell, p in enumerate(occupants, start=1):
        if p is None:
            continue
        (work_x if p in working else walk_x).append(cell)
        (work_y if p in working else walk_y).append(0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=free_x, y=free_y, mode="markers", name="Sitz frei", marker=dict(symbol="square", size=9, color=C.COLOR_SEAT_FREE), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=taken_x, y=taken_y, mode="markers", name="sitzt", marker=dict(symbol="square", size=9, color=C.COLOR_SEAT_TAKEN), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=walk_x, y=walk_y, mode="markers", name="im Gang", marker=dict(symbol="circle", size=11, color=C.COLOR_WALKING), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=work_x, y=work_y, mode="markers", name="verstaut / wechselt", marker=dict(symbol="diamond", size=12, color=C.COLOR_WORKING), hoverinfo="skip"))
    fig.update_layout(**_LAYOUT, height=260, title=f"Takt {t} von {total}: {len(seated)} von {inst.N} sitzen",
                      legend=dict(orientation="h", y=-0.25), xaxis_title="Reihe (Tür vorn links)", yaxis=dict(visible=False, range=[-4, 4]))
    fig.update_xaxes(range=[0, inst.R + 1])
    return _fixed(fig)


def build_wait_map(inst, order, waits) -> go.Figure:
    """Wartezeit im Gang je Sitz (Takte, die der Fahrgast stehen bleiben musste, weil die nächste Zelle belegt war)."""
    by_seat = {p: w for p, w in zip(order, waits)}
    xs, ys, ws = [], [], []
    for i in range(inst.N):
        x, y = _seat_xy(inst.row[i], inst.side[i], inst.pos[i])
        xs.append(x)
        ys.append(y)
        ws.append(by_seat.get(i, 0))
    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers", hovertemplate="Reihe %{x}<br>Wartezeit %{marker.color} Takte<extra></extra>",
        marker=dict(symbol="square", size=9, color=ws, colorscale="YlOrRd", cmin=0, colorbar=dict(title="Takte", thickness=10)),
    ))
    fig.update_layout(**_LAYOUT, height=240, title="Wartezeit im Gang je Sitz", xaxis_title="Reihe", yaxis=dict(visible=False, range=[-4, 4]))
    fig.update_xaxes(range=[0, inst.R + 1])
    return _fixed(fig)


def _heat(z, xs, ys, title, colorscale, fmt, zmid=None):
    fig = go.Figure(go.Heatmap(
        z=z, x=[f"e = {x}" for x in xs], y=[f"≤ {y}" for y in ys], colorscale=colorscale, zmid=zmid, text=[[fmt.format(v).replace(".", ",") for v in row] for row in z],
        texttemplate="%{text}", hovertemplate="%{x}, Verstauzeit %{y}: %{text}<extra></extra>", colorbar=dict(thickness=10),
    ))
    fig.update_layout(**_LAYOUT, height=300, title=title, xaxis=dict(type="category"), yaxis=dict(type="category", title="Verstauzeit (Takte)"))
    return _fixed(fig)


def build_regime_heatmaps(m) -> tuple[go.Figure, go.Figure]:
    """Zwei Karten über Türrate und Verstauzeit: Verhältnis zu Zufall und Abstand zur Eintrittsschranke (Regel: m['rule'])."""
    name = C.RULE_SHORT[m["rule"]]
    ratio = _heat(m["ratio"], m["e"], m["smax"], f"{name} / Zufall (kleiner ist besser)", "RdYlGn_r", "{:.2f}", zmid=0.9)
    bound = _heat(m["over_bound"], m["e"], m["smax"], f"{name} / Eintrittsschranke (1 = nicht mehr zu holen)", "Blues", "{:.2f}")
    return ratio, bound


def build_lines(x, series, xtitle, title, ytitle="Boarding-Zeit / Zufall") -> go.Figure:
    """Linien je Regel über einen Parameter; `series`: {Regel (oder Beschriftung): (Werte, Farbe, gestrichelt)}."""
    fig = go.Figure()
    for label, (values, color, dash) in series.items():
        fig.add_trace(go.Scatter(x=x, y=values, mode="lines+markers", name=label, line=dict(color=color, dash="dash" if dash else "solid"),
                                 hovertemplate=f"{label}: %{{y:.3f}}<extra></extra>"))
    fig.add_hline(y=1.0, line_dash="dot", line_color="#888")
    fig.update_layout(**_LAYOUT, height=300, title=title, xaxis_title=xtitle, yaxis_title=ytitle, legend=dict(orientation="h", y=-0.3))
    return _fixed(fig)


def build_lookahead(rows) -> go.Figure:
    """Je Gruppenanteil: Zufall, Steffen-artig, beste gefundene Reihenfolge mit Voraussicht und Eintrittsschranke (Takte, Mittel über die Instanzen)."""
    labels = [f"{r['g']} % Gruppen" for r in rows]
    fig = go.Figure()
    for key, name, color in (("random", "Zufall", C.RULE_COLORS["random"]), ("steffen", "Steffen-artig", C.RULE_COLORS["steffen"]),
                             ("best", "beste gefundene (Voraussicht)", "#e8a63b"), ("entry", "Eintrittsschranke", "#555")):
        fig.add_trace(go.Bar(x=labels, y=[r[key] for r in rows], name=name, marker_color=color, text=[f"{r[key]:.0f}" for r in rows], textposition="outside", cliponaxis=False))
    fig.update_layout(**_LAYOUT, height=340, barmode="group", yaxis_title="Boarding-Zeit (Takte)", legend=dict(orientation="h", y=-0.25), title="Was mindestens möglich ist")
    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(type="category")
    return _fixed(fig)
