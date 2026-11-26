"""Pruebas del agente minimax/alfa-beta del nivel 2.

Se evalúa el agente de forma aislada de la interfaz gráfica.
"""

import contextlib
import io
import unittest

from agentes.nivel2_alfabeta import AgenteAlfaBeta, EstadoSimulacion
from nucleo.estado import EstadoJuego, aplicar_movimiento, estado_inicial, movimientos_validos
from nucleo.mapa import cargar_laberinto_desde_archivo
from pathlib import Path

MAPA = Path(__file__).resolve().parents[1] / "mapas" / "nivel2.txt"


class TestAgenteAlfaBeta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.laberinto = cargar_laberinto_desde_archivo(MAPA)

    def estado_del_primer_turno(self):
        return aplicar_movimiento(estado_inicial(self.laberinto), "ARRIBA")

    def decidir(self, agente, estado):
        # El agente actual imprime la cifra de nodos, sin afectar a la decisión.
        with contextlib.redirect_stdout(io.StringIO()):
            return agente.elegir_movimiento(estado)

    def test_profundidad_cuatro_por_defecto(self):
        self.assertEqual(AgenteAlfaBeta().profundidad_max, 4)

    def test_movimiento_legal_en_escenario_oficial(self):
        estado = self.estado_del_primer_turno()
        accion = self.decidir(AgenteAlfaBeta(), estado)
        self.assertIn(accion, movimientos_validos(estado))

    def test_captura_inmediata_en_estado_de_prueba(self):
        # La proximidad es intencional: verifica una decisión del algoritmo
        # independientemente de si surge en el escenario oficial.
        estado = EstadoJuego(self.laberinto, (9, 9), (9, 10), turno="AGENTE")
        accion = self.decidir(AgenteAlfaBeta(), estado)
        self.assertEqual(accion, "ABAJO")

    def test_utilidad_de_terminales(self):
        captura = EstadoSimulacion((5, 5), (5, 5), (10, 10), self.laberinto)
        escape = EstadoSimulacion((1, 1), (10, 10), (10, 10), self.laberinto)
        self.assertEqual(captura.es_terminal(), "captura")
        self.assertEqual(captura.utilidad(), 1000)
        self.assertEqual(escape.es_terminal(), "escape")
        self.assertEqual(escape.utilidad(), -1000)

    def test_heuristica_de_estado_no_terminal(self):
        estado = EstadoSimulacion((2, 2), (3, 2), (10, 10), self.laberinto)
        self.assertEqual(estado.evaluar_heuristica(), 15 - 1)

    def test_el_arbol_no_supera_profundidad_maxima(self):
        class Instrumentado(AgenteAlfaBeta):
            def __init__(self):
                super().__init__()
                self.profundidades = []
            def _max_valor(self, estado, alfa, beta, profundidad_actual):
                self.profundidades.append(profundidad_actual)
                return super()._max_valor(estado, alfa, beta, profundidad_actual)
            def _min_valor(self, estado, alfa, beta, profundidad_actual):
                self.profundidades.append(profundidad_actual)
                return super()._min_valor(estado, alfa, beta, profundidad_actual)
        agente = Instrumentado()
        self.decidir(agente, self.estado_del_primer_turno())
        self.assertIn(4, agente.profundidades)
        self.assertLessEqual(max(agente.profundidades), 4)

    def test_poda_reduce_expansiones_contra_minimax_sin_poda(self):
        estado = self.estado_del_primer_turno()
        sim = EstadoSimulacion(estado.pos_agente, estado.pos_jugador,
                               estado.laberinto.salida, estado.laberinto)
        # Contador equivalente al del agente: cuenta nodos raíz e internos
        # expandidos, no hojas terminales ni hojas por profundidad.
        def sin_poda(nodo, profundidad, maximo):
            if nodo.es_terminal() is not None:
                return nodo.utilidad(), 0
            if profundidad >= 4:
                return nodo.evaluar_heuristica(), 0
            hijos = nodo.sucesores_max() if maximo else nodo.sucesores_min()
            valores, expandidos = [], 1
            for _, hijo in hijos:
                valor, cuenta = sin_poda(hijo, profundidad + 1, not maximo)
                valores.append(valor)
                expandidos += cuenta
            return (max(valores) if maximo else min(valores)), expandidos
        total_sin_poda = 0
        for _, hijo in sim.sucesores_max():
            _, internos = sin_poda(hijo, 1, False)
            total_sin_poda += 1 + internos
        agente = AgenteAlfaBeta()
        self.decidir(agente, estado)
        total_con_poda = agente.obtener_estadisticas()["nodos_explorados"]
        self.assertLess(total_con_poda, total_sin_poda)

    def test_reinicio_limpia_estadisticas(self):
        agente = AgenteAlfaBeta()
        self.decidir(agente, self.estado_del_primer_turno())
        self.assertGreater(agente.obtener_estadisticas()["nodos_explorados"], 0)
        agente.reiniciar()
        self.assertEqual(agente.obtener_estadisticas()["nodos_explorados"], 0)
        self.assertIsNone(agente.ultima_accion)


if __name__ == "__main__":
    unittest.main()
