from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class Student:
    """
    Student record used by the GA.

    Chromosome representation (MANDATORY):
      - A chromosome is an ordered list of Student indices.
      - Each index maps to a seat number in row-major order.
    """

    student_id: str
    name: str
    subject: str


@dataclass
class FitnessResult:
    fitness: float
    clash_count: int
    clash_seats: Set[int]
    duplicate_penalty: int
    adjacency_penalty: int


def _seat_index(r: int, c: int, cols: int) -> int:
    return r * cols + c


def build_seating_grid(
    chromosome: Sequence[int],
    students: Sequence[Student],
    rows: int,
    cols: int,
) -> List[List[Optional[Student]]]:
    """
    Map the chromosome (ordered indices) into a rows x cols grid.
    Empty seats (if seats > students) are None.
    """
    grid: List[List[Optional[Student]]] = [[None for _ in range(cols)] for _ in range(rows)]
    for seat_i in range(rows * cols):
        if seat_i >= len(chromosome):
            break
        idx = chromosome[seat_i]
        r, c = divmod(seat_i, cols)
        if 0 <= idx < len(students):
            grid[r][c] = students[idx]
        else:
            grid[r][c] = None
    return grid


def compute_clashes(
    grid: Sequence[Sequence[Optional[Student]]],
) -> Tuple[int, int, Set[Tuple[int, int]]]:
    """
    Clash definition (MANDATORY):
      - Same subject adjacent horizontally -> penalty
      - Same subject adjacent vertically -> penalty

    Returns:
      - clash_count: number of adjacent same-subject edges
      - adjacent_pairs: number of any adjacent student pairs
      - clash_cells: set of (r, c) cells involved in at least one clash
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    clash_cells: Set[Tuple[int, int]] = set()
    clashes = 0
    adjacent_pairs = 0

    for r in range(rows):
        for c in range(cols):
            s = grid[r][c]
            if s is None:
                continue

            # right neighbor
            if c + 1 < cols and grid[r][c + 1] is not None:
                adjacent_pairs += 1
                if grid[r][c + 1].subject == s.subject:
                    clashes += 1
                    clash_cells.add((r, c))
                    clash_cells.add((r, c + 1))

            # bottom neighbor
            if r + 1 < rows and grid[r + 1][c] is not None:
                adjacent_pairs += 1
                if grid[r + 1][c].subject == s.subject:
                    clashes += 1
                    clash_cells.add((r, c))
                    clash_cells.add((r + 1, c))

    return clashes, adjacent_pairs, clash_cells


def evaluate_fitness(
    chromosome: Sequence[int],
    students: Sequence[Student],
    rows: int,
    cols: int,
) -> FitnessResult:
    """
    Fitness function (MANDATORY):
      - Duplicate student assignment -> heavy penalty
      - Same subject adjacency -> penalty
      - Higher fitness is better

    We follow the spec shape:
      Fitness = TotalSeats - ClashPenalty
    and add a heavy duplicate penalty on top.
    """
    total_seats = rows * cols

    # Duplicate student assignment penalty (heavy).
    seen: Set[int] = set()
    dupes = 0
    for idx in chromosome:
        if idx in seen:
            dupes += 1
        seen.add(idx)
    duplicate_penalty = dupes * (10 * total_seats)

    grid = build_seating_grid(chromosome, students, rows, cols)
    clash_count, adjacent_pairs, clash_cells = compute_clashes(grid)

    empty_seats = total_seats - len(students)
    gap_penalty = adjacent_pairs * 2 if empty_seats > 0 else 0

    adjacency_penalty = (clash_count * 10) + gap_penalty
    clash_penalty = adjacency_penalty + duplicate_penalty

    fitness = float((total_seats * 15) - clash_penalty)

    clash_seats: Set[int] = set()
    for (r, c) in clash_cells:
        clash_seats.add(_seat_index(r, c, cols))

    return FitnessResult(
        fitness=fitness,
        clash_count=clash_count,
        clash_seats=clash_seats,
        duplicate_penalty=duplicate_penalty,
        adjacency_penalty=adjacency_penalty,
    )


def subject_color_class(subject: str) -> str:
    """
    Deterministic Tailwind color choice per subject.
    """
    palette = [
        "bg-blue-500",
        "bg-purple-500",
        "bg-emerald-500",
        "bg-amber-500",
        "bg-pink-500",
        "bg-cyan-500",
        "bg-indigo-500",
        "bg-teal-500",
        "bg-rose-500",
        "bg-lime-500",
    ]
    i = abs(hash(subject)) % len(palette)
    return palette[i]


def to_seat_cards(
    chromosome: Sequence[int],
    students: Sequence[Student],
    rows: int,
    cols: int,
) -> Dict[str, object]:
    """
    Prepare UI-friendly data:
      - seat_cards: list of seat dicts (row-major length rows*cols)
      - clash_seats: set of seat indices (row-major) to highlight red borders
      - clash_count and fitness
    """
    total_seats = rows * cols
    result = evaluate_fitness(chromosome, students, rows, cols)
    grid = build_seating_grid(chromosome, students, rows, cols)

    seat_cards: List[Dict[str, object]] = []
    for seat_i in range(total_seats):
        r, c = divmod(seat_i, cols)
        s = grid[r][c]
        if s is None:
            seat_cards.append(
                {
                    "empty": True,
                    "seat_index": seat_i,
                }
            )
        else:
            seat_cards.append(
                {
                    "empty": False,
                    "seat_index": seat_i,
                    "student_id": s.student_id,
                    "name": s.name,
                    "subject": s.subject,
                    "subject_color": subject_color_class(s.subject),
                    "is_clash": seat_i in result.clash_seats,
                }
            )

    return {
        "seat_cards": seat_cards,
        "clash_seats": sorted(list(result.clash_seats)),
        "clash_count": result.clash_count,
        "fitness": result.fitness,
    }

