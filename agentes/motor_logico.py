"""
Motor de cláusulas definidas de Horn: DECIR y PREGUNTAR.
"""


class BaseConocimiento:
    def __init__(self) -> None:
        self.hechos: set[str] = set()
        self.reglas: list[tuple[frozenset[str], str]] = []

    def decir(self, proposicion: str | tuple[str, ...],
            conclusion: str | None = None) -> None:
        """Incorpora un hecho o una regla de la forma P1 y ... y Pn => Q."""
        if conclusion is None:
            if not isinstance(proposicion, str):
                raise TypeError("Un hecho debe ser una proposición.")
            self.hechos.add(proposicion)
        else:
            premisas = (proposicion,) if isinstance(proposicion, str) else proposicion
            regla = (frozenset(premisas), conclusion)
            if not regla[0]:
                self.hechos.add(conclusion)
            elif regla not in self.reglas:
                self.reglas.append(regla)

    def preguntar(self, objetivo: str) -> bool:
        cuenta = [len(premisas) for premisas, _ in self.reglas]
        inferido = {p: False for p in self.hechos}
        for premisas, cabeza in self.reglas:
            for p in premisas:
                inferido[p] = False
            inferido[cabeza] = False
        agenda = sorted(self.hechos)

        while agenda:
            p = agenda.pop()
            if p == objetivo:
                return True
            if not inferido[p]:
                inferido[p] = True
                for c, (premisas, cabeza) in enumerate(self.reglas):
                    if p in premisas:
                        cuenta[c] -= 1
                        if cuenta[c] == 0:
                            agenda.append(cabeza)

        return False
