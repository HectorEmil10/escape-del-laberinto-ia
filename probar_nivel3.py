"""Ejecuta solamente el nivel 3 con la interfaz existente."""
from pathlib import Path

from agentes.nivel3_guardian import AgenteGuardian
from interfaz.consola_basica import ejecutar_en_consola
from nucleo.mapa import cargar_laberinto_desde_archivo
from nucleo.motor import MotorJuego

if __name__ == "__main__":
    ruta = Path(__file__).resolve().parent / "mapas" / "nivel3.txt"
    lab = cargar_laberinto_desde_archivo(ruta, nombre="Nivel 3 - Lógica Proposicional")
    ejecutar_en_consola(MotorJuego([(lab, AgenteGuardian())]))