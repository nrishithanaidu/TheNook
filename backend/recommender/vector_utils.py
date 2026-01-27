import math
from typing import List, Tuple


Vector = Tuple[float, float]


def euclidean_distance(v1: Vector, v2: Vector) -> float:
    

    return math.sqrt(
        (v1[0] - v2[0]) ** 2 +
        (v1[1] - v2[1]) ** 2
    )


def average_vectors(vectors: List[Vector]) -> Vector:
    

    if not vectors:
        return (0.0, 0.0)

    x = sum(v[0] for v in vectors) / len(vectors)
    y = sum(v[1] for v in vectors) / len(vectors)

    return (round(x, 3), round(y, 3))


def normalize_vector(vector: Vector) -> Vector:
    
    magnitude = math.sqrt(vector[0] ** 2 + vector[1] ** 2)

    if magnitude == 0:
        return (0.0, 0.0)

    return (
        round(vector[0] / magnitude, 3),
        round(vector[1] / magnitude, 3)
    )
