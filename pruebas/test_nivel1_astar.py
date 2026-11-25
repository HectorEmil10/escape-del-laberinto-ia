import unittest

from agentes.nivel1_astar import AgenteAStar
from nucleo.agente_base import AgenteBase
from nucleo.estado import EstadoJuego, aplicar_movimiento, movimientos_validos
from nucleo.mapa import cargar_laberinto_desde_archivo, cargar_laberinto_desde_texto

# Mapa donde el jugador (1, 1) queda encerrado: no existe ruta hacia él.
MAPA_ENCERRADO = """
.........E
........G.
..........
..........
..........
..........
..........
..........
#.........
P#........
"""


class TestAgenteAStar(unittest.TestCase):
    def setUp(self) -> None:
        self.lab = cargar_laberinto_desde_archivo("mapas/nivel1.txt", nombre="Nivel 1")
        self.agente = AgenteAStar()

    def _estado_agente(self, lab, jugador, agente) -> EstadoJuego:
        return EstadoJuego(lab, pos_jugador=jugador, pos_agente=agente, turno="AGENTE")

    def test_cumple_el_contrato(self) -> None:
        self.assertIsInstance(self.agente, AgenteBase)
        estado = self._estado_agente(self.lab, self.lab.inicio_jugador, self.lab.inicio_agente)
        accion = self.agente.elegir_movimiento(estado)
        self.assertIn(accion, movimientos_validos(estado, actor="AGENTE"))

    def test_ruta_optima_nivel_1(self) -> None:
        # Jugador quieto en (1, 1): el agente llega en tantos turnos como pasos tiene la ruta óptima.
        pos_agente = self.lab.inicio_agente  # (8, 10)
        pasos = 0
        while pos_agente != (1, 1) and pasos < 60:
            estado = self._estado_agente(self.lab, (1, 1), pos_agente)
            accion = self.agente.elegir_movimiento(estado)
            self.assertIn(accion, movimientos_validos(estado, actor="AGENTE"))
            pos_agente = aplicar_movimiento(estado, accion).pos_agente
            pasos += 1
        self.assertEqual(pos_agente, (1, 1))
        self.assertEqual(pasos, 16)  # distancia Manhattan = 16 y el camino no necesita rodeos

    def test_ultima_ruta_y_estadisticas(self) -> None:
        estado = self._estado_agente(self.lab, self.lab.inicio_jugador, self.lab.inicio_agente)
        self.agente.elegir_movimiento(estado)
        self.assertEqual(self.agente.ultima_ruta[0], self.lab.inicio_agente)
        self.assertEqual(self.agente.ultima_ruta[-1], self.lab.inicio_jugador)
        self.assertGreater(self.agente.obtener_estadisticas()["nodos_explorados"], 0)
        self.agente.reiniciar()
        self.assertEqual(self.agente.ultima_ruta, [])

    def test_sin_ruta_devuelve_movimiento_valido(self) -> None:
        lab = cargar_laberinto_desde_texto(MAPA_ENCERRADO, "Encerrado")
        estado = self._estado_agente(lab, (1, 1), lab.inicio_agente)
        accion = self.agente.elegir_movimiento(estado)
        self.assertIn(accion, movimientos_validos(estado, actor="AGENTE"))


if __name__ == "__main__":
    unittest.main()
