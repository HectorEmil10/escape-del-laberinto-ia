"""Comprueba carga, contrato y progresión de los tres niveles oficiales.

Las posiciones próximas a la salida solo se usan para probar las transiciones
entre niveles, sin sustituir la ejecución real de las técnicas de IA.
"""

from dataclasses import replace
from pathlib import Path
import unittest

from agentes.nivel1_astar import AgenteAStar
from agentes.nivel2_alfabeta import AgenteAlfaBeta
from agentes.nivel3_guardian import AgenteGuardian
from nucleo.estado import movimientos_validos
from nucleo.mapa import cargar_laberinto_desde_archivo
from nucleo.motor import MotorJuego, ResultadoNivel

RAIZ = Path(__file__).resolve().parents[1]


def construir():
    agentes = (AgenteAStar(), AgenteAlfaBeta(), AgenteGuardian())
    niveles = [
        (cargar_laberinto_desde_archivo(RAIZ / "mapas" / f"nivel{i}.txt"), agente)
        for i, agente in enumerate(agentes, start=1)
    ]
    return MotorJuego(niveles)


class TestIntegracionTresNiveles(unittest.TestCase):
    def test_contrato_carga_y_turnos_iniciales(self):
        motor = construir()
        self.assertEqual(motor.total_niveles, 3)
        for indice in range(3):
            motor.iniciar_nivel(indice)
            self.assertEqual(motor.estado.pos_jugador, (1, 1))
            self.assertEqual(motor.estado.laberinto.salida, (10, 10))
            self.assertEqual(motor.estado.turno, "HUMANO")
            self.assertTrue(movimientos_validos(motor.estado))

    def test_avance_entre_niveles_y_finalizacion(self):
        motor = construir()
        for indice in range(3):
            self.assertEqual(motor.nivel_actual, indice + 1)
            # Estado de prueba inmediato a la salida; se evalúa el motor,
            # no se reemplazan las rutas ni decisiones del videojuego.
            motor.estado = replace(motor.estado, pos_jugador=(9, 10))
            self.assertEqual(motor.ejecutar_turno_humano("DERECHA"),
                             ResultadoNivel.VICTORIA_HUMANO)
            self.assertEqual(motor.avanzar_nivel(), indice < 2)
        self.assertEqual(motor.nivel_actual, 3)


if __name__ == "__main__":
    unittest.main()
