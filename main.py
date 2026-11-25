from interfaz.consola_basica import ejecutar_en_consola
from nucleo.agente_base import AgenteAleatorio
from nucleo.mapa import cargar_laberinto_desde_archivo
from nucleo.motor import MotorJuego

# Cuando integres los módulos del equipo, descomenta estas importaciones:
# from agentes.nivel1_astar import AgenteAStar
# from agentes.nivel2_alfabeta import AgenteAlfaBeta
from agentes.nivel3_guardian import AgenteGuardian


def construir_motor() -> MotorJuego:
    lab1 = cargar_laberinto_desde_archivo("mapas/nivel1.txt", nombre="Nivel 1 - A*")
    lab2 = cargar_laberinto_desde_archivo("mapas/nivel2.txt", nombre="Nivel 2 - Alfa-Beta")
    lab3 = cargar_laberinto_desde_archivo("mapas/nivel3.txt", nombre="Nivel 3 - Lógica Proposicional")

    niveles = [
        (lab1, AgenteAleatorio(semilla=1)),  # Reemplazar por AgenteAStar()
        (lab2, AgenteAleatorio(semilla=2)),  # Reemplazar por AgenteAlfaBeta(profundidad_max=4)
        (lab3, AgenteAleatorio(semilla=3)),  # Reemplazar por AgenteGuardian()
    ]
    return MotorJuego(niveles)


if __name__ == "__main__":
    motor = construir_motor()
    ejecutar_en_consola(motor)