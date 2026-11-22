from nucleo.estado import EstadoJuego, movimientos_validos
from nucleo.mapa import ALTO, ANCHO
from nucleo.motor import MotorJuego, ResultadoNivel

TECLAS_A_ACCION = {
    "w": "ARRIBA",
    "s": "ABAJO",
    "a": "IZQUIERDA",
    "d": "DERECHA",
}


def renderizar_ascii(estado: EstadoJuego) -> str:
    """Dibuja el tablero con y=10 arriba y y=1 abajo."""
    lab = estado.laberinto
    filas: list[str] = []
    for y in range(ALTO, 0, -1):
        celdas: list[str] = []
        for x in range(1, ANCHO + 1):
            pos = (x, y)
            if pos == estado.pos_jugador and pos == estado.pos_agente:
                celdas.append("X")  # Captura
            elif pos == estado.pos_jugador:
                celdas.append("P")
            elif pos == estado.pos_agente:
                celdas.append("G")
            elif pos == lab.salida:
                celdas.append("E")
            elif pos in lab.obstaculos:
                celdas.append("#")
            else:
                celdas.append(".")
        filas.append(f"{y:2d} | " + " ".join(celdas))
    filas.append("   +" + "--" * ANCHO)
    filas.append("     " + " ".join(str(x) for x in range(1, ANCHO + 1)))
    return "\n".join(filas)


def ejecutar_en_consola(motor: MotorJuego) -> None:
    while True:
        print(f"\n=== NIVEL {motor.nivel_actual}/{motor.total_niveles}: {motor.estado.laberinto.nombre} ===")
        print(f"Agente: {motor.agente_actual.nombre}")
        print(f"Turno: {motor.estado.numero_turno} | P={motor.estado.pos_jugador} | G={motor.estado.pos_agente}")
        print(renderizar_ascii(motor.estado))

        validas = movimientos_validos(motor.estado, actor="HUMANO")
        tecla = input(f"Mueve [W/A/S/D] (válidas: {validas}, Q para salir): ").strip().lower()
        if tecla == "q":
            print("Partida terminada por el usuario.")
            return
        accion_humano = TECLAS_A_ACCION.get(tecla)
        if accion_humano not in validas:
            print("Movimiento inválido. Intenta de nuevo.")
            continue

        resultado = motor.ejecutar_turno_humano(accion_humano)
        if resultado == ResultadoNivel.EN_CURSO:
            accion_agente, resultado = motor.ejecutar_turno_agente()
            stats = motor.agente_actual.obtener_estadisticas()
            info_extra = f" | {stats}" if stats else ""
            print(f"El agente se movió: {accion_agente}{info_extra}")

        if resultado == ResultadoNivel.CAPTURA_AGENTE:
            print(renderizar_ascii(motor.estado))
            print(f"\nCapturado en el nivel {motor.nivel_actual}.")
            reintentar = input("¿Reintentar nivel? [s/n]: ").strip().lower()
            if reintentar == "s":
                motor.iniciar_nivel(motor.indice_nivel)
            else:
                return
        elif resultado == ResultadoNivel.VICTORIA_HUMANO:
            print(renderizar_ascii(motor.estado))
            print(f"\nNivel {motor.nivel_actual} superado.")
            if not motor.avanzar_nivel():
                print("\n¡Felicidades! Completaste los 3 niveles consecutivos.")
                return