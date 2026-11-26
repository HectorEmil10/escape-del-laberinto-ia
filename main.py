import sys
from pathlib import Path

from agentes.nivel1_astar import AgenteAStar
from agentes.nivel2_alfabeta import AgenteAlfaBeta
from agentes.nivel3_guardian import AgenteGuardian
from interfaz.consola_basica import ejecutar_en_consola
# Reemplaza esta línea con el import real que usa tu archivo main_grafico.py:
from interfaz.pygame_moria import ejecutar_en_pygame
from nucleo.mapa import cargar_laberinto_desde_archivo
from nucleo.motor import MotorJuego

DIRECTORIO_MAPAS = Path(__file__).resolve().parent / "mapas"

NIVELES_CONFIGURACION = [
    ("nivel1.txt", "Nivel 1 - A*"),
    ("nivel2.txt", "Nivel 2 - Alfa-Beta"),
    ("nivel3.txt", "Nivel 3 - Lógica Proposicional"),
]


def construir_motor() -> MotorJuego:
    agentes = [AgenteAStar(), AgenteAlfaBeta(), AgenteGuardian()]
    niveles = [
        (cargar_laberinto_desde_archivo(DIRECTORIO_MAPAS / archivo, nombre=titulo), agente)
        for (archivo, titulo), agente in zip(NIVELES_CONFIGURACION, agentes)
    ]
    return MotorJuego(niveles)


def main() -> None:
    motor = construir_motor()
    if "--consola" in sys.argv:
        ejecutar_en_consola(motor)
    else:
        ejecutar_en_pygame(motor)


if __name__ == "__main__":
    main()