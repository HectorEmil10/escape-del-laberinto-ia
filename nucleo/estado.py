from dataclasses import dataclass
from typing import Literal

from nucleo.mapa import ACCIONES, Laberinto, Posicion

Actor = Literal["HUMANO", "AGENTE"]


@dataclass(frozen=True)
class EstadoJuego:
    """
    Estado completo e inmutable de una partida en un instante dado.
    Compatible con búsqueda en grafos (Tema 3) y búsqueda adversarial (Minimax).
    """

    laberinto: Laberinto
    pos_jugador: Posicion
    pos_agente: Posicion
    turno: Actor = "HUMANO"  # Regla 5: el jugador humano siempre mueve primero
    numero_turno: int = 1


def estado_inicial(laberinto: Laberinto) -> EstadoJuego:
    """Construye el estado inicial de un nivel."""
    return EstadoJuego(
        laberinto=laberinto,
        pos_jugador=laberinto.inicio_jugador,
        pos_agente=laberinto.inicio_agente,
        turno="HUMANO",
        numero_turno=1,
    )


def es_captura(estado: EstadoJuego) -> bool:
    """El agente gana cuando ocupa la misma celda que el jugador."""
    return estado.pos_jugador == estado.pos_agente


def es_escape(estado: EstadoJuego) -> bool:
    """El jugador gana al alcanzar la salida (10, 10) sin ser capturado."""
    return estado.pos_jugador == estado.laberinto.salida and not es_captura(estado)


def test_terminal(estado: EstadoJuego) -> bool:
    """TEST_TERMINAL(estado) para Minimax (Algoritmos 10 y 11, Tema 3) y el motor."""
    return es_captura(estado) or es_escape(estado)


def movimientos_validos(estado: EstadoJuego, actor: Actor | None = None) -> list[str]:
    """Devuelve la lista de acciones válidas para el actor indicado (o el del turno actual)."""
    if test_terminal(estado):
        return []
    quien = actor or estado.turno
    pos_actual = estado.pos_jugador if quien == "HUMANO" else estado.pos_agente
    return [accion for accion, _ in estado.laberinto.vecinos(pos_actual)]


def aplicar_movimiento(estado: EstadoJuego, accion: str) -> EstadoJuego:
    """
    Aplica una acción válida al actor en turno y devuelve un NUEVO EstadoJuego.
    """
    if test_terminal(estado):
        raise ValueError("No se pueden aplicar movimientos sobre un estado terminal.")
    if accion not in ACCIONES:
        raise ValueError(f"Acción desconocida: '{accion}'. Válidas: {list(ACCIONES.keys())}")

    dx, dy = ACCIONES[accion]
    if estado.turno == "HUMANO":
        nueva_pos = (estado.pos_jugador[0] + dx, estado.pos_jugador[1] + dy)
        if not estado.laberinto.es_transitable(nueva_pos):
            raise ValueError(f"Movimiento inválido '{accion}' para HUMANO hacia {nueva_pos}.")
        return EstadoJuego(
            laberinto=estado.laberinto,
            pos_jugador=nueva_pos,
            pos_agente=estado.pos_agente,
            turno="AGENTE",
            numero_turno=estado.numero_turno,
        )

    nueva_pos = (estado.pos_agente[0] + dx, estado.pos_agente[1] + dy)
    if not estado.laberinto.es_transitable(nueva_pos):
        raise ValueError(f"Movimiento inválido '{accion}' para AGENTE hacia {nueva_pos}.")
    return EstadoJuego(
        laberinto=estado.laberinto,
        pos_jugador=estado.pos_jugador,
        pos_agente=nueva_pos,
        turno="HUMANO",
        numero_turno=estado.numero_turno + 1,
    )


def sucesores(estado: EstadoJuego) -> list[tuple[str, EstadoJuego]]:
    """
    Función SUCESORES(estado) del Tema 3.
    Devuelve pares (accion, nuevo_estado) para el actor al que le corresponde mover.
    """
    return [(accion, aplicar_movimiento(estado, accion)) for accion in movimientos_validos(estado)]