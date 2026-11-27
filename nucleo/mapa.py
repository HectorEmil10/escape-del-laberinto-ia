from dataclasses import dataclass
from pathlib import Path

ANCHO = 10
ALTO = 10

SIMBOLO_JUGADOR = "P"
SIMBOLO_AGENTE = "G"
SIMBOLO_SALIDA = "E"
SIMBOLO_OBSTACULO = "#"
SIMBOLO_LIBRE = "."

ACCIONES: dict[str, tuple[int, int]] = {
    "ARRIBA": (0, 1),
    "ABAJO": (0, -1),
    "IZQUIERDA": (-1, 0),
    "DERECHA": (1, 0),
}

Posicion = tuple[int, int]


@dataclass(frozen=True)
class Laberinto:
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
        x, y = pos
        adyacentes: list[tuple[str, Posicion]] = []
        for accion, (dx, dy) in ACCIONES.items():
            candidata = (x + dx, y + dy)
            if self.es_transitable(candidata):
                adyacentes.append((accion, candidata))
        return adyacentes


def distancia_manhattan(a: Posicion, b: Posicion) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def cargar_laberinto_desde_archivo(ruta: str | Path, nombre: str | None = None) -> Laberinto:
    archivo = Path(ruta)
    contenido = archivo.read_text(encoding="utf-8")
    return cargar_laberinto_desde_texto(contenido, nombre=nombre or archivo.stem)


def cargar_laberinto_desde_texto(texto: str, nombre: str = "Nivel") -> Laberinto:
    filas = [fila.strip() for fila in texto.strip().splitlines() if fila.strip()]
    if len(filas) != ALTO:
        raise ValueError(f"{nombre}: se esperaban {ALTO} filas y hay {len(filas)}.")

    obstaculos: set[Posicion] = set()
    inicio_jugador: Posicion | None = None
    inicio_agente: Posicion | None = None
    salida: Posicion | None = None

    # La primera línea del texto está arriba (y=10) y la última abajo (y=1).
    for idx_fila, fila in enumerate(filas):
        if len(fila) != ANCHO:
            raise ValueError(f"{nombre}: la fila {idx_fila + 1} no tiene {ANCHO} columnas.")
        y = ALTO - idx_fila
        for idx_col, celda in enumerate(fila):
            pos = (idx_col + 1, y)
            if celda == SIMBOLO_OBSTACULO:
                obstaculos.add(pos)
            elif celda == SIMBOLO_JUGADOR:
                inicio_jugador = pos
            elif celda == SIMBOLO_AGENTE:
                inicio_agente = pos
            elif celda == SIMBOLO_SALIDA:
                salida = pos

    if inicio_jugador is None or inicio_agente is None or salida is None:
        raise ValueError(f"{nombre}: faltan elementos obligatorios ('P', 'G' o 'E').")

    return Laberinto(
        nombre=nombre,
        obstaculos=frozenset(obstaculos),
        inicio_jugador=inicio_jugador,
        inicio_agente=inicio_agente,
        salida=salida,
    )