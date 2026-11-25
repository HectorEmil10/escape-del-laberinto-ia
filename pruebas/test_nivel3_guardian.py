import unittest
from pathlib import Path

from agentes.nivel3_guardian import AgenteGuardian
from agentes.motor_logico import BaseConocimiento
from nucleo.estado import EstadoJuego, aplicar_movimiento, es_captura, movimientos_validos
from nucleo.mapa import cargar_laberinto_desde_archivo
from nucleo.motor import MotorJuego, ResultadoNivel

RUTA_MAPA = Path(__file__).resolve().parents[1] / "mapas" / "nivel3.txt"


class TestGuardian(unittest.TestCase):
    def setUp(self):
        self.lab = cargar_laberinto_desde_archivo(RUTA_MAPA)
        self.agente = AgenteGuardian()

    def estado(self, jugador, guardian=(8, 9), turno=1):
        return EstadoJuego(self.lab, jugador, guardian, "AGENTE", turno)

    def test_patrulla_completa(self):
        posiciones = [(8, 9), (9, 9), (9, 8), (8, 8), (8, 9)]
        acciones = ["DERECHA", "ABAJO", "IZQUIERDA", "ARRIBA"]
        for i, esperada in enumerate(acciones):
            estado = self.estado((1, 1), posiciones[i], i + 1)
            accion = self.agente.elegir_movimiento(estado)
            self.assertEqual(accion, esperada)
            self.assertIn(accion, movimientos_validos(estado))
            self.assertEqual(aplicar_movimiento(estado, accion).pos_agente, posiciones[i + 1])
            self.assertEqual(self.agente.obtener_estadisticas()["modo"], "PATRULLA")

    def test_captura_en_cuatro_direcciones(self):
        casos = [((9, 10), "ARRIBA"), ((9, 8), "ABAJO"),
                 ((8, 9), "IZQUIERDA"), ((10, 9), "DERECHA")]
        for jugador, esperada in casos:
            with self.subTest(direccion=esperada):
                estado = self.estado(jugador, (9, 9))
                accion = self.agente.elegir_movimiento(estado)
                self.assertEqual(accion, esperada)
                self.assertTrue(es_captura(aplicar_movimiento(estado, accion)))
                stats = self.agente.obtener_estadisticas()
                self.assertEqual(stats["modo"], "INFERENCIA")
                self.assertEqual(stats["inferencia"], self.agente.REGLAS[esperada][1])

    def test_diagonal_no_es_percepcion(self):
        estado = self.estado((7, 8))
        self.assertEqual(self.agente.elegir_movimiento(estado), "DERECHA")
        self.assertEqual(self.agente.obtener_estadisticas()["percepciones"], [])

    def test_percepciones_no_se_acumulan(self):
        self.agente.elegir_movimiento(self.estado((8, 10)))
        self.assertEqual(self.agente.obtener_estadisticas()["inferencia"], "MoverArriba")
        self.agente.elegir_movimiento(self.estado((1, 1), turno=2))
        self.assertEqual(self.agente.obtener_estadisticas()["modo"], "PATRULLA")
        self.assertIsNone(self.agente.obtener_estadisticas()["inferencia"])
        self.assertIn("JugadorArriba_0", self.agente.bc.hechos)
        self.assertTrue(self.agente.bc.preguntar("MoverArriba_0"))
        self.assertFalse(self.agente.bc.preguntar("MoverArriba_1"))
        self.assertTrue(self.agente.bc.preguntar("MoverDerecha_1"))

    def test_reinicio(self):
        self.agente.elegir_movimiento(self.estado((1, 1)))
        self.agente.reiniciar()
        self.assertEqual(self.agente.obtener_estadisticas(), {})
        self.assertEqual(self.agente.t, 0)
        self.assertEqual(self.agente.bc.hechos, set())
        self.assertEqual(self.agente.bc.reglas, [])
        self.assertEqual(self.agente.elegir_movimiento(self.estado((1, 1))), "DERECHA")

    def test_decision_consulta_motor_logico(self):
        class BCRegistro(BaseConocimiento):
            def __init__(self):
                super().__init__()
                self.consultas = []

            def preguntar(self, objetivo):
                self.consultas.append(objetivo)
                return super().preguntar(objetivo)

        instancias = []
        def crear():
            bc = BCRegistro()
            instancias.append(bc)
            return bc

        agente = AgenteGuardian(fabrica_bc=crear)
        self.assertEqual(agente.elegir_movimiento(self.estado((8, 10))), "ARRIBA")
        self.assertIn("JugadorArriba_0", instancias[0].hechos)
        self.assertIn("MoverArriba_0", instancias[0].consultas)
        self.assertIn("AccionElegida_ARRIBA_0", instancias[0].hechos)

    def test_bc_persistente_y_contador(self):
        bc = self.agente.bc
        self.assertEqual(self.agente.t, 0)
        self.agente.elegir_movimiento(self.estado((1, 1)))
        self.assertEqual(self.agente.t, 1)
        self.agente.elegir_movimiento(self.estado((1, 1), (9, 9), 2))
        self.assertEqual(self.agente.t, 2)
        self.assertIs(self.agente.bc, bc)
        self.assertIn("SinJugadorAdyacente_0", bc.hechos)
        self.assertIn("SinJugadorAdyacente_1", bc.hechos)
        self.assertIn("AccionElegida_DERECHA_0", bc.hechos)
        self.assertIn("AccionElegida_ABAJO_1", bc.hechos)
        self.assertTrue(bc.preguntar("MoverDerecha_0"))
        self.assertTrue(bc.preguntar("MoverAbajo_1"))
        self.assertFalse(bc.preguntar("MoverDerecha_1"))

    def test_patrulla_consulta_motor_logico(self):
        class BCRegistro(BaseConocimiento):
            def __init__(self):
                super().__init__()
                self.consultas = []

            def preguntar(self, objetivo):
                self.consultas.append(objetivo)
                return super().preguntar(objetivo)

        agente = AgenteGuardian(fabrica_bc=BCRegistro)
        self.assertEqual(agente.elegir_movimiento(self.estado((1, 1))), "DERECHA")
        self.assertIn("MoverDerecha_0", agente.bc.consultas)
        self.assertIn("AccionElegida_DERECHA_0", agente.bc.hechos)
        self.assertEqual(agente.obtener_estadisticas()["modo"], "PATRULLA")

    def test_captura_prevalece_sobre_patrulla(self):
        self.assertEqual(self.agente.elegir_movimiento(self.estado((8, 10))), "ARRIBA")
        self.assertTrue(self.agente.bc.preguntar("MoverArriba_0"))
        self.assertFalse(self.agente.bc.preguntar("MoverDerecha_0"))

    def test_integracion_motor(self):
        motor = MotorJuego([(self.lab, self.agente)])
        self.assertEqual(motor.ejecutar_turno_humano("DERECHA"), ResultadoNivel.EN_CURSO)
        accion, resultado = motor.ejecutar_turno_agente()
        self.assertEqual((accion, resultado), ("DERECHA", ResultadoNivel.EN_CURSO))
        self.assertEqual(motor.estado.pos_agente, (9, 9))
        self.assertEqual(motor.historial[-1].estadisticas_agente["modo"], "PATRULLA")

    def test_captura_en_motor(self):
        motor = MotorJuego([(self.lab, self.agente)])
        motor.estado = EstadoJuego(self.lab, (9, 7), (9, 9), "HUMANO")
        self.assertEqual(motor.ejecutar_turno_humano("ARRIBA"), ResultadoNivel.EN_CURSO)
        self.assertEqual(motor.ejecutar_turno_agente(), ("ABAJO", ResultadoNivel.CAPTURA_AGENTE))

    def test_partida_completa_desde_inicio(self):
        # Secuencia de prueba del humano, no parte del algoritmo del guardián.
        acciones = ["ARRIBA"] * 6 + ["DERECHA"] * 5 + ["ARRIBA"] + ["DERECHA"] * 2 + ["ARRIBA"] * 2 + ["DERECHA"] * 2
        motor = MotorJuego([(self.lab, self.agente)])
        for indice, accion in enumerate(acciones):
            resultado = motor.ejecutar_turno_humano(accion)
            if indice == len(acciones) - 1:
                self.assertEqual(resultado, ResultadoNivel.VICTORIA_HUMANO)
            else:
                self.assertEqual(resultado, ResultadoNivel.EN_CURSO)
                _, resultado_agente = motor.ejecutar_turno_agente()
                self.assertEqual(resultado_agente, ResultadoNivel.EN_CURSO)
        self.assertEqual(motor.estado.pos_jugador, (10, 10))

    def test_escape_en_motor(self):
        motor = MotorJuego([(self.lab, self.agente)])
        motor.estado = EstadoJuego(self.lab, (9, 10), (8, 8), "HUMANO")
        self.assertEqual(motor.ejecutar_turno_humano("DERECHA"), ResultadoNivel.VICTORIA_HUMANO)


class TestMotorLogico(unittest.TestCase):
    def test_ejemplo_diapositiva_64(self):
        bc = BaseConocimiento()
        for hecho in ("A", "B", "E"):
            bc.decir(hecho)
        bc.decir(("A", "B"), "C")
        bc.decir(("C",), "D")
        bc.decir(("B", "E"), "F")
        bc.decir(("D", "F"), "G")
        self.assertTrue(bc.preguntar("G"))
        self.assertFalse(bc.preguntar("X"))

    def test_premisas_incompletas(self):
        bc = BaseConocimiento()
        bc.decir(("A", "B"), "C")
        bc.decir("A")
        self.assertFalse(bc.preguntar("C"))
        bc.decir("B")
        self.assertTrue(bc.preguntar("C"))

    def test_ciclo_y_duplicados(self):
        bc = BaseConocimiento()
        bc.decir(("A",), "B")
        bc.decir(("B",), "A")
        bc.decir(("A",), "B")
        self.assertFalse(bc.preguntar("B"))
        bc.decir("A")
        self.assertTrue(bc.preguntar("B"))
        self.assertFalse(bc.preguntar("C"))

    def test_clausula_sin_premisas(self):
        bc = BaseConocimiento()
        bc.decir((), "A")
        bc.decir(("A",), "B")
        self.assertTrue(bc.preguntar("B"))


if __name__ == "__main__":
    unittest.main()
