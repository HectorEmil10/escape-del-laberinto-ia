"""Pruebas del motor proposicional — integrante 4.

Ejecutar desde la raíz del repositorio:
    python -m unittest discover -s pruebas -v
"""

import unittest

from agentes.motor_logico import BaseConocimiento, ReglaHorn, crear_base_para_turno


class TestMotorLogico(unittest.TestCase):
    def test_ejemplo_del_tema4(self):
        bc = BaseConocimiento(hechos=("A", "B", "E"))
        bc.agregar_regla(("A", "B"), "C")
        bc.agregar_regla(("C",), "D")
        bc.agregar_regla(("B", "E"), "F")
        bc.agregar_regla(("D", "F"), "G")
        self.assertTrue(bc.preguntar("G"))
        self.assertEqual(bc.inferir_todos(), {"A", "B", "C", "D", "E", "F", "G"})

    def test_premisas_incompletas(self):
        bc = BaseConocimiento(hechos=("A",))
        bc.agregar_regla(("A", "B"), "C")
        self.assertFalse(bc.preguntar("C"))

    def test_encadenamiento_de_tres_saltos(self):
        bc = BaseConocimiento(hechos=("P",))
        bc.agregar_regla(("P",), "Q")
        bc.agregar_regla(("Q",), "R")
        self.assertTrue(bc.preguntar("R"))
        self.assertFalse(bc.preguntar("S"))

    def test_ciclo_sin_hechos(self):
        bc = BaseConocimiento()
        bc.agregar_regla(("A",), "B")
        bc.agregar_regla(("B",), "A")
        self.assertFalse(bc.preguntar("A"))

    def test_ciclo_con_hecho(self):
        bc = BaseConocimiento(hechos=("A",))
        bc.agregar_regla(("A",), "B")
        bc.agregar_regla(("B",), "A")
        self.assertTrue(bc.preguntar("B"))

    def test_preguntar_no_mutar_hechos(self):
        bc = BaseConocimiento(hechos=("P",))
        bc.agregar_regla(("P",), "Q")
        self.assertTrue(bc.preguntar("Q"))
        self.assertEqual(bc.hechos, {"P"})
        self.assertTrue(bc.preguntar("Q"))

    def test_regla_sin_premisas(self):
        bc = BaseConocimiento(reglas=(ReglaHorn((), "Inicio"),))
        self.assertTrue(bc.preguntar("Inicio"))

    def test_premisas_duplicadas(self):
        bc = BaseConocimiento(hechos=("A",))
        bc.agregar_regla(("A", "A"), "B")
        self.assertTrue(bc.preguntar("B"))

    def test_explicar(self):
        bc = BaseConocimiento(hechos=("A",))
        bc.agregar_regla(("A",), "B")
        correcto, pasos = bc.explicar("B")
        self.assertTrue(correcto)
        self.assertEqual(pasos, ["A ⇒ B"])

    def test_validacion_de_simbolos(self):
        with self.assertRaises(ValueError):
            BaseConocimiento(hechos=("Jugador Arriba",))
        with self.assertRaises(ValueError):
            ReglaHorn(("P",), "")
        with self.assertRaises(TypeError):
            ReglaHorn("P", "Q")

    def test_consulta_del_guardian_en_celda_adyacente(self):
        reglas = (
            ReglaHorn(("JugadorArriba", "CeldaArribaLibre"), "MoverArriba"),
            ReglaHorn(("JugadorAbajo", "CeldaAbajoLibre"), "MoverAbajo"),
        )
        bc = crear_base_para_turno(reglas, ("JugadorArriba", "CeldaArribaLibre"))
        self.assertTrue(bc.preguntar("MoverArriba"))
        self.assertFalse(bc.preguntar("MoverAbajo"))

    def test_no_hay_accion_sin_percepcion(self):
        reglas = (ReglaHorn(("JugadorDerecha",), "MoverDerecha"),)
        bc = crear_base_para_turno(reglas, ())
        self.assertFalse(bc.preguntar("MoverDerecha"))

    def test_no_hay_percepciones_obsoletas_de_turnos_anteriores(self):
        regla = ReglaHorn(("JugadorDerecha",), "MoverDerecha")
        primero = crear_base_para_turno((regla,), ("JugadorDerecha",))
        segundo = crear_base_para_turno((regla,), ())
        self.assertTrue(primero.preguntar("MoverDerecha"))
        self.assertFalse(segundo.preguntar("MoverDerecha"))

    def test_reglas_con_misma_conclusion(self):
        bc = BaseConocimiento(hechos=("B",))
        bc.agregar_regla(("A",), "Mover")
        bc.agregar_regla(("B",), "Mover")
        self.assertTrue(bc.preguntar("Mover"))

    def test_sin_reglas_solo_hechos(self):
        bc = BaseConocimiento(hechos=("A",))
        self.assertTrue(bc.preguntar("A"))
        self.assertFalse(bc.preguntar("B"))

    def test_regla_repetida_no_se_agrega_dos_veces(self):
        regla = ReglaHorn(("A",), "B")
        bc = BaseConocimiento(reglas=(regla, regla), hechos=("A",))
        self.assertEqual(len(bc.reglas), 1)
        self.assertTrue(bc.preguntar("B"))


if __name__ == "__main__":
    unittest.main()
