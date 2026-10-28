"""Compare beta parameters with exact probabilities plus reproducible sampling.

Run: python3 -m research_tools.exponential_audit --output-dir docs/research
Profiles are synthetic; their probabilities are not observed product KPIs.
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from math import fsum, isfinite
from pathlib import Path
from random import Random

from .weighted_sampling import (
    ELEMENTS, Context, Distribution, all_contexts, configurations, select_context,
    validate_sample, weights_for,
)

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "config/mvp1_rules.json"
FOLK_PATH = ROOT / "dan_gian_config.json"
PROFILES = ("BASE_NO_AUXILIARY_BONUSES", "ILLUSTRATIVE_LOCKED_BONUSES")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def average_metrics(rows):
    count = len(rows)
    result = {key: fsum(row[key] for row in rows) / count for key in ("mode_acceptance_rate", "score_ge_75_rate", "mean_score")}
    result["expected_element_counts"] = {e: fsum(row["expected_element_counts"][e] for row in rows) / count for e in ELEMENTS}
    result["even_count_probabilities"] = {str(i): fsum(row["even_count_probabilities"][str(i)] for row in rows) / count for i in range(1, 6)}
    return result


def feasibility_report(quota_max):
    hung_rows, non_hung_pairs = [], []
    for context in all_contexts(quota_max=quota_max):
        if context.state != "DAI_HUNG":
            continue
        first = configurations(context, quota_max=quota_max)
        retry = configurations(context, retry=True, quota_max=quota_max)
        cap_units = max(c.raw_units for c in first)
        retry_units = max((c.raw_units for c in retry), default=None)
        old_context, _ = select_context(context.primary, context.the, context.dung, quota_max=5)
        old_cap = max(c.raw_units for c in configurations(old_context, quota_max=5)) / 6
        _, candidates = select_context(context.primary, context.the, context.dung, quota_max=quota_max)
        best = max(first, key=lambda c: (c.raw_units, -c.conflicts))
        hung_rows.append({
            "P": context.primary, "The": context.the, "Dung": context.dung, "strategy": context.strategy,
            "selected_remedy": context.remedy, "candidates": candidates,
            "G_cap_first_attempt": cap_units / 6, "max_raw_retry": retry_units / 6 if retry_units is not None else None,
            "cap_attainable_in_retry": cap_units == retry_units,
            "threshold": context.threshold,
            "retry_has_threshold_passing_configuration": any(c.meets(cap_units, context.threshold) for c in retry),
            "best_first_element_counts": {e: best.counts[2 * i] + best.counts[2 * i + 1] for i, e in enumerate(ELEMENTS)},
            "quota_3_to_5_comparison": {"remedy": old_context.remedy, "G_cap": old_cap,
                                       "cap_changed": old_cap != cap_units / 6,
                                       "remedy_changed": old_context.remedy != context.remedy},
        })
    for primary in ELEMENTS:
        for the in ELEMENTS:
            # Same pool/score/hard rules for all non-Hung Dung choices at P/The.
            dung = the
            context = Context(primary, the, dung)
            cap_units = max(c.raw_units for c in configurations(context, quota_max=quota_max))
            retry = configurations(context, retry=True, quota_max=quota_max)
            non_hung_pairs.append({"P": primary, "The": the, "G_cap": cap_units / 6,
                                   "cap_attainable_with_3_even_3_odd": any(c.raw_units == cap_units for c in retry)})
    return {
        "scope": "Finite mathematical feasibility under confirmed base scoring, quota 3..4, pool 00..99; not calendar or product KPI validation.",
        "pool": {"min": 0, "max": 99, "size": 100},
        "quota": {"min": 3, "max": quota_max}, "hung_contexts": len(hung_rows),
        "all_hung_have_passing_retry": all(row["retry_has_threshold_passing_configuration"] for row in hung_rows),
        "all_hung_caps_remain_attainable_in_retry": all(row["cap_attainable_in_retry"] for row in hung_rows),
        "minimum_G_cap": min(row["G_cap_first_attempt"] for row in hung_rows),
        "maximum_G_cap": max(row["G_cap_first_attempt"] for row in hung_rows),
        "caps_changed_from_quota_3_to_5": sum(row["quota_3_to_5_comparison"]["cap_changed"] for row in hung_rows),
        "selected_remedies_changed_from_quota_3_to_5": sum(row["quota_3_to_5_comparison"]["remedy_changed"] for row in hung_rows),
        "tie_break_used_in_experiment": "Same deterministic order as runtime: highest feasible raw score; fewer conflicts at that maximum; higher remedy S_i; fixed element order.",
        "rows": hung_rows, "non_hung_target_pairs": non_hung_pairs,
    }


def run(betas, samples_per_context, seed, quota_max, folk_numbers):
    contexts = all_contexts(quota_max=quota_max)
    output = []
    sampled_total = retry_total = invalid = 0
    for profile in PROFILES:
        for beta in betas:
            rng = Random(f"{seed}|{profile}|{beta}")
            context_rows = []
            groups = defaultdict(list)
            sample_stats = Counter()
            mode_counts = Counter(c.state for c in contexts)
            for context in contexts:
                first = configurations(context, quota_max=quota_max)
                cap_units = max(c.raw_units for c in first)
                if cap_units <= 0:
                    raise ValueError("Nonpositive normalization cap")
                weights = weights_for(context, beta, folk_numbers, profile)
                dist = Distribution(first, weights)
                metrics = dist.exact_metrics(cap_units, context.threshold)
                context_rows.append({"P": context.primary, "The": context.the, "Dung": context.dung,
                                     "state": context.state, "remedy": context.remedy, "G_cap": cap_units / 6,
                                     **metrics})
                groups[context.state].append(metrics)
                retry = tuple(c for c in configurations(context, retry=True, quota_max=quota_max) if c.meets(cap_units, context.threshold))
                retry_dist = Distribution(retry, weights) if retry else None
                seen = set()
                for _ in range(samples_per_context):
                    numbers, config = dist.sample(rng)
                    sampled_total += 1
                    sample_stats["first_draws"] += 1
                    ok = validate_sample(numbers, context, quota_max=quota_max)
                    invalid += not ok
                    if not ok:
                        raise RuntimeError(f"Invalid first sample: {context}, {numbers}")
                    sample_stats["first_mode_passes"] += config.meets(cap_units, context.threshold)
                    sample_stats["first_score_ge_75"] += config.meets(cap_units, 75)
                    sample_stats["repeated_first_sets_within_context"] += numbers in seen
                    seen.add(numbers)
                    if not config.meets(cap_units, context.threshold) and retry_dist:
                        retry_numbers, retry_config = retry_dist.sample(rng)
                        retry_total += 1
                        sample_stats["conditional_retries_sampled"] += 1
                        ok = validate_sample(retry_numbers, context, quota_max=quota_max, retry=True)
                        invalid += not ok or not retry_config.meets(cap_units, context.threshold)
                        if not ok or not retry_config.meets(cap_units, context.threshold):
                            raise RuntimeError("Invalid conditional retry")
            averages = average_metrics(context_rows)
            output.append({"profile": profile, "beta": beta, "exact_equal_context_average": averages,
                           "exact_by_state": {state: {"contexts": mode_counts[state], **average_metrics(rows)} for state, rows in groups.items()},
                           "monte_carlo": dict(sample_stats), "contexts": context_rows})
            print(f"{profile} beta={beta:g}: accept={averages['mode_acceptance_rate']:.3%}, score>=75={averages['score_ge_75_rate']:.3%}", flush=True)
    return output, {"sampled_first_sets": sampled_total, "sampled_conditional_retry_sets": retry_total, "hard_rule_violations": invalid}


def markdown_report(report):
    lines = ["# Thử phân bố trọng số hàm mũ — MVP 1", "",
             f"Bể **00–99**, trần quota **4**; runtime dùng **beta = {report['selected_beta']}**. Core Mai Hoa Y/M/D/H và lớp lịch không bị thay đổi trong kiểm chứng này.", "",
             "Thử `b(n) = exp(beta × (S_i − max_allowed_S) / 100)`, sau đó ×3 hành giải sát và cộng các delta đã khóa. Beta lớn hơn ưu tiên mạnh hơn số có S_i cao. Trừ max là ổn định số học; mọi bộ có sáu số nên không đổi phân bố tương đối.", "",
             "Xác suất một bộ hợp lệ tỷ lệ tích trọng số của sáu số, cùng luật sampling của runtime. Dùng đa thức đối xứng để tính chính xác khối lượng từng cấu hình và bốc tập không hoàn lại; khác cách bốc tuần tự rồi xóa số. Các profile delta dưới đây chỉ là dữ liệu tổng hợp.", "",
             "125 tổ hợp P/Thể/Dụng có trọng số bằng nhau. Hai profile: không có delta phụ; và delta tổng hợp minh họa (tháng Dần, hào 2, Kim +30%/Thủy +20% Thần Sát, danh sách dân gian đã chốt). Profile minh họa không phải lá số thật, không suy ra tần suất sao hoặc các KPI thực tế.", "",
             "| Profile | Beta | Đạt ngưỡng mode lượt 1 | Điểm ≥75 lượt 1 | Điểm trung bình |",
             "|---|---:|---:|---:|---:|"]
    for row in report["results"]:
        m = row["exact_equal_context_average"]
        profile = "Không delta phụ" if row["profile"] == PROFILES[0] else "Delta minh họa"
        lines.append(f"| {profile} | {row['beta']:g} | {m['mode_acceptance_rate']:.2%} | {m['score_ge_75_rate']:.2%} | {m['mean_score']:.2f} |")
    lines.extend(["", "Các tỷ lệ bảng trên tính từ toàn bộ cấu hình, không phải ước lượng từ Monte Carlo. JSON có phân bố chẵn/lẻ, số lượng kỳ vọng từng hành, kết quả từng ngữ cảnh và số bộ trùng trong lượt lấy mẫu. Trùng bộ giữa các phiên/lượt độc lập vẫn có thể xảy ra, khác việc trùng số bên trong bộ.", "",
                  "Retry trong thử nghiệm chọn trực tiếp từ cấu hình 3–3 đạt ngưỡng, giữ G_cap/ngưỡng/quẻ cũ. Trong Đại Hung thêm lọc số khắc Thể như phương án retry hiện có. Tỷ lệ đạt sau bước đó đến từ điều kiện bộ sinh; không chứng minh ×3 hoặc phép gieo ngẫu nhiên bất kỳ chắc chắn đạt.", "",
                  f"Monte Carlo seed **{report['seed']}**, **{report['samples_per_context']} bộ/ngữ cảnh/profile/beta**: {report['sampling_checks']['sampled_first_sets']:,} bộ đầu và {report['sampling_checks']['sampled_conditional_retry_sets']:,} bộ retry; lỗi luật cứng **{report['sampling_checks']['hard_rule_violations']}**.", "",
                  f"**Runtime giữ beta = {report['selected_beta']}.** Kiểm chứng này không thay đổi beta; cần corpus hồ sơ/thời gian đại diện để đánh giá tỷ lệ đạt và độ đa dạng thực tế. Điểm phong thủy nội bộ không đo xác suất trúng thưởng hay hiệu quả cải vận.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/research")
    parser.add_argument("--samples-per-context", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--betas", type=float, nargs="+")
    args = parser.parse_args()
    if args.samples_per_context < 1:
        parser.error("samples-per-context must be positive")
    rules = json.loads(RULES_PATH.read_text())
    quota_max = rules["remediation"]["target_quota_max"]
    if (rules["remediation"]["target_quota_min"], quota_max) != (3, 4):
        parser.error("This audit requires the confirmed quota 3..4")
    betas = args.betas if args.betas is not None else rules["exponential_weights"]["trial_betas"]
    if any(not isfinite(beta) or not 0 <= beta <= 20 for beta in betas):
        parser.error("This numerical trial supports finite beta values from 0 to 20")
    expected_numbers = {"pool_min": 0, "pool_max": 99, "set_size": 6, "without_replacement": True,
                        "reject_single_parity": True, "reject_six_of_one_element": True}
    if rules["numbers"] != expected_numbers:
        parser.error("This experiment implements only the declared MVP 1 pool and hard number rules")
    if (rules["evaluation"]["yin_yang_weight"], rules["evaluation"]["element_weight"],
        rules["evaluation"]["thresholds"]) != (0.4, 0.6, {"DAI_CAT": 80, "NORMAL": 80, "DAI_HUNG": 85}):
        parser.error("Changed scoring policy requires a new audit implementation")
    if (rules["remediation"]["only_dai_hung"], rules["remediation"]["ban_controlling_primary_from_attempt"],
        rules["remediation"]["target_weight_multiplier"]) != (True, 1, 3):
        parser.error("Changed remediation policy requires a new audit implementation")
    folk_numbers = {entry["number"] for entry in json.loads(FOLK_PATH.read_text())["entries"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    revision = rules["rules_version"].rsplit("-", 1)[-1]
    feasibility = feasibility_report(quota_max)
    (args.output_dir / f"remediation_feasibility_{revision}.json").write_text(json.dumps(feasibility, ensure_ascii=False, indent=2) + "\n")
    results, checks = run(betas, args.samples_per_context, args.seed, quota_max, folk_numbers)
    report = {"status": "SYNTHETIC_DISTRIBUTION_AUDIT_NOT_PRODUCT_KPI", "rules_version": rules["rules_version"],
              "numbers": rules["numbers"], "rules_sha256": digest(RULES_PATH), "folk_config_sha256": digest(FOLK_PATH),
              "implementation_sha256": {"optimizer_and_sampler": digest(ROOT / "research_tools/weighted_sampling.py"),
                                         "audit": digest(ROOT / "research_tools/exponential_audit.py")},
              "seed": args.seed, "samples_per_context": args.samples_per_context,
              "beta_formula": "exp(beta * (S_i - max_allowed_S) / 100)", "selected_beta": rules["exponential_weights"]["selected_beta"],
              "sampling_law": "P(set | hard constraints) proportional to product(number weights)",
              "context_distribution": "Equal weight for each of 125 synthetic P/The/Dung combinations; not observed natal/casting distribution",
              "bonus_profile_is_synthetic": True, "sampling_checks": checks, "results": results}
    (args.output_dir / f"exponential_distribution_trial_{revision}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (args.output_dir / f"exponential_distribution_trial_{revision}.md").write_text(markdown_report(report))
    print(json.dumps({"feasible_hung": feasibility["all_hung_have_passing_retry"], **checks}))


if __name__ == "__main__":
    main()
