from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from fitness import FitnessResult, Student, evaluate_fitness


@dataclass
class GAConfig:
    population_size: int = 80
    generations: int = 100
    tournament_k: int = 3
    mutation_rate: float = 0.05
    elitism: int = 2


def _tournament_select(
    population: Sequence[List[int]],
    fitnesses: Sequence[FitnessResult],
    k: int,
) -> List[int]:
    """
    Tournament selection (MANDATORY).
    Randomly sample k individuals and return the best (highest fitness).
    """
    n = len(population)
    best_i = None
    for _ in range(k):
        i = random.randrange(n)
        if best_i is None or fitnesses[i].fitness > fitnesses[best_i].fitness:
            best_i = i
    return population[best_i].copy()  # safe copy


def _single_point_order_crossover(p1: Sequence[int], p2: Sequence[int]) -> Tuple[List[int], List[int]]:
    """
    Single-point crossover (MANDATORY) adapted for permutations:
      - Pick a cut point
      - Child takes prefix from parent A
      - Remaining positions are filled from parent B in order (skipping duplicates)

    This keeps "single point" behavior while ensuring each student appears once.
    """
    if len(p1) != len(p2):
        raise ValueError("Parents must have same chromosome length.")
    n = len(p1)
    if n < 2:
        return list(p1), list(p2)

    cut = random.randint(1, n - 1)

    def build_child(a: Sequence[int], b: Sequence[int]) -> List[int]:
        prefix = list(a[:cut])
        used = set(prefix)
        rest = [g for g in b if g not in used]
        return prefix + rest

    return build_child(p1, p2), build_child(p2, p1)


def _mutate_swap(chromosome: List[int], mutation_rate: float) -> None:
    """
    Mutation (MANDATORY): randomly swap two genes.
    """
    if random.random() > mutation_rate or len(chromosome) < 2:
        return
    i, j = random.sample(range(len(chromosome)), 2)
    chromosome[i], chromosome[j] = chromosome[j], chromosome[i]


def optimize_seating_ga(
    students: Sequence[Student],
    rows: int,
    cols: int,
    config: GAConfig,
) -> Dict[str, object]:
    """
    Evolution process (MANDATORY):
      1) Initialize population
      2) Evaluate fitness
      3) Tournament selection
      4) Single-point crossover
      5) Swap mutation (~5%)
      6) Replace worst individuals (done via generational replacement + elitism)
      7) Repeat for N generations

    Returns best chromosome + fitness history for visualization.
    """
    student_count = len(students)
    if student_count == 0:
        raise ValueError("No students provided.")
    if rows * cols < student_count:
        raise ValueError("Not enough seats for all students.")

    # Population initialization (MANDATORY): random permutations of all students.
    base = list(range(student_count))
    population: List[List[int]] = []
    for _ in range(config.population_size):
        chrom = base.copy()
        random.shuffle(chrom)
        population.append(chrom)

    history_best: List[float] = []
    history_avg: List[float] = []

    def eval_all(pop: Sequence[List[int]]) -> List[FitnessResult]:
        return [evaluate_fitness(ch, students, rows, cols) for ch in pop]

    for _gen in range(config.generations):
        fitnesses = eval_all(population)
        avg_fit = sum(fr.fitness for fr in fitnesses) / len(fitnesses)
        best_i = max(range(len(population)), key=lambda i: fitnesses[i].fitness)

        history_best.append(fitnesses[best_i].fitness)
        history_avg.append(avg_fit)

        # Elitism: carry over top N unchanged
        elite_indices = sorted(range(len(population)), key=lambda i: fitnesses[i].fitness, reverse=True)[
            : config.elitism
        ]
        next_pop: List[List[int]] = [population[i].copy() for i in elite_indices]

        # Fill the rest of next generation
        while len(next_pop) < config.population_size:
            p1 = _tournament_select(population, fitnesses, config.tournament_k)
            p2 = _tournament_select(population, fitnesses, config.tournament_k)
            c1, c2 = _single_point_order_crossover(p1, p2)
            _mutate_swap(c1, config.mutation_rate)
            _mutate_swap(c2, config.mutation_rate)
            next_pop.append(c1)
            if len(next_pop) < config.population_size:
                next_pop.append(c2)

        population = next_pop

    # Final evaluation
    final_fitnesses = eval_all(population)
    best_i = max(range(len(population)), key=lambda i: final_fitnesses[i].fitness)
    best = population[best_i]
    best_fit = final_fitnesses[best_i]

    return {
        "best_chromosome": best,
        "best_fitness": best_fit.fitness,
        "best_clash_count": best_fit.clash_count,
        "history_best": history_best,
        "history_avg": history_avg,
        "population_size": config.population_size,
        "generations": config.generations,
    }

