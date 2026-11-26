# -*- coding: utf-8 -*-
"""Nivel 2: Agente perseguidor con Minimax y poda alfa-beta.

Se basa en los Algoritmos 9, 10 y 11 (DECISIÓN-MINIMAX, MAX-VALOR y MIN-VALOR con poda) del Tema 3.
El agente es el jugador MAX (perseguidor) y el humano es MIN.
"""

from nucleo.agente_base import AgenteBase
from nucleo.estado import EstadoJuego, movimientos_validos
from nucleo.mapa import ACCIONES, Laberinto, Posicion, distancia_manhattan  # noqa: F401


class EstadoSimulacion:
    """Clase auxiliar ligera para simular estados futuros en el árbol de búsqueda 
    sin alterar el estado real del motor del juego proporcionado por el Integrante 1.
    """
    def __init__(self, pos_agente: Posicion, pos_jugador: Posicion, salida: Posicion, laberinto: Laberinto):
        self.pos_agente = pos_agente
        self.pos_jugador = pos_jugador
        self.salida = salida
        self.laberinto = laberinto

    def es_terminal(self) -> str | None:
        """Determina si el estado es terminal:
        - Captura: El agente (MAX) ocupa la misma celda que el humano (MIN).
        - Escape: El humano (MIN) alcanza la celda de la salida.
        """
        if self.pos_agente == self.pos_jugador:
            return "captura"
        if self.pos_jugador == self.salida:
            return "escape"
        return None

    def utilidad(self) -> int:
        """Asigna una utilidad numérica a los estados terminales desde la perspectiva de MAX."""
        resultado = self.es_terminal()
        if resultado == "captura":
            return 1000   # Gana el agente (MAX)
        elif resultado == "escape":
            return -1000  # Gana el humano (MIN)
        return 0

    def evaluar_heuristica(self) -> int:
        """Función heurística para estados no terminales al alcanzar la profundidad máxima.
        Fórmula: Distancia del humano a la salida - Distancia del agente al humano.
        Busca que el humano esté más lejos de la salida y más cerca del agente.
        """
        d_humano_salida = distancia_manhattan(self.pos_jugador, self.salida)
        d_agente_humano = distancia_manhattan(self.pos_agente, self.pos_jugador)
        return d_humano_salida - d_agente_humano

    def sucesores_max(self) -> list[tuple[str, "EstadoSimulacion"]]:
        """Genera los sucesores para el turno de MAX (Agente) usando laberinto.vecinos."""
        lista = []
        for accion, nueva_pos in self.laberinto.vecinos(self.pos_agente):
            nuevo_estado = EstadoSimulacion(nueva_pos, self.pos_jugador, self.salida, self.laberinto)
            lista.append((accion, nuevo_estado))
        return lista

    def sucesores_min(self) -> list[tuple[str, "EstadoSimulacion"]]:
        """Genera los sucesores para el turno de MIN (Humano) usando laberinto.vecinos."""
        lista = []
        for accion, nueva_pos in self.laberinto.vecinos(self.pos_jugador):
            nuevo_estado = EstadoSimulacion(self.pos_agente, nueva_pos, self.salida, self.laberinto)
            lista.append((accion, nuevo_estado))
        return lista


class AgenteAlfaBeta(AgenteBase):
    def __init__(self, profundidad_max: int = 4) -> None:
        super().__init__(nombre="Agente Minimax Alfa-Beta (Nivel 2)")
        self.profundidad_max = profundidad_max
        self._nodos_explorados: int = 0
        self.ultima_accion: str | None = None

    # ------------------------------------------------------------------
    # Contrato con el motor
    # ------------------------------------------------------------------
    def elegir_movimiento(self, estado: EstadoJuego) -> str:
        # Obtenemos la posición de la salida desde el estado o el laberinto
        salida_celda = getattr(estado, "salida", getattr(estado.laberinto, "salida", (10, 10)))
        
        sim_estado = EstadoSimulacion(
            pos_agente=estado.pos_agente,
            pos_jugador=estado.pos_jugador,
            salida=salida_celda,
            laberinto=estado.laberinto
        )

        self._nodos_explorados = 0
        alfa = -float('inf')
        beta = float('inf')
        
        mejor_valor = -float('inf')
        mejor_accion = None

        sucesores = sim_estado.sucesores_max()
        if not sucesores:
            self.ultima_accion = None
            return movimientos_validos(estado, actor="AGENTE")[0]

        # Algoritmo 9: DECISIÓN-MINIMAX con alfa-beta
        for accion, sucesor in sucesores:
            self._nodos_explorados += 1
            # Profundidad 1 consumida por este primer movimiento de MAX
            valor = self._min_valor(sucesor, alfa, beta, profundidad_actual=1)
            
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_accion = accion
                
            alfa = max(alfa, mejor_valor)

        print(f"[Nivel 2] Nodos explorados con poda alfa-beta: {self._nodos_explorados}")
        self.ultima_accion = mejor_accion
        return mejor_accion if mejor_accion else movimientos_validos(estado, actor="AGENTE")[0]

    def reiniciar(self) -> None:
        self._nodos_explorados = 0
        self.ultima_accion = None

    def obtener_estadisticas(self) -> dict:
        return {"nodos_explorados": self._nodos_explorados}

    # ------------------------------------------------------------------
    # Algoritmo 10: MAX_VALOR con poda alfa-beta
    # ------------------------------------------------------------------
    def _max_valor(self, estado: EstadoSimulacion, alfa: float, beta: float, profundidad_actual: int) -> float:
        if estado.es_terminal() is not None or profundidad_actual >= self.profundidad_max:
            if estado.es_terminal() is not None:
                return estado.utilidad()
            return estado.evaluar_heuristica()

        self._nodos_explorados += 1
        v = -float('inf')
        
        for _, sucesor in estado.sucesores_max():
            v = max(v, self._min_valor(sucesor, alfa, beta, profundidad_actual + 1))
            if v >= beta:
                return v  # Poda Beta
            alfa = max(alfa, v)
        return v

    # ------------------------------------------------------------------
    # Algoritmo 11: MIN_VALOR con poda alfa-beta
    # ------------------------------------------------------------------
    def _min_valor(self, estado: EstadoSimulacion, alfa: float, beta: float, profundidad_actual: int) -> float:
        if estado.es_terminal() is not None or profundidad_actual >= self.profundidad_max:
            if estado.es_terminal() is not None:
                return estado.utilidad()
            return estado.evaluar_heuristica()

        self._nodos_explorados += 1
        v = float('inf')
        
        for _, sucesor in estado.sucesores_min():
            v = min(v, self._max_valor(sucesor, alfa, beta, profundidad_actual + 1))
            if v <= alfa:
                return v  # Poda Alfa
            beta = min(beta, v)
        return v
