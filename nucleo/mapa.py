from dataclasses import dataclass
from pathlib import Path

ANCHO = 10
ALTO = 10

SIMBOLO_JUGADOR = "P"
SIMBOLO_AGENTE = "G"
SIMBOLO_SALIDA = "E"
SIMBOLO_OBSTACULO = "#"
SIMBOLO_LIBRE = "."
SIMBOLOS_VALIDOS = {
    SIMBOLO_JUGADOR,
    SIMBOLO_AGENTE,
    SIMBOLO_SALIDA,
    SIMBOLO_OBSTACULO,
    SIMBOLO_LIBRE,
}

# Movimientos ortogonales en coordenadas cartesianas (x, y)
ACCIONES: dict[str, tuple[int, int]] = {
    "ARRIBA": (0, 1),
    "ABAJO": (0, -1),
    "IZQUIERDA": (-1, 0),
    "DERECHA": (1, 0),
}

Posicion = tuple[int, int]


@dataclass(frozen=True)
class Laberinto:
    """Representación inmutable de un escenario 10x10 del juego."""

    nombre: str
    obstaculos: frozenset[Posicion]
    inicio_jugador: Posicion
    inicio_agente: Posicion
    salida: Posicion
    ancho: int = ANCHO
    alto: int = ALTO

    def en_limites(self, pos: Posicion) -> bool:
        x, y = pos
        return 1 <= x <= self.ancho and 1 <= y <= self.alto

    def es_transitable(self, pos: Posicion) -> bool:
        return self.en_limites(pos) and pos not in self.obstaculos

    def vecinos(self, pos: Posicion) -> list[tuple[str, Posicion]]:
        """Devuelve pares (accion, nueva_pos) transitables desde pos."""
        x, y = pos
        resultado: list[tuple[str, Posicion]] = []
        for accion, (dx, dy) in ACCIONES.items():
            siguiente = (x + dx, y + dy)
            if self.es_transitable(siguiente):
                resultado.append((accion, siguiente))
        return resultado


def distancia_manhattan(a: Posicion, b: Posicion) -> int:
    """Heurística Manhattan requerida en el Nivel 1 y útil en el Nivel 2."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def cargar_laberinto_desde_texto(texto: str, nombre: str = "Nivel") -> Laberinto:
    """
    Convierte una cuadrícula de texto de 10x10 a un objeto Laberinto.
    La primera línea del texto corresponde a y = 10 y la última a y = 1.
    """
    lineas = [linea.strip() for linea in texto.strip().splitlines() if linea.strip()]
    if len(lineas) != ALTO:
        raise ValueError(f"{nombre}: se esperaban {ALTO} filas y se encontraron {len(lineas)}.")

    obstaculos: set[Posicion] = set()
    inicio_jugador: Posicion | None = None
    inicio_agente: Posicion | None = None
    salida: Posicion | None = None

    for fila_idx, linea in enumerate(lineas):
        if len(linea) != ANCHO:
            raise ValueError(
                f"{nombre}: la fila {fila_idx + 1} tiene {len(linea)} columnas (deben ser {ANCHO})."
            )
        y = ALTO - fila_idx  # fila 0 -> y=10 (arriba), fila 9 -> y=1 (abajo)
        for col_idx, simbolo in enumerate(linea):
            if simbolo not in SIMBOLOS_VALIDOS:
                raise ValueError(f"{nombre}: símbolo inválido '{simbolo}' en fila {fila_idx + 1}.")
            x = col_idx + 1  # col 0 -> x=1 (izquierda), col 9 -> x=10 (derecha)
            pos = (x, y)

            if simbolo == SIMBOLO_OBSTACULO:
                obstaculos.add(pos)
            elif simbolo == SIMBOLO_JUGADOR:
                if inicio_jugador is not None:
                    raise ValueError(f"{nombre}: hay más de un jugador 'P'.")
                inicio_jugador = pos
            elif simbolo == SIMBOLO_AGENTE:
                if inicio_agente is not None:
                    raise ValueError(f"{nombre}: hay más de un agente 'G'.")
                inicio_agente = pos
            elif simbolo == SIMBOLO_SALIDA:
                if salida is not None:
                    raise ValueError(f"{nombre}: hay más de una salida 'E'.")
                salida = pos

    if inicio_jugador != (1, 1):
        raise ValueError(f"{nombre}: el jugador 'P' debe iniciar en (1, 1), encontrado en {inicio_jugador}.")
    if salida != (10, 10):
        raise ValueError(f"{nombre}: la salida 'E' debe estar en (10, 10), encontrada en {salida}.")
    if inicio_agente is None:
        raise ValueError(f"{nombre}: no se encontró la posición inicial del agente 'G'.")

    return Laberinto(
        nombre=nombre,
        obstaculos=frozenset(obstaculos),
        inicio_jugador=inicio_jugador,
        inicio_agente=inicio_agente,
        salida=salida,
    )


def cargar_laberinto_desde_archivo(ruta: str | Path, nombre: str | None = None) -> Laberinto:
    path = Path(ruta)
    contenido = path.read_text(encoding="utf-8")
    return cargar_laberinto_desde_texto(contenido, nombre=nombre or path.stem)