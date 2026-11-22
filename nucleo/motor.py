from dataclasses import dataclass
from enum import Enum
from typing import Any

from nucleo.agente_base import AgenteBase
from nucleo.estado import (
    EstadoJuego,
    aplicar_movimiento,
    es_captura,
    es_escape,
    estado_inicial,
    movimientos_validos,
)
from nucleo.mapa import Laberinto


class ResultadoNivel(Enum):
    EN_CURSO = "EN_CURSO"
    VICTORIA_HUMANO = "VICTORIA_HUMANO"
    CAPTURA_AGENTE = "CAPTURA_AGENTE"


@dataclass
class RegistroMovimiento:
    nivel: int
    numero_turno: int
    actor: str
    accion: str
    pos_jugador: tuple[int, int]
    pos_agente: tuple[int, int]
    estadisticas_agente: dict[str, Any]


class MotorJuego:
    """Gestiona los 3 niveles consecutivos, el ciclo de turnos y el historial."""

    def __init__(self, niveles: list[tuple[Laberinto, AgenteBase]]) -> None:
        if not niveles:
            raise ValueError("Debe proporcionarse al menos un nivel.")
        self.niveles = niveles
        self.indice_nivel: int = 0
        self.estado: EstadoJuego = estado_inicial(self.niveles[0][0])
        self.historial: list[RegistroMovimiento] = []
        self.iniciar_nivel(0)

    @property
    def nivel_actual(self) -> int:
        return self.indice_nivel + 1

    @property
    def total_niveles(self) -> int:
        return len(self.niveles)

    @property
    def agente_actual(self) -> AgenteBase:
        return self.niveles[self.indice_nivel][1]

    def iniciar_nivel(self, indice: int) -> EstadoJuego:
        if not (0 <= indice < len(self.niveles)):
            raise IndexError(f"Índice de nivel fuera de rango: {indice}")
        self.indice_nivel = indice
        laberinto, agente = self.niveles[indice]
        agente.reiniciar()
        self.estado = estado_inicial(laberinto)
        return self.estado

    def evaluar_resultado(self) -> ResultadoNivel:
        if es_captura(self.estado):
            return ResultadoNivel.CAPTURA_AGENTE
        if es_escape(self.estado):
            return ResultadoNivel.VICTORIA_HUMANO
        return ResultadoNivel.EN_CURSO

    def ejecutar_turno_humano(self, accion: str) -> ResultadoNivel:
        if self.estado.turno != "HUMANO":
            raise RuntimeError("No es el turno del jugador humano.")
        if self.evaluar_resultado() != ResultadoNivel.EN_CURSO:
            raise RuntimeError("El nivel actual ya terminó.")

        self.estado = aplicar_movimiento(self.estado, accion)
        self.historial.append(
            RegistroMovimiento(
                nivel=self.nivel_actual,
                numero_turno=self.estado.numero_turno,
                actor="HUMANO",
                accion=accion,
                pos_jugador=self.estado.pos_jugador,
                pos_agente=self.estado.pos_agente,
                estadisticas_agente={},
            )
        )
        return self.evaluar_resultado()

    def ejecutar_turno_agente(self) -> tuple[str, ResultadoNivel]:
        if self.estado.turno != "AGENTE":
            raise RuntimeError("No es el turno del agente.")
        if self.evaluar_resultado() != ResultadoNivel.EN_CURSO:
            raise RuntimeError("El nivel actual ya terminó.")

        agente = self.agente_actual
        accion = agente.elegir_movimiento(self.estado)
        validas = movimientos_validos(self.estado, actor="AGENTE")
        if accion not in validas:
            raise ValueError(
                f"El agente '{agente.nombre}' devolvió '{accion}', pero las válidas son {validas}."
            )

        turno_previo = self.estado.numero_turno
        self.estado = aplicar_movimiento(self.estado, accion)
        self.historial.append(
            RegistroMovimiento(
                nivel=self.nivel_actual,
                numero_turno=turno_previo,
                actor="AGENTE",
                accion=accion,
                pos_jugador=self.estado.pos_jugador,
                pos_agente=self.estado.pos_agente,
                estadisticas_agente=agente.obtener_estadisticas(),
            )
        )
        return accion, self.evaluar_resultado()

    def avanzar_nivel(self) -> bool:
        """
        Avanza al siguiente nivel si quedan pendientes.
        Devuelve True si inició el siguiente nivel; False si se completaron los 3.
        """
        if self.evaluar_resultado() != ResultadoNivel.VICTORIA_HUMANO:
            raise RuntimeError("Solo se puede avanzar tras ganar el nivel actual.")
        if self.indice_nivel + 1 >= len(self.niveles):
            return False
        self.iniciar_nivel(self.indice_nivel + 1)
        return True