"""Verify the research optimizer/sampler against independent small-pool sums."""

import unittest
from collections import Counter
from itertools import combinations
from math import exp, prod
from random import Random

from research_tools.weighted_sampling import (
    ELEMENTS, Context, Distribution, ProductSubsetSampler, configurations,
    element_of, relation_score, select_context, validate_sample, weights_for,
)


class WeightedSamplingTest(unittest.TestCase):
    def test_direction_of_relation_and_zero_tail(self):
        self.assertEqual(element_of(0), "Thủy")
        self.assertEqual(relation_score("Mộc", "Kim"), 0)
        self.assertEqual(relation_score("Kim", "Mộc"), -100)

    def test_optimizer_matches_bruteforce_small_pool(self):
        pool = tuple(range(16))
        context, _ = select_context("Mộc", "Mộc", "Kim", pool)
        raw_values = []
        for numbers in combinations(pool, 6):
            if validate_sample(numbers, context, pool=pool):
                scores = [relation_score(element_of(n), context.primary) + relation_score(element_of(n), context.the) for n in numbers]
                conflicts = sum(relation_score(element_of(n), context.primary) == -100 or relation_score(element_of(n), context.the) == -100 for n in numbers)
                raw_values.append(sum(scores) - 90 * conflicts)
        self.assertEqual(max(raw_values), max(c.raw_units for c in configurations(context, pool)))

    def test_exact_partition_and_pass_rate_match_bruteforce(self):
        pool = tuple(range(12))
        context = Context("Mộc", "Kim", "Kim")
        weights = weights_for(context, 1.0, {9, 11}, "ILLUSTRATIVE_LOCKED_BONUSES", pool)
        configs = configurations(context, pool)
        cap = max(c.raw_units for c in configs)
        dist = Distribution(configs, weights, pool)
        mass = passing_mass = 0.0
        for numbers in combinations(pool, 6):
            if not validate_sample(numbers, context, pool=pool):
                continue
            weight = prod(weights[n] for n in numbers)
            raw = sum(relation_score(element_of(n), context.primary) + relation_score(element_of(n), context.the) for n in numbers)
            raw -= 90 * sum(relation_score(element_of(n), context.primary) == -100 or relation_score(element_of(n), context.the) == -100 for n in numbers)
            even = sum(n % 2 == 0 for n in numbers)
            yin_yang = {1: 8, 2: 70, 3: 100, 4: 70, 5: 8}[even]
            score = 0.4 * yin_yang + 60 * max(0, min(raw, cap)) / cap
            mass += weight
            passing_mass += weight * (score >= context.threshold)
        self.assertAlmostEqual(dist.partition, mass, places=10)
        self.assertAlmostEqual(dist.exact_metrics(cap, context.threshold)["mode_acceptance_rate"], passing_mass / mass, places=12)

    def test_product_subset_probabilities(self):
        sampler = ProductSubsetSampler((1, 2, 3), (1.0, 2.0, 3.0))
        rng = Random(924)
        counts = Counter(tuple(sampler.sample(2, rng)) for _ in range(12000))
        for subset, probability in {(1, 2): 2 / 11, (1, 3): 3 / 11, (2, 3): 6 / 11}.items():
            self.assertAlmostEqual(counts[subset] / 12000, probability, delta=0.015)

    def test_weight_ratio_matches_exponent_and_remediation(self):
        context, _ = select_context("Mộc", "Mộc", "Kim")
        weights = weights_for(context, 2, set(), "BASE_NO_AUXILIARY_BONUSES")
        self.assertNotIn(7, weights)  # Kim controls primary Wood, banned from attempt one.
        self.assertAlmostEqual(weights[9] / weights[1], 3 * exp(2 * (200 - 160) / 100))

    def test_quota_four_and_frozen_cap_on_all_hung_cases(self):
        cases = 0
        for primary in ELEMENTS:
            for the in ELEMENTS:
                for dung in ELEMENTS:
                    context, _ = select_context(primary, the, dung)
                    if context.state != "DAI_HUNG":
                        continue
                    first = configurations(context)
                    retry = configurations(context, retry=True)
                    cap = max(c.raw_units for c in first)
                    self.assertGreater(cap, 0)
                    self.assertEqual(cap, max(c.raw_units for c in retry))
                    self.assertTrue(any(c.meets(cap, 85) for c in retry))
                    target = ELEMENTS.index(context.remedy) * 2
                    self.assertTrue(all(3 <= c.counts[target] + c.counts[target + 1] <= 4 for c in first))
                    cases += 1
        self.assertEqual(cases, 25)


if __name__ == "__main__":
    unittest.main()
