from interfaz.consola_basica import ejecutar_en_consola
from nucleo.agente_base import AgenteAleatorio
from nucleo.mapa import cargar_laberinto_desde_archivo
from nucleo.motor import MotorJuego

# Cuando se integren los modulos, descomenten esto
from agentes.nivel1_astar import AgenteAStar
# from agentes.nivel2_alfabeta import AgenteAlfaBeta
from agentes.nivel3_guardian import AgenteGuardian


def construir_motor() -> MotorJuego:
    lab1 = cargar_laberinto_desde_archivo("mapas/nivel1.txt", nombre="Nivel 1 - A*")
    lab2 = cargar_laberinto_desde_archivo("mapas/nivel2.txt", nombre="Nivel 2 - Alfa-Beta")
    lab3 = cargar_laberinto_desde_archivo("mapas/nivel3.txt", nombre="Nivel 3 - Lógica Proposicional")

    niveles = [
        (lab1, AgenteAStar()), 
        (lab2, AgenteAleatorio(semilla=2)),  #se cambia nombre por el que se quiera
        (lab3, AgenteAleatorio(semilla=3)),  #se cambia nombre por el que se quiera
    ]
    return MotorJuego(niveles)


if __name__ == "__main__":
    motor = construir_motor()
    ejecutar_en_consola(motor)