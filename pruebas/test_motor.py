import unittest

from nucleo.agente_base import AgenteBase
from nucleo.estado import (
    EstadoJuego,
    aplicar_movimiento,
    es_captura,
    es_escape,
    estado_inicial,
    sucesores,
)
from nucleo.mapa import cargar_laberinto_desde_texto
from nucleo.motor import MotorJuego, ResultadoNivel

MAPA_PRUEBA = """
.........E
........G.
..........
..........
..........
..........
..........
..........
.#........
P.........
"""


class AgenteFijo(AgenteBase):
    def __init__(self, acciones: list[str]) -> None:
        super().__init__(nombre="AgenteFijo")
        self._acciones = list(acciones)
        self._i = 0

    def elegir_movimiento(self, estado: EstadoJuego) -> str:
        accion = self._acciones[self._i % len(self._acciones)]
        self._i += 1
        return accion

    def reiniciar(self) -> None:
        self._i = 0


class TestMotorJuego(unittest.TestCase):
    def setUp(self) -> None:
        self.lab = cargar_laberinto_desde_texto(MAPA_PRUEBA, "MapaPrueba")

    def test_coordenadas_cartesianas(self) -> None:
        self.assertEqual(self.lab.inicio_jugador, (1, 1))
        self.assertEqual(self.lab.salida, (10, 10))
        self.assertEqual(self.lab.inicio_agente, (9, 9))
        self.assertIn((2, 2), self.lab.obstaculos)

    def test_inmutabilidad_y_sucesores(self) -> None:
        inicial = estado_inicial(self.lab)
        hijos = dict(sucesores(inicial))
        self.assertIn("ARRIBA", hijos)
        self.assertIn("DERECHA", hijos)
        self.assertNotIn("ABAJO", hijos)
        self.assertNotIn("IZQUIERDA", hijos)
        self.assertEqual(inicial.pos_jugador, (1, 1))  # No mutado
        self.assertEqual(hijos["ARRIBA"].pos_jugador, (1, 2))
        self.assertEqual(hijos["ARRIBA"].turno, "AGENTE")

    def test_bloqueo_obstaculo(self) -> None:
        e1 = aplicar_movimiento(estado_inicial(self.lab), "ARRIBA")  # P en (1, 2)
        e2 = aplicar_movimiento(e1, "IZQUIERDA")  # G en (8, 9), turno HUMANO
        with self.assertRaises(ValueError):
            aplicar_movimiento(e2, "DERECHA")  # (2, 2) es '#'

    def test_escape_y_captura(self) -> None:
        cerca_salida = EstadoJuego(self.lab, pos_jugador=(9, 10), pos_agente=(5, 5), turno="HUMANO")
        escapo = aplicar_movimiento(cerca_salida, "DERECHA")
        self.assertTrue(es_escape(escapo))
        self.assertFalse(es_captura(escapo))

        cerca_agente = EstadoJuego(self.lab, pos_jugador=(5, 5), pos_agente=(5, 6), turno="AGENTE")
        capturado = aplicar_movimiento(cerca_agente, "ABAJO")
        self.assertTrue(es_captura(capturado))
        self.assertFalse(es_escape(capturado))

    def test_flujo_motor_turnos(self) -> None:
        motor = MotorJuego([(self.lab, AgenteFijo(["IZQUIERDA"]))])
        res_h = motor.ejecutar_turno_humano("DERECHA")
        self.assertEqual(res_h, ResultadoNivel.EN_CURSO)
        self.assertEqual(motor.estado.pos_jugador, (2, 1))
        accion_a, res_a = motor.ejecutar_turno_agente()
        self.assertEqual(accion_a, "IZQUIERDA")
        self.assertEqual(res_a, ResultadoNivel.EN_CURSO)
        self.assertEqual(motor.estado.pos_agente, (8, 9))
        self.assertEqual(motor.estado.numero_turno, 2)


if __name__ == "__main__":
    unittest.main()