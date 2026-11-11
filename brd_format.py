"""Zahlenformat für deutsche Texte: Dezimalkomma, Tausenderpunkt nur an der Zahl (nie am ganzen Satz)."""


def de(x: float, nd: int = 1) -> str:
    """Zahl mit `nd` Nachkommastellen und Dezimalkomma, z. B. de(26.2) -> '26,2'."""
    return f"{x:.{nd}f}".replace(".", ",")


def signed(x: float, nd: int = 0) -> str:
    """Zahl mit Vorzeichen und Dezimalkomma, z. B. signed(-147) -> '-147', signed(3.5, 1) -> '+3,5'."""
    return f"{x:+.{nd}f}".replace(".", ",")
