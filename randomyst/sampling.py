"""Exact bucket enumeration and product-weight subset sampling for the MVP runtime.

The selected law P(B | hard rules) is proportional to product(w[n] for n in B).
It is deliberately distinct from sequential weighted draws with removal.
"""

from bisect import bisect_left
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from math import exp, fsum, isfinite, prod
from random import Random

ELEMENTS = ("Mộc", "Hỏa", "Thổ", "Kim", "Thủy")
GENERATES = dict(zip(ELEMENTS, ELEMENTS[1:] + ELEMENTS[:1]))
CONTROLS = dict(zip(ELEMENTS, ("Thổ", "Kim", "Thủy", "Mộc", "Hỏa")))
BUCKETS = tuple((element, parity) for element in ELEMENTS for parity in (0, 1))
THRESHOLDS = {"DAI_CAT": 80, "THU_CAT": 80, "BINH_HOA": 80, "TIEU_HAO": 80, "DAI_HUNG": 85}
DEFAULT_POOL = tuple(range(100))


def element_of(number):
    return ELEMENTS[((number % 10 - 1) % 10) // 2]


def relation_score(element, target):
    if element == target:
        return 80
    if GENERATES[element] == target:
        return 100
    if GENERATES[target] == element:
        return 30
    if CONTROLS[target] == element:
        return 0
    if CONTROLS[element] == target:
        return -100
    raise ValueError("Unknown element relation")


def state_of(the, dung):
    if the == dung:
        return "BINH_HOA"
    if GENERATES[dung] == the:
        return "DAI_CAT"
    if CONTROLS[the] == dung:
        return "THU_CAT"
    if GENERATES[the] == dung:
        return "TIEU_HAO"
    return "DAI_HUNG"


@dataclass(frozen=True)
class Context:
    primary: str
    the: str
    dung: str
    remedy: str | None = None
    strategy: str = "NONE"

    @property
    def state(self):
        return state_of(self.the, self.dung)

    @property
    def threshold(self):
        return THRESHOLDS[self.state]

    def allowed(self, element, retry=False):
        if self.state != "DAI_HUNG":
            return True
        return CONTROLS[element] != self.primary and (not retry or CONTROLS[element] != self.the)


@dataclass(frozen=True)
class Configuration:
    counts: tuple[int, ...]
    raw_units: int  # six times G_raw; includes -90 for each conflicting number
    conflicts: int
    even_count: int

    @property
    def yin_yang(self):
        return {1: 8, 2: 70, 3: 100, 4: 70, 5: 8}[self.even_count]

    def score_numerator(self, cap_units):
        return 2 * self.yin_yang * cap_units + 300 * max(0, min(self.raw_units, cap_units))

    def score(self, cap_units):
        return self.score_numerator(cap_units) / (5 * cap_units)

    def meets(self, cap_units, threshold):
        return self.score_numerator(cap_units) >= threshold * 5 * cap_units


@lru_cache(maxsize=None)
def count_vectors(capacities, total=6):
    """Capacity-aware compositions of six; at most 5,005 vectors for ten buckets."""
    result = []

    def visit(index, remaining, prefix):
        if index == len(capacities):
            if remaining == 0:
                result.append(tuple(prefix))
            return
        for count in range(min(capacities[index], remaining) + 1):
            visit(index + 1, remaining - count, prefix + [count])

    visit(0, total, [])
    return tuple(result)


def grouped_pool(pool):
    return tuple(tuple(n for n in pool if element_of(n) == e and n % 2 == p) for e, p in BUCKETS)


@lru_cache(maxsize=None)
def configurations(context, pool=DEFAULT_POOL, retry=False, quota_max=4):
    groups = grouped_pool(pool)
    capacities = tuple(len(group) if context.allowed(e, retry) else 0 for group, (e, _) in zip(groups, BUCKETS))
    scores = {e: relation_score(e, context.primary) + relation_score(e, context.the) for e in ELEMENTS}
    conflict = {e: relation_score(e, context.primary) == -100 or relation_score(e, context.the) == -100 for e in ELEMENTS}
    output = []
    for counts in count_vectors(capacities):
        even_count = sum(counts[::2])
        if even_count in (0, 6) or (retry and even_count != 3):
            continue
        totals = tuple(counts[i] + counts[i + 1] for i in range(0, 10, 2))
        if max(totals) == 6:
            continue
        if context.state == "DAI_HUNG":
            if context.remedy is None:
                raise ValueError("Hung context must have a selected remedy")
            if not 3 <= totals[ELEMENTS.index(context.remedy)] <= quota_max:
                continue
        conflicts = sum(count * conflict[e] for count, e in zip(totals, ELEMENTS))
        raw_units = sum(count * scores[e] for count, e in zip(totals, ELEMENTS)) - 90 * conflicts
        output.append(Configuration(counts, raw_units, conflicts, even_count))
    return tuple(output)


def select_context(primary, the, dung, pool=DEFAULT_POOL, quota_max=4):
    base = Context(primary, the, dung)
    if base.state != "DAI_HUNG":
        return base, []
    ideal = GENERATES[the] == primary and CONTROLS[primary] == dung
    candidates = (primary,) if ideal else tuple(e for e in ELEMENTS if (GENERATES[e] == the or CONTROLS[e] == dung) and CONTROLS[e] != primary)
    audited = []
    contexts = []
    for remedy in candidates:
        context = Context(primary, the, dung, remedy, "IDEAL_CHAIN" if ideal else "SAFE_REMEDIATION")
        configs = configurations(context, pool, quota_max=quota_max)
        if not configs:
            audited.append({"remedy": remedy, "feasible": False})
            continue
        best = max(configs, key=lambda c: (c.raw_units, -c.conflicts))
        single_score = relation_score(remedy, primary) + relation_score(remedy, the)
        audited.append({"remedy": remedy, "feasible": True, "best_raw": best.raw_units / 6, "conflicts_at_best": best.conflicts, "single_element_score": single_score})
        # Versioned deterministic tie-break: raw score, conflicts, target score, element order.
        contexts.append(((best.raw_units, -best.conflicts, single_score, -ELEMENTS.index(remedy)), context))
    if not contexts:
        raise ValueError("No feasible remedy under the declared constraints")
    return max(contexts, key=lambda row: row[0])[1], audited


def elementary_symmetric(weights, max_count=6):
    values = [1.0] + [0.0] * max_count
    for weight in weights:
        for count in range(max_count, 0, -1):
            values[count] += weight * values[count - 1]
    return tuple(values)


class ProductSubsetSampler:
    """Fixed-size weighted subsets via suffix elementary-symmetric polynomials."""

    def __init__(self, numbers, weights):
        if len(numbers) != len(weights) or len(set(numbers)) != len(numbers):
            raise ValueError("Distinct numbers and aligned weights are required")
        if any(not isfinite(w) or w <= 0 for w in weights):
            raise ValueError("Weights must be finite and positive")
        self.numbers, self.weights = tuple(numbers), tuple(weights)
        self.suffix = [(1.0,) + (0.0,) * 6 for _ in range(len(numbers) + 1)]
        for index in range(len(numbers) - 1, -1, -1):
            remaining = self.suffix[index + 1]
            self.suffix[index] = (1.0,) + tuple(remaining[k] + weights[index] * remaining[k - 1] for k in range(1, 7))

    def sample(self, count, rng):
        if not 0 <= count <= min(6, len(self.numbers)):
            raise ValueError("Subset count outside supported range")
        chosen = []
        for index, number in enumerate(self.numbers):
            if count == 0:
                break
            probability = self.weights[index] * self.suffix[index + 1][count - 1] / self.suffix[index][count]
            if rng.random() < probability:
                chosen.append(number)
                count -= 1
        if count:
            raise RuntimeError("Sampling invariant failed")
        return chosen


class Distribution:
    def __init__(self, configs, weights, pool=DEFAULT_POOL):
        self.configs = tuple(configs)
        groups = grouped_pool(pool)
        self.samplers = []
        polynomials = []
        for group in groups:
            eligible = tuple(n for n in group if n in weights)
            sampler = ProductSubsetSampler(eligible, [weights[n] for n in eligible])
            self.samplers.append(sampler)
            polynomials.append(sampler.suffix[0])
        self.masses = tuple(prod(polynomials[i][count] for i, count in enumerate(c.counts)) for c in configs)
        self.partition = fsum(self.masses)
        if not isfinite(self.partition) or self.partition <= 0:
            raise ValueError("No positive finite mass in feasible configurations")
        self.cdf = []
        cumulative = 0.0
        for mass in self.masses:
            cumulative += mass
            self.cdf.append(cumulative)
        self.sampling_total = cumulative

    def sample(self, rng):
        index = min(bisect_left(self.cdf, rng.random() * self.sampling_total), len(self.configs) - 1)
        config = self.configs[index]
        numbers = []
        for sampler, count in zip(self.samplers, config.counts):
            numbers.extend(sampler.sample(count, rng))
        return tuple(sorted(numbers)), config

    def exact_metrics(self, cap_units, threshold):
        means = [0.0] * 5
        parity = {str(i): 0.0 for i in range(1, 6)}
        mode_rate = score75_rate = mean_score = 0.0
        for config, mass in zip(self.configs, self.masses):
            probability = mass / self.partition
            mode_rate += probability * config.meets(cap_units, threshold)
            score75_rate += probability * config.meets(cap_units, 75)
            mean_score += probability * config.score(cap_units)
            parity[str(config.even_count)] += probability
            for i in range(5):
                means[i] += probability * (config.counts[2 * i] + config.counts[2 * i + 1])
        return {"mode_acceptance_rate": mode_rate, "score_ge_75_rate": score75_rate, "mean_score": mean_score,
                "expected_element_counts": dict(zip(ELEMENTS, means)), "even_count_probabilities": parity}


def validate_sample(numbers, context, quota_max=4, retry=False, pool=DEFAULT_POOL):
    if len(numbers) != 6 or len(set(numbers)) != 6 or any(n not in pool for n in numbers):
        return False
    elements = [element_of(n) for n in numbers]
    if len(set(elements)) == 1 or sum(n % 2 == 0 for n in numbers) in (0, 6):
        return False
    if retry and sum(n % 2 == 0 for n in numbers) != 3:
        return False
    if context.state == "DAI_HUNG":
        if not 3 <= elements.count(context.remedy) <= quota_max:
            return False
        if any(not context.allowed(e, retry) for e in elements):
            return False
    return True
