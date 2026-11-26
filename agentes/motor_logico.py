"""Motor de inferencia proposicional del nivel 3.

Este módulo no mueve al personaje ni determina patrullajes: solamente
almacena proposiciones, aplica reglas y contesta consultas lógicas.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import re
from typing import Iterable


_SIMBOLO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validar_simbolo(valor: str) -> str:
    """Verifica que una proposición sea atómica y pueda usarse como clave."""
    if not isinstance(valor, str) or not _SIMBOLO.fullmatch(valor):
        raise ValueError(f"Proposición inválida: {valor!r}")
    return valor


@dataclass(frozen=True)
class ReglaHorn:
    """Regla definida de Horn: premisa1 ∧ ... ∧ premisaN ⇒ conclusion."""

    premisas: tuple[str, ...]
    conclusion: str

    def __post_init__(self) -> None:
        if isinstance(self.premisas, str):
            raise TypeError("Las premisas deben ser una secuencia, no una cadena.")
        # A ∧ A ⇒ B tiene el mismo significado que A ⇒ B.
        nuevas = tuple(dict.fromkeys(_validar_simbolo(x) for x in self.premisas))
        object.__setattr__(self, "premisas", nuevas)
        _validar_simbolo(self.conclusion)

    def __str__(self) -> str:
        if not self.premisas:
            return self.conclusion
        return " ∧ ".join(self.premisas) + " ⇒ " + self.conclusion


class BaseConocimiento:
    """Base de conocimiento con operaciones DECIR y PREGUNTAR

    Las inferencias son calculadas al consultar, no se incorporan como hechos,
    de forma que no se altere la base al llamar varias veces a PREGUNTAR
    """

    def __init__(
        self,
        hechos: Iterable[str] = (),
        reglas: Iterable[ReglaHorn] = (),
    ) -> None:
        self.hechos: set[str] = set()
        self.reglas: list[ReglaHorn] = []
        for regla in reglas:
            self.decir(regla)
        for hecho in hechos:
            self.decir(hecho)

    def decir(
        self,
        proposicion: str | ReglaHorn | Iterable[str],
        conclusion: str | None = None,
    ) -> None:
        """Agrega un hecho o una regla.

        Las siguientes tres formas son válidas:
          decir("A")                         # hecho
          decir(("A", "B"), "C")           # regla de Horn (API del guardián)
          decir(ReglaHorn(("A", "B"), "C"))  # regla como objeto
        Una regla con cero premisas se convierte en un hecho
        """
        if conclusion is None:
            if isinstance(proposicion, str):
                self.hechos.add(_validar_simbolo(proposicion))
                return
            if not isinstance(proposicion, ReglaHorn):
                raise TypeError("Para agregar una regla, proporciona la conclusión.")
            regla = proposicion
        else:
            if isinstance(proposicion, str):
                premisas = (proposicion,)
            elif isinstance(proposicion, ReglaHorn):
                raise TypeError("No pases una conclusión adicional a ReglaHorn.")
            else:
                premisas = tuple(proposicion)
            regla = ReglaHorn(premisas, conclusion)

        if not regla.premisas:
            self.hechos.add(regla.conclusion)
        elif regla not in self.reglas:
            self.reglas.append(regla)

    def agregar_regla(self, premisas: Iterable[str], conclusion: str) -> None:
        """Alias para registrar la regla de Horn sin construir el objeto"""
        self.decir(tuple(premisas), conclusion)

    def preguntar(self, objetivo: str) -> bool:
        """Devuelve True si la BC puede demostrar el objetivo con Horn"""
        _validar_simbolo(objetivo)
        demostrado, _, _ = self._encadenamiento_hacia_adelante(objetivo)
        return demostrado

    def inferir_todos(self) -> frozenset[str]:
        """Calcula todas las proposiciones deducibles sin modificar la BC"""
        _, conocidos, _ = self._encadenamiento_hacia_adelante(None)
        return frozenset(conocidos)

    def explicar(self, objetivo: str) -> tuple[bool, list[str]]:
        """Indica si se demuestra el objetivo y las reglas que se aplicaron"""
        _validar_simbolo(objetivo)
        demostrado, _, traza = self._encadenamiento_hacia_adelante(objetivo)
        return demostrado, traza

    def _encadenamiento_hacia_adelante(
        self, objetivo: str | None,
    ) -> tuple[bool, set[str], list[str]]:
        """Adaptación de ¿IMPLICACIÓN-EHD-LP?(BC, q), Tema 4, Algoritmo 6

        cuenta[c]: cuántas premisas faltan para activar una regla
        inferido: símbolos que ya fueron procesados
        agenda: símbolos verdaderos pendientes por procesar
        """
        cuenta = [len(regla.premisas) for regla in self.reglas]
        # Índice para buscar únicamente reglas cuyo antecedente contiene p
        dependientes: dict[str, list[int]] = defaultdict(list)
        for i, regla in enumerate(self.reglas):
            for premisa in regla.premisas:
                dependientes[premisa].append(i)

        conocidos = set(self.hechos)
        agenda = deque(sorted(conocidos))
        inferido: set[str] = set()
        traza: list[str] = []

        while agenda:
            p = agenda.popleft()
            if p == objetivo:
                return True, conocidos, traza
            if p in inferido:
                continue
            inferido.add(p)
            for indice in dependientes.get(p, ()):
                cuenta[indice] -= 1
                if cuenta[indice] == 0:
                    regla = self.reglas[indice]
                    if regla.conclusion not in conocidos:
                        conocidos.add(regla.conclusion)
                        agenda.append(regla.conclusion)
                        traza.append(str(regla))

        # Si no hay objetivo, se solicitó el cierre lógico completo
        return objetivo is None, conocidos, traza


def crear_base_para_turno(
    reglas: Iterable[ReglaHorn], percepciones: Iterable[str]
) -> BaseConocimiento:
    """Alternativa para agentes sin memoria, creando una BC nueva por turno."""
    return BaseConocimiento(hechos=percepciones, reglas=reglas)
