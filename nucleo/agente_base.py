from abc import ABC, abstractmethod
import random
from typing import Any

from nucleo.estado import EstadoJuego, movimientos_validos


class AgenteBase(ABC):
    """
    Contrato común que deben heredar los agentes de los 3 niveles
    (Integrantes 2, 3 y 5).
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre

    @abstractmethod
    def elegir_movimiento(self, estado: EstadoJuego) -> str:
        """
        Recibe el EstadoJuego actual (con turno == 'AGENTE') y devuelve
        una acción válida: 'ARRIBA', 'ABAJO', 'IZQUIERDA' o 'DERECHA'.
        Debe ejecutarse en vivo durante la partida (sin rutas precalculadas).
        """

    def reiniciar(self) -> None:
        """Restablece el estado interno del agente al iniciar o reintentar un nivel."""

    def obtener_estadisticas(self) -> dict[str, Any]:
        """Devuelve métricas del último turno (nodos explorados, modo patrulla/inferencia, etc.)."""
        return {}


class AgenteAleatorio(AgenteBase):
    """Agente de prueba para validar el motor antes de integrar los módulos de IA."""

    def __init__(self, semilla: int | None = None) -> None:
        super().__init__(nombre="Agente de Prueba (Aleatorio)")
        self._rng = random.Random(semilla)

    def elegir_movimiento(self, estado: EstadoJuego) -> str:
        opciones = movimientos_validos(estado, actor="AGENTE")
        if not opciones:
            raise RuntimeError("El agente no tiene movimientos válidos disponibles.")
        return self._rng.choice(opciones)