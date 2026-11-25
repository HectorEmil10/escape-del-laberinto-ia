"""Nivel 3: agente guardián basado en conocimiento.
Cada proposición perceptual y cada acción se identifican con el tiempo del agente.
"""
from typing import Any

from agentes.motor_logico import BaseConocimiento
from nucleo.agente_base import AgenteBase
from nucleo.estado import EstadoJuego, movimientos_validos
from nucleo.mapa import ACCIONES, Posicion


class AgenteGuardian(AgenteBase):
    PATRULLA: tuple[Posicion, ...] = ((8, 9), (9, 9), (9, 8), (8, 8))
    REGLAS = {
        "ARRIBA": ("JugadorArriba", "MoverArriba"),
        "ABAJO": ("JugadorAbajo", "MoverAbajo"),
        "IZQUIERDA": ("JugadorIzquierda", "MoverIzquierda"),
        "DERECHA": ("JugadorDerecha", "MoverDerecha"),
    }

    def __init__(self, fabrica_bc=BaseConocimiento) -> None:
        super().__init__(nombre="Agente Guardián (Lógica Proposicional)")
        self._fabrica_bc = fabrica_bc
        self.reiniciar()

    def reiniciar(self) -> None:
        self.bc = self._fabrica_bc()
        self.t = 0
        self._estadisticas: dict[str, Any] = {}

    def _sentencia(self, proposicion: str) -> str:
        """Genera un símbolo proposicional distinto para cada instante."""
        return f"{proposicion}_{self.t}"

    @staticmethod
    def _posicion(pos: Posicion) -> str:
        return f"EnPosicion_{pos[0]}_{pos[1]}"

    def _registrar_reglas(self) -> None:
        for direccion, (percepcion, accion) in self.REGLAS.items():
            self.bc.decir((self._sentencia(percepcion),
                        self._sentencia(f"Valido_{direccion}")),
                        self._sentencia(accion))

        # Reglas de patrullaje: posición actual + ausencia de jugador
        # adyacente + movimiento válido => siguiente acción del ciclo.
        # El desplazamiento se obtiene de los puntos de patrulla.
        for i, actual in enumerate(self.PATRULLA):
            destino = self.PATRULLA[(i + 1) % len(self.PATRULLA)]
            delta = (destino[0] - actual[0], destino[1] - actual[1])
            direccion = next(d for d, desplazamiento in ACCIONES.items()
                             if desplazamiento == delta)
            self.bc.decir((self._sentencia("SinJugadorAdyacente"),
                        self._sentencia(self._posicion(actual)),
                        self._sentencia(f"Valido_{direccion}")),
                        self._sentencia(self.REGLAS[direccion][1]))

    def _percibir(self, estado: EstadoJuego) -> list[str]:
        gx, gy = estado.pos_agente
        px, py = estado.pos_jugador
        desplazamiento = (px - gx, py - gy)
        return [self.REGLAS[d][0] for d, delta in ACCIONES.items()
                if delta == desplazamiento]

    def construir_sentencia_de_percepcion(self, estado: EstadoJuego,
                                        validas: list[str]) -> list[str]:
        """Convierte las observaciones actuales en hechos del tiempo t."""
        percepciones = self._percibir(estado)
        hechos = percepciones or ["SinJugadorAdyacente"]
        hechos = hechos + [self._posicion(estado.pos_agente)]
        hechos += [f"Valido_{direccion}" for direccion in validas]
        return [self._sentencia(hecho) for hecho in hechos]

    def pedir_accion(self, validas: list[str]) -> tuple[str, str, int]:
        """PREGUNTAR qué acción del tiempo t se deduce de la BC."""
        consultas = 0
        for direccion, (_, accion) in self.REGLAS.items():
            if direccion not in validas:
                continue
            consulta = self._sentencia(accion)
            consultas += 1
            if self.bc.preguntar(consulta):
                return direccion, consulta, consultas
        raise RuntimeError("La BC no dedujo un movimiento válido del guardián.")

    def construir_sentencia_de_accion(self, accion: str) -> str:
        return self._sentencia(f"AccionElegida_{accion}")

    def elegir_movimiento(self, estado: EstadoJuego) -> str:
        if estado.turno != "AGENTE":
            raise ValueError("No es el turno del guardián.")
        validas = movimientos_validos(estado, actor="AGENTE")
        if not validas:
            raise RuntimeError("No hay movimientos válidos para el guardián.")

        # Preparar las cláusulas de Horn correspondientes al instante t.
        self._registrar_reglas()

        # 1. DECIR(BC, CONSTRUIR-SENTENCIA-DE-PERCEPCION(percepcion, t)).
        hechos = self.construir_sentencia_de_percepcion(estado, validas)
        for hecho in hechos:
            self.bc.decir(hecho)

        # 2. accion <- PREGUNTAR(BC, PEDIR-ACCION(t)).
        movimiento, consulta, consultas = self.pedir_accion(validas)

        # 3. DECIR(BC, CONSTRUIR-SENTENCIA-DE-ACCION(accion, t)).
        sentencia_accion = self.construir_sentencia_de_accion(movimiento)
        self.bc.decir(sentencia_accion)

        # Estadísticas para el motor y la interfaz, sin intervenir en la decisión.
        percepciones = self._percibir(estado)
        modo = "INFERENCIA" if percepciones else "PATRULLA"
        gx, gy = estado.pos_agente
        dx, dy = ACCIONES[movimiento]
        self._estadisticas = {
            "turno": estado.numero_turno,
            "tiempo": self.t,
            "modo": modo,
            "percepciones": percepciones,
            "hechos_actuales": hechos,
            "inferencia": self.REGLAS[movimiento][1] if percepciones else None,
            "consulta_accion": consulta,
            "consultas": consultas,
            "accion": movimiento,
            "sentencia_accion": sentencia_accion,
            "destino": (gx + dx, gy + dy),
        }

        # 4. t <- t + 1.
        self.t += 1
        # 5. return accion.
        return movimiento

    def obtener_estadisticas(self) -> dict[str, Any]:
        resultado = dict(self._estadisticas)
        for clave in ("percepciones", "hechos_actuales"):
            if clave in resultado:
                resultado[clave] = list(resultado[clave])
        return resultado
