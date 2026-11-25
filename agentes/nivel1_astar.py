"""Nivel 1: agente perseguidor con A* (Integrante 2 Rodrigo Yo).

Se basa en el Algoritmo 5 (A*) del Tema 3.

Lo que ya nos da el motor del Integrante 1 (carpeta nucleo/):
  - Un estado es una celda (x, y). El estado del juego trae pos_agente y pos_jugador.
  - estado.laberinto.vecinos(pos) nos da los movimientos posibles desde una celda
    (cada uno cuesta 1). Salen en este orden: ARRIBA, ABAJO, IZQUIERDA, DERECHA,
    y ese orden afecta cuando hay rutas igual de cortas.
  - La heurística es distancia_manhattan(a, b), que ya está en nucleo/mapa.py.

Lo que hace _a_estrella: arma la frontera, g y padre, saca la celda con menor
f = g + h, y si es la meta arma la ruta hacia atrás con los padres. Si no es la
meta, revisa sus vecinos y los actualiza si son nuevos o si encontró un camino
más barato.

Con el motor: elegir_movimiento(estado) regresa 'ARRIBA', 'ABAJO', 'IZQUIERDA'
o 'DERECHA'. Se calcula en cada turno del agente (no hay rutas guardadas de
antes): el inicio es donde está el agente, la meta es donde está el jugador, y
solo se usa el primer paso de la ruta.
"""

import heapq
from itertools import count

from nucleo.agente_base import AgenteBase
from nucleo.estado import EstadoJuego, movimientos_validos
from nucleo.mapa import ACCIONES, Laberinto, Posicion, distancia_manhattan  # noqa: F401


class AgenteAStar(AgenteBase):
    def __init__(self) -> None:
        super().__init__(nombre="Agente A* (Nivel 1)")
        # La interfaz gráfica dibuja esta ruta cuando se presiona H.
        self.ultima_ruta: list[Posicion] = []
        self._nodos_explorados: int = 0

    # ------------------------------------------------------------------
    # Contrato con el motor
    # ------------------------------------------------------------------
    def elegir_movimiento(self, estado: EstadoJuego) -> str:
        inicio = estado.pos_agente
        meta = estado.pos_jugador

        ruta = self._a_estrella(inicio, meta, estado.laberinto)

        if ruta is not None and len(ruta) >= 2:
            self.ultima_ruta = ruta
            return self._accion_hacia(inicio, ruta[1])  # solo el primer paso

        # Sin ruta (o ya en la meta): el motor exige una acción válida.
        self.ultima_ruta = []
        return movimientos_validos(estado, actor="AGENTE")[0]

    def reiniciar(self) -> None:
        self.ultima_ruta = []
        self._nodos_explorados = 0

    def obtener_estadisticas(self) -> dict:
        stats: dict = {"nodos_explorados": self._nodos_explorados}
        if self.ultima_ruta:
            stats["pasos_ruta"] = len(self.ultima_ruta) - 1
        return stats

    # ------------------------------------------------------------------
    # Auxiliar: traduce "pasar de una celda a la siguiente" a una acción
    # ------------------------------------------------------------------
    @staticmethod
    def _accion_hacia(origen: Posicion, destino: Posicion) -> str:
        for accion, (dx, dy) in ACCIONES.items():
            if (origen[0] + dx, origen[1] + dy) == destino:
                return accion
        raise ValueError(f"{destino} no es vecino de {origen}.")

    # ------------------------------------------------------------------
    # Algoritmo 5 (A*)
    # ------------------------------------------------------------------
    def _a_estrella(self, inicio: Posicion, meta: Posicion, laberinto: Laberinto) -> list[Posicion] | None:
        """Devuelve la ruta [inicio, ..., meta] o None si no existe.

        Actualiza self._nodos_explorados (cuántos nodos se extrajeron de
        la frontera) para que se muestre en el panel de la interfaz.
        """
        # Inicialización: g(s) = 0, padre(s) = NULO y frontera con s, f(s) = h(s).
        g: dict[Posicion, int] = {inicio: 0}
        padre: dict[Posicion, Posicion | None] = {inicio: None}
        desempate = count()  # a igual f, sale primero el que se insertó antes
        frontera = [(distancia_manhattan(inicio, meta), next(desempate), inicio)]
        self._nodos_explorados = 0

        # Mientras la frontera no esté vacía.
        while frontera:
            # Extraer el nodo n con menor f(n).
            f_n, _, n = heapq.heappop(frontera)

            # Entrada vieja: luego se encontró un camino mejor hacia n. Se ignora.
            if f_n > g[n] + distancia_manhattan(n, meta):
                continue

            self._nodos_explorados += 1

            # Si n es la meta, se reconstruye la ruta siguiendo los padres hacia atrás
            if n == meta:
                ruta = []
                actual: Posicion | None = n
                while actual is not None:
                    ruta.append(actual)
                    actual = padre[actual]
                ruta.reverse()
                return ruta

            # Para cada vecino v de n, cada movimiento cuesta 1.
            for _accion, v in laberinto.vecinos(n):
                g_nuevo = g[n] + 1
                # v no explorado, o se encontró un camino más barato hacia v.
                if v not in g or g_nuevo < g[v]:
                    g[v] = g_nuevo
                    padre[v] = n
                    f_v = g_nuevo + distancia_manhattan(v, meta)
                    heapq.heappush(frontera, (f_v, next(desempate), v))

        # La frontera se vació sin llegar a la meta: no hay ruta.
        return None
