#!/usr/bin/env python3
"""Run the survey analyses from included records.

Default: Python standard library only. Reads the included analysis inputs and
writes reproduced/numeric-validation.json plus recomputed numerical summaries.
This validates arithmetic and consistency of recorded signatures, not SQL
execution, interpretation validity, source transcription, or human judgments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path


PAIRS = ("IB", "IC", "IA", "BC", "BA", "CA")
STATES = {"P", "N", "U"}
ROLES = "analysis/data/overlap/roles"
REL = "analysis/data/overlap/relationships"
HARM = "analysis/data/benchmarks"
CLARITY = "analysis/data/clarity/outputs"


class CheckError(Exception):
    pass


def require(ok, message):
    if not ok:
        raise CheckError(message)


def compare(actual, expected, where):
    """Compare machine data, allowing only negligible float serialization error."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected),
                f"{where}: dictionary keys differ")
        for key in expected:
            compare(actual[key], expected[key], f"{where}.{key}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected),
                f"{where}: list size differs")
        for index, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, f"{where}[{index}]")
    elif expected is None or isinstance(expected, (str, bool)):
        require(type(actual) is type(expected) and actual == expected,
                f"{where}: expected {expected!r}, got {actual!r}")
    elif isinstance(expected, int):
        require(type(actual) in (int, float) and actual == expected,
                f"{where}: expected {expected}, got {actual!r}")
    else:
        require(type(actual) in (int, float) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10),
                f"{where}: expected {expected!r}, got {actual!r}")


def integer(value, where):
    require(not isinstance(value, bool), f"{where}: Boolean is not an integer")
    try:
        result = int(value)
    except (ValueError, TypeError) as exc:
        raise CheckError(f"{where}: invalid integer {value!r}") from exc
    require(str(result) == str(value).strip(), f"{where}: noninteger {value!r}")
    return result


def number(value):
    if value is None or str(value).strip().lower() in ("", "none", "null", "na", "n/a"):
        return None
    result = float(value)
    require(math.isfinite(result), "Nonfinite numeric value")
    return result


def boolean(value):
    if isinstance(value, bool):
        return value
    require(value in ("True", "False"), f"Invalid Boolean {value!r}")
    return value == "True"


def index(rows, fields, where):
    result = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        require(key not in result, f"{where}: duplicate key {key}")
        result[key] = row
    return result


class Package:
    def __init__(self, root):
        self.root = root.resolve()
        self.out = self.root / "reproduced"
        self.inputs = {}
        self.out.mkdir(parents=True, exist_ok=True)
        require(self.out.resolve().is_relative_to(self.root),
                "reproduced/ must not point outside the package")

    def path(self, relative):
        path = (self.root / relative).resolve()
        require(path.is_relative_to(self.root) and path.is_file(),
                f"Required package input missing or outside package: {relative}")
        return path

    def track(self, relative):
        path = self.path(relative)
        raw = path.read_bytes()
        self.inputs[relative] = hashlib.sha256(raw).hexdigest()
        return raw

    def json(self, relative):
        return json.loads(self.track(relative))

    def csv(self, relative):
        return list(csv.DictReader(self.track(relative).decode("utf-8-sig").splitlines()))

    def jsonl(self, relative):
        return [json.loads(line) for line in self.track(relative).decode("utf-8").splitlines()
                if line.strip()]

    def write(self, name, data):
        target = self.out / name
        require(target.resolve().is_relative_to(self.out.resolve()),
                "Output must remain inside reproduced/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")

    def unchanged(self):
        for relative, expected in self.inputs.items():
            require(hashlib.sha256(self.path(relative).read_bytes()).hexdigest() == expected,
                    f"Input changed during reproduction: {relative}")


def choice(state):
    require(state in STATES, f"Invalid state {state!r}")
    return (1,) if state == "P" else (0,) if state == "N" else (0, 1)


def pair_metrics(records):
    output = {}
    for pair in PAIRS:
        p, q = pair
        complete = [r for r in records if "U" not in (r["states"][p], r["states"][q])]
        both = sum(r["states"][p] == r["states"][q] == "P" for r in complete)
        union = sum("P" in (r["states"][p], r["states"][q]) for r in complete)
        # Enumerate attainable (intersection, union) totals, not independent extrema.
        attainable = {(0, 0)}
        for r in records:
            increments = {(a * b, int(bool(a or b)))
                          for a in choice(r["states"][p]) for b in choice(r["states"][q])}
            attainable = {(n + a, d + b) for n, d in attainable for a, b in increments}
        fractions = [Fraction(n, d) for n, d in attainable if d]
        output[pair] = {
            "pair": pair, "settings": len(records), "eligible": len(complete),
            "both": both, "either": union,
            "jaccard": float(Fraction(both, union)) if union else None,
            "bounds": [float(min(fractions)), float(max(fractions))] if fractions
            else [None, None],
        }
    return output


def perspectives(pkg):
    records = pkg.json(f"{REL}/outputs/strict-analysis-records.json")
    scope = pkg.json("analysis/data/analysis-scope.json")
    paper_ids = {r["paper_id"] for r in records}
    require(len(records) == scope["direct_nl2sql_settings"], "Analysis setting membership differs")
    require(paper_ids == set(scope["direct_nl2sql_paper_ids"]), "Analysis paper membership differs")
    require(len(paper_ids) == scope["direct_nl2sql_papers"], "Analysis paper count differs")
    require(paper_ids <= set(scope["analysis_source_paper_ids"]), "Paper outside fixed analysis corpus")
    require(not paper_ids.intersection(scope["excluded_literature"]), "Literature-only paper entered analysis")
    roles = pkg.json(f"{ROLES}/proposed-assignments.json")
    byid = index(records, ("setting_id",), "settings")
    byrole = index(roles, ("setting_id",), "roles")
    require(len(records) == 89 and set(byid) == set(byrole),
            "Expected the same 89 unique settings in records and roles")
    for r in records:
        require(set(r["states"]) == set("IBCA"), f"{r['setting_id']}: endpoint keys")
        require(all(s in STATES for s in r["states"].values()), "Invalid endpoint state")
        role = byrole[(r["setting_id"],)]
        require(r["states"]["C"] == role["direct"]["status"], "C differs from direct role")
        require(role["verification"]["status"] in STATES, "Invalid verification state")
        require(set(r["connections"]) == set(PAIRS), "Missing main pair")
        for pair in PAIRS:
            require(set(r["connections"][pair]) ==
                    {"integration", "relationship_evaluation"}, "Invalid properties")
            for prop, state in r["connections"][pair].items():
                require(state in STATES, "Invalid connection state")
                if state == "P":
                    require(all(r["states"][p] == "P" for p in pair),
                            "Positive connection requires present endpoints")
                # There is intentionally no G/E implication in either direction.
    direct = pair_metrics(records)
    overlap = pkg.csv(f"{ROLES}/outputs/pairwise_overlap.csv")
    require({r["pair"] for r in overlap} == set(PAIRS) and len(overlap) == 6,
            "Overlap CSV must contain exactly the six main setting pairs")
    for row in overlap:
        require(row["scope"] == "direct_NL2SQL_core" and row["unit"] == "setting",
                "Unexpected overlap population")
        m = direct[row["pair"]]
        for field, key in (("N", "settings"), ("eligible_complete_pairs", "eligible"),
                           ("intersection", "both"), ("union", "either")):
            compare(integer(row[field], field), m[key], f"overlap.{row['pair']}.{field}")
        compare(number(row["jaccard"]), m["jaccard"], "Jaccard")
        compare(json.loads(row["jaccard_binary_completion_bounds"]), m["bounds"], "bounds")

    role_counts = {name: dict(Counter(r[name]["status"] for r in roles))
                   for name in ("direct", "verification")}
    combinations = dict(Counter(r["direct"]["status"] + r["verification"]["status"]
                                for r in roles))
    scopes = {}
    for name in ("direct", "verification", "inclusive"):
        scope_records = []
        for r in records:
            role = byrole[(r["setting_id"],)]
            d, v = role["direct"]["status"], role["verification"]["status"]
            c = ("P" if "P" in (d, v) else "N" if d == v == "N" else "U") \
                if name == "inclusive" else role[name]["status"]
            scope_records.append({"states": {**r["states"], "C": c}})
        scopes[name] = {
            "presence": dict(Counter(r["states"]["C"] for r in scope_records)),
            "pairs": list(pair_metrics(scope_records).values()),
        }
    stored = pkg.json(f"{ROLES}/definition-sensitivity.json")
    compare(stored["roles"], role_counts, "role counts")
    if "role_combinations" in stored:
        compare(stored["role_combinations"], combinations, "role combinations")
    for name, calculated in scopes.items():
        compare(stored["scopes"][name]["presence"], calculated["presence"], name)
        saved = index(stored["scopes"][name]["pairs"], ("pair",), name)
        require(set(saved) == {(p,) for p in PAIRS}, f"{name}: pair inventory")
        for m in calculated["pairs"]:
            for k, v in m.items():
                compare(saved[(m["pair"],)][k], v, f"{name}.{m['pair']}.{k}")

    counts = pkg.csv(f"{REL}/outputs/connection_counts.csv")
    count_index = index(counts, ("pair", "property"), "connection counts")
    expected_keys = {(p, prop) for p in PAIRS
                     for prop in ("integration", "relationship_evaluation")}
    require(set(count_index) == expected_keys, "Expected independent G and E rows for six pairs")
    recalculated = []
    for (pair, prop), row in count_index.items():
        require(row["scope"] == "direct_NL2SQL_core" and row["unit"] == "setting",
                "Unexpected connection population")
        eligible = [r for r in records if all(r["states"][p] == "P" for p in pair)]
        states = Counter(r["connections"][pair][prop] for r in eligible)
        values = {"N": len(records), "both_perspectives_present": len(eligible),
                  "among_PP_present": states["P"], "among_PP_absent": states["N"],
                  "among_PP_unclear": states["U"]}
        for key, value in values.items():
            compare(integer(row[key], key), value, f"{pair}.{prop}.{key}")
        recalculated.append({"pair": pair, "property": prop, **values})
    contract = pkg.json(f"{REL}/reviews/verification.json")
    evaluated = [r for r in recalculated if r["property"] == "relationship_evaluation"]
    totals = {state: sum(r[field] for r in evaluated) for state, field in
              (("P", "among_PP_present"), ("N", "among_PP_absent"), ("U", "among_PP_unclear"))}
    compare(totals, contract["manuscript_results"]["main_evaluation_totals"], "manuscript relationship totals")
    ib = next(r for r in evaluated if r["pair"] == "IB")
    ib_totals = {state: ib[field] for state, field in
                 (("P", "among_PP_present"), ("N", "among_PP_absent"), ("U", "among_PP_unclear")) if ib[field]}
    compare(ib_totals, contract["manuscript_results"]["ib_empirical_evaluation"], "manuscript IB result")
    result = {"revision": contract["revision"], "main_evaluation_totals": totals,
              "roles": role_counts, "role_combinations": combinations,
              "scopes": scopes, "connection_counts": recalculated}
    pkg.write("perspective-calculations.json", result)
    return {"settings": 89, "overlap_rows": len(overlap),
            "connection_rows": len(counts), "independent_G_E": True,
            "scope": "Numerical summaries of fixed scientific labels, not label validation."}


def scare(pkg):
    rows = pkg.csv(f"{HARM}/inputs/scare_table3.csv")
    stored = pkg.json(f"{HARM}/outputs/scare_reconstruction.json")
    require(len(rows) == 7 and len({r["method"] for r in rows}) == 7, "SCARE method inventory")
    require(set(stored) == {r["method"] for r in rows}, "SCARE stored methods differ")
    rebuilt = {}
    for row in rows:
        n = integer(row["n_per_category"], "SCARE n")
        require(n > 0, "SCARE category size must be positive")
        total = 4 * n
        width = Fraction(row["rounding_halfwidth_pp"])
        require(width == Fraction(1, 20), "Expected the declared +/-0.05 percentage-point rule")
        def matches(k, denominator, percentage):
            return denominator > 0 and abs(
                Fraction(100 * k, denominator) - Fraction(percentage)) <= width
        def counts(percentage):
            return [k for k in range(n + 1) if matches(k, n, percentage)]
        def predictions(precision, recall):
            return [(tp, denom) for tp in counts(recall)
                    for denom in range(max(1, tp), total + 1)
                    if matches(tp, denom, precision)]
        options = []
        pools = [counts(row[k]) for k in ("PR", "Cov_AC", "CR", "Cov_AI")]
        pools.extend((predictions(row["Prec_M"], row["Rec_M"]),
                      predictions(row["Prec_U"], row["Rec_U"])))
        for cac, aac, cai, aai, (tm, pm), (tu, pu) in itertools.product(*pools):
            if cac > aac or cai > aai:
                continue
            rejected_feasible = 2 * n - aac - aai
            low = max(0, pm - tm - (n - tu), rejected_feasible - (pu - tu))
            high = min(rejected_feasible, pm - tm, n - tm - (pu - tu) + rejected_feasible)
            if low > high:
                continue
            a, af, c = total - pm - pu, aac + aai, cac + cai
            if not 0 < af <= a <= total:
                continue
            options.append({
                "C_AC": cac, "A_AC": aac, "C_AI": cai, "A_AI": aai,
                "TP_M": tm, "predicted_M": pm, "TP_U": tu, "predicted_U": pu,
                "answerable_to_M_min": low, "answerable_to_M_max": high,
                "A": a, "Af": af, "C": c, "A_nonanswerable": a - af,
                "answerable_coverage": af / (2 * n),
                "answerable_correct_per_request": c / (2 * n),
                "answerable_marginal_error": (af - c) / (2 * n),
                "answerable_selective_error": (af - c) / af,
                "all_sql_return_rate": a / total,
                "native_policy_marginal_failure": (a - c) / total,
                "native_policy_selective_failure": (a - c) / a,
                "sql_M_min": n - tm - (pu - tu - rejected_feasible + high),
                "sql_M_max": n - tm - (pu - tu - rejected_feasible + low),
                "sql_U_min": n - tu - (pm - tm - low),
                "sql_U_max": n - tu - (pm - tm - high),
            })
        require(options, f"SCARE {row['method']}: no feasible reconstruction")
        int_keys = ("C_AC", "A_AC", "C_AI", "A_AI", "TP_M", "predicted_M", "TP_U", "predicted_U")
        saved = index(stored[row["method"]]["options"], int_keys, "SCARE saved options")
        actual = index(options, int_keys, "SCARE computed options")
        require(set(saved) == set(actual), f"SCARE {row['method']}: feasible option set differs")
        for key in actual:
            compare(saved[key], actual[key], f"SCARE {row['method']} option")
        bounds = {k: [min(o[k] for o in options), max(o[k] for o in options)]
                  for k in options[0]}
        compare(stored[row["method"]]["compatible_aggregates"], len(options), "SCARE option count")
        compare(stored[row["method"]]["bounds"], bounds, "SCARE bounds")
        rebuilt[row["method"]] = {
            "compatible_aggregates": len(options), "options": options, "bounds": bounds,
        }
    pkg.write("scare-reconstruction.json", rebuilt)
    return {"methods": len(rebuilt), "feasible_option_sets_checked": True,
            "rounding": "Exact rational +/-0.05 percentage points, inclusive endpoints",
            "scope": "Assumes pooled counts and supplied transcription. No source-table reinspection."}


def published_percentage(text):
    text = str(text).strip()
    multiplier = 1000 if text.endswith("K") else 1
    return Fraction(text.rstrip("K")) * multiplier, Fraction(multiplier, 20)


def trustsql(pkg):
    inputs = pkg.csv(f"{HARM}/inputs/trustsql_count_records.csv")
    saved = index(pkg.csv(f"{HARM}/outputs/trustsql_reconstructed.csv"),
                  ("dataset", "method"), "TrustSQL retained")
    excluded = index(pkg.json(f"{HARM}/outputs/trustsql_excluded.json"),
                     ("dataset", "method"), "TrustSQL excluded")
    checks = index(pkg.csv(f"{HARM}/outputs/trustsql_source_checks.csv"),
                   ("dataset", "method", "check"), "TrustSQL checks")
    keyed = index(inputs, ("dataset", "method"), "TrustSQL inputs")
    require(len(keyed) == 56 and len(saved) == 54 and len(excluded) == 2,
            "TrustSQL expected 56 source cells, 54 retained and two excluded")
    require(set(saved).isdisjoint(excluded) and set(saved) | set(excluded) == set(keyed),
            "TrustSQL retained/excluded partition differs")
    known_exclusions = {("Advising", "T5 → Error M"), ("ATIS", "CLS P → MAC-SQL")}
    require(set(excluded) == known_exclusions, "TrustSQL explicit exclusion identities differ")
    expected_checks, rebuilt, exclusions = set(), [], []
    for key, row in keyed.items():
        nf, ni, c, af, ai = (integer(row[k], k) for k in
                            ("n_feasible", "n_infeasible", "correct_sql",
                             "sql_feasible", "sql_infeasible"))
        require(nf > 0 and ni > 0 and 0 <= c <= af <= nf and 0 <= ai <= ni,
                f"TrustSQL {key}: invalid count constraints")
        match = re.search(r"(\d+)\s*/\s*\((\d+)\+(\d+)\)", row["source_cell"])
        require(match and tuple(map(int, match.groups())) == (c, af, ai),
                f"TrustSQL {key}: input counts disagree with source-cell transcription")
        printed_accuracy = Fraction(row["source_cell"].split()[0])
        n, wrong, declined, attempted = nf + ni, af - c, ni - ai, af + ai
        require(attempted > 0, f"TrustSQL {key}: published accuracy has no attempts")
        def score(penalty):
            return Fraction(100 * (c + declined - penalty * (wrong + ai)), n)
        accuracy = Fraction(100 * c, attempted)
        if key in excluded:
            require(row["status"] == "excluded_unresolved_inconsistent_cell",
                    "Excluded input must retain its status")
            item = excluded[key]
            for k in ("n_feasible", "n_infeasible", "correct_sql", "sql_feasible", "sql_infeasible"):
                compare(item[k], integer(row[k], k), f"Excluded {key}.{k}")
            compare(item["derived_returned_accuracy_pct"], float(accuracy), "Excluded accuracy")
            compare(item["derived_RS10_pct"], float(score(10)), "Excluded RS10")
            compare(item["derived_RSN_pct"], float(score(n)), "Excluded RSN")
            discrepancies = {"Table8_SQL_accuracy": abs(accuracy - printed_accuracy) > Fraction(1, 20)}
            for tag, penalty in (("RS0", 0), ("RS10", 10), ("RSN", n)):
                target, tol = published_percentage(item[f"published_{tag}_pct"])
                discrepancies["Table3_" + tag] = abs(score(penalty) - target) > tol
            require(any(discrepancies.values()), f"Excluded {key}: no documented discrepancy")
            exclusions.append({"dataset": key[0], "method": key[1],
                               "discrepancy_checks": discrepancies})
            continue
        require(row["status"] == "included", "Retained input status differs")
        rec = {
            "N": n, "wrong_sql_feasible": wrong, "feasible_withheld": nf - af,
            "correct_infeasible_declines": declined, "feasible_coverage": af / nf,
            "feasible_correct_per_request": c / nf, "feasible_marginal_error": wrong / nf,
            "feasible_selective_error": wrong / af if af else None,
            "all_sql_coverage": attempted / n, "infeasible_sql_return_rate": ai / ni,
            "native_policy_selective_failure": (wrong + ai) / attempted,
            "native_policy_marginal_failure": (wrong + ai) / n,
            "correct_sql_utility_component": c / n,
            "infeasible_decline_utility_component": declined / n,
            "RS_0_pct": float(score(0)), "RS_10_pct": float(score(10)),
            "RS_N_pct": float(score(n)),
        }
        for field, value in rec.items():
            compare(number(saved[key][field]), value, f"TrustSQL {key}.{field}")
        for field in ("n_feasible", "n_infeasible", "correct_sql", "sql_feasible", "sql_infeasible"):
            compare(integer(saved[key][field], field), integer(row[field], field),
                    f"TrustSQL retained {key}.{field}")
        for name, derived in [(f"Table3_RS_{penalty}", score(penalty))
                              for penalty in (0, 10, n)] + [("Table8_SQL_accuracy", accuracy)]:
            ck = (*key, name)
            require(ck in checks, f"TrustSQL missing check {ck}")
            expected_checks.add(ck)
            stored_check = checks[ck]
            target, tol = published_percentage(stored_check["published"])
            if name == "Table8_SQL_accuracy":
                compare(float(target), float(printed_accuracy), "Published Table8 value")
            passed = abs(derived - target) <= tol
            compare(number(stored_check["derived_pct"]), float(derived), f"{ck}.derived")
            compare(number(stored_check["absolute_difference_pp"]),
                    float(abs(derived - target)), f"{ck}.difference")
            compare(boolean(stored_check["pass"]), passed, f"{ck}.pass")
            require(passed, f"Retained TrustSQL check does not pass: {ck}")
        rebuilt.append({"dataset": key[0], "method": key[1], **rec})
    require(set(checks) == expected_checks and len(checks) == 216,
            "TrustSQL source-check inventory differs from four checks per retained cell")
    pkg.write("trustsql-reconstruction.json", {"retained": rebuilt, "excluded": exclusions})
    return {"source_cells": 56, "retained": 54, "excluded": 2, "arithmetic_checks": 216,
            "scope": "Checks transcribed count/score consistency, not the omitted original publication."}


def clarity_measure(rows):
    positive = [r for r in rows if r.get("all_alternatives_agree") is True]
    return {
        "N": len(rows), "conversation_records": sum(r["conversation_records"] for r in rows),
        "complete_reference_sets": sum(r.get("all_alternatives_executed") is True for r in rows),
        "unanimous_agreement": len(positive),
        "any_pair_agreement": sum(r.get("any_pair_agrees") is True for r in rows),
        "unanimous_rate": len(positive) / len(rows) if rows else None,
        "all_empty_agreements": sum(bool(r.get("all_empty")) for r in positive),
        "all_null_agreements": sum(bool(r.get("all_null")) for r in positive),
        "scalar_zero_agreements": sum(bool(r.get("all_scalar_zero")) for r in positive),
        "empty_source_relation_agreements": sum(bool(r.get("references_empty_source_relation"))
                                                for r in positive),
        "executed_query_instances": sum(sum(v["execution"]["ok"]
                                            for v in r.get("references", [])) for r in rows),
        "failed_reference_instances": sum(r.get("reference_failures", 0) for r in rows),
    }


def clarity(pkg):
    rows = pkg.jsonl(f"{CLARITY}/bundle-ledger.jsonl")
    byid = index(rows, ("bundle_id",), "CLARITY ledger")
    require(len(rows) == 3128, "CLARITY requires the full 3,128-case ledger")
    expected_pair_total = 0
    for r in rows:
        require(r["dataset"] in ("spider", "bird"), "Unknown CLARITY dataset")
        refs = r.get("references", [])
        if not refs:
            require(not r.get("fixed_output_screened_eligible"),
                    "Case without references cannot be primary")
            continue
        good = [v["execution"] for v in refs if v["execution"]["ok"]]
        complete = len(good) == len(refs) and len(refs) > 1
        compare(r["all_alternatives_executed"], complete, "CLARITY completeness")
        compare(r["reference_failures"], len(refs) - len(good), "Reference failure count")
        for execution in good:
            for sig in ("ordered_signature", "bag_signature", "set_signature"):
                require(re.fullmatch(r"[0-9a-f]{64}", execution[sig]) is not None,
                        "Invalid recorded result signature")
            compare(execution["empty"], execution["row_count"] == 0, "Empty-result flag")
        comparator = "ordered_signature" if r["outer_order_required"] else "bag_signature"
        unanimous = len({v[comparator] for v in good}) == 1 if complete else None
        compare(r["all_alternatives_agree"], unanimous, "CLARITY unanimity")
        for flag, key in (("all_empty", "empty"), ("all_null", "all_null"),
                          ("all_scalar_zero", "scalar_zero")):
            if complete:
                compare(r[flag], all(v[key] for v in good), f"CLARITY {flag}")
        frequency = Counter(v[comparator] for v in good)
        matches = sum(n * (n - 1) // 2 for n in frequency.values())
        pairs = len(good) * (len(good) - 1) // 2
        compare(r["executed_pair_count"], pairs, "Executed pair count")
        compare(r["matching_pair_count"], matches, "Matching pair count")
        compare(r["any_pair_agrees"], matches > 0 if complete else None, "Any-pair flag")
        expected_pair_total += pairs
        if r["fixed_output_screened_eligible"]:
            require(complete and not r["category"].startswith("value")
                    and not r.get("fixed_output_exclusion_reasons"),
                    "Primary eligibility conflicts with recorded exclusion gates")
        populations = r.get("source_relation_population", [])
        if populations:
            compare(r["references_empty_source_relation"],
                    any(v.get("ok") and v["row_count"] == 0 for v in populations),
                    "Recorded source-table emptiness")
            if r.get("all_identified_source_relations_nonempty"):
                require(all(v.get("ok") and v["row_count"] > 0 for v in populations),
                        "Nonempty-source condition contradicts recorded table counts")

    pair_rows = pkg.csv(f"{CLARITY}/pair-comparisons.csv")
    seen = set()
    for row in pair_rows:
        key = (row["bundle_id"], integer(row["reference_i"], "reference_i"),
               integer(row["reference_j"], "reference_j"))
        require(key not in seen, "Duplicate CLARITY pair")
        seen.add(key)
        require((key[0],) in byid, "Pair references missing ledger case")
        r = byid[(key[0],)]
        refs = r["references"]
        require(0 <= key[1] < key[2] < len(refs), "Invalid reference pair indices")
        a, b = refs[key[1]]["execution"], refs[key[2]]["execution"]
        require(a["ok"] and b["ok"], "Pair contains a failed reference")
        require(row["dataset"] == r["dataset"] and row["category"] == r["category"],
                "Pair and ledger scope differ")
        expected = {
            "row_bag_equal": a["bag_signature"] == b["bag_signature"],
            "ordered_list_equal": a["ordered_signature"] == b["ordered_signature"],
            "row_set_equal": a["set_signature"] == b["set_signature"],
            "declared_comparator_equal": a["ordered_signature" if r["outer_order_required"]
                                             else "bag_signature"] ==
                                         b["ordered_signature" if r["outer_order_required"]
                                             else "bag_signature"],
            "either_empty": a["empty"] or b["empty"],
            "both_empty": a["empty"] and b["empty"],
            "fixed_output_screened_eligible": r["fixed_output_screened_eligible"],
        }
        for field, value in expected.items():
            compare(boolean(row[field]), value, f"CLARITY pair.{field}")
    require(len(seen) == expected_pair_total, "CLARITY pair ledger is incomplete")

    saved = pkg.json(f"{CLARITY}/agreement-summary.json")
    rates = index(pkg.csv(f"{CLARITY}/agreement-rates.csv"),
                  ("dataset", "category", "population"), "CLARITY rates")
    expected_rates, rebuilt = {}, {}
    for dataset in ("spider", "bird"):
        data = [r for r in rows if r["dataset"] == dataset]
        complete = [r for r in data if r.get("all_alternatives_executed")]
        primary = [r for r in data if r.get("fixed_output_screened_eligible")]
        single = [r for r in primary if all(len(t["spans"]) == 1 for t in r["targets"])]
        populations = {
            "complete_execution_diagnostic": complete,
            "complete_column_execution_diagnostic": [r for r in complete
                                                     if not r["category"].startswith("value")],
            "fixed_output_screened": primary,
            # This excludes all-empty sets, not every set with an empty member.
            "fixed_output_nonempty_results": [r for r in primary if not r.get("all_empty")],
            "fixed_output_nonempty_source_relations": [r for r in primary
                                                       if r.get("all_identified_source_relations_nonempty")],
            "fixed_output_nonempty_source_and_results": [
                r for r in primary if r.get("all_identified_source_relations_nonempty")
                and not r.get("all_empty")],
            "fixed_output_nonnull_nonempty_results": [
                r for r in primary if not r.get("all_empty") and not r.get("all_null")],
            "fixed_output_single_target_occurrence": single,
            "fixed_output_single_occurrence_nonempty_source": [
                r for r in single if r.get("all_identified_source_relations_nonempty")],
        }
        summary = {
            "intake_bundles": len(data),
            "category_bundles": dict(Counter(r["category"] for r in data)),
            "status_counts": dict(Counter(r["status"] for r in data)),
            "construction_unresolved_reasons": dict(Counter(
                r.get("construction_reason") for r in data if r["status"] == "construction_unresolved")),
            "populations": {name: clarity_measure(pop) for name, pop in populations.items()},
        }
        compare(saved[dataset], summary, f"CLARITY {dataset} summary")
        rebuilt[dataset] = summary
        for name, population in populations.items():
            expected_rates[dataset, "all", name] = clarity_measure(population)
            for category in sorted({r["category"] for r in data}):
                expected_rates[dataset, category, name] = clarity_measure(
                    [r for r in population if r["category"] == category])
        for db in sorted({r["db_id"] for r in primary}):
            expected_rates[dataset, "database:" + db, "fixed_output_screened"] = clarity_measure(
                [r for r in primary if r["db_id"] == db])
    require(set(rates) == set(expected_rates), "CLARITY rate-row inventory differs")
    for key, values in expected_rates.items():
        for field, value in values.items():
            compare(number(rates[key][field]), value, f"CLARITY rates {key}.{field}")
    pkg.write("clarity-calculations.json", rebuilt)
    return {
        "cases": len(rows), "signature_pairs_checked": len(pair_rows),
        "primary": {ds: rebuilt[ds]["populations"]["fixed_output_screened"]
                    for ds in ("spider", "bird")},
        "source_nonempty": {
            ds: rebuilt[ds]["populations"]["fixed_output_nonempty_source_relations"]
            for ds in ("spider", "bird")},
        "scope": "Recomputes saved-signature agreement and conditional denominators. "
                 "SQL, table counts, screening semantics and interpretation validity are not rerun. "
                 "The independent_targeted_review summary is not validated from this ledger.",
    }


def additional_checks(pkg):
    commands = [
        "analysis/checks/check_relationship_reviews.py",
        "analysis/checks/check_benchmark_audit.py",
        "analysis/checks/check_recorded_reviews.py",
        "analysis/clarity/verify_cases.py",
        "analysis/scare/check_tradeoff.py",
        "analysis/benchmarks/verify_recorded.py",
    ]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for command in commands:
        pkg.track(command)
        result = subprocess.run([sys.executable, str(pkg.path(command))],
                                cwd=pkg.root, env=env, capture_output=True, text=True)
        require(result.returncode == 0,
                f"Check {command} failed: {(result.stderr or result.stdout)[-2000:]}")
        print(f"{command}: pass")
    return {"status": "pass", "commands": commands,
            "scope": "Checks included records without network, databases, or model inference."}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    pkg = Package(Path(__file__).resolve().parents[1])
    results = {}
    for name, function in (("perspectives", perspectives), ("scare", scare),
                           ("trustsql", trustsql), ("clarity", clarity)):
        try:
            results[name] = {"status": "pass", **function(pkg)}
            print(f"{name}: pass")
        except (CheckError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            results[name] = {"status": "fail", "error": str(exc)}
            print(f"{name}: FAIL: {exc}", file=sys.stderr)
    try:
        results["additional_checks"] = additional_checks(pkg)
    except (CheckError, OSError) as exc:
        results["additional_checks"] = {"status": "fail", "error": str(exc)}
    try:
        pkg.unchanged()
        immutable = True
    except (CheckError, OSError) as exc:
        immutable = False
        results["input_integrity"] = {"status": "fail", "error": str(exc)}
    passed = immutable and all(r["status"] == "pass" for r in results.values())
    receipt = {
        "status": "pass" if passed else "fail",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": results, "inputs_unchanged": immutable, "input_sha256": pkg.inputs,
        "not_performed": [
            "Source-fulltext inspection or verification of published-table transcription",
            "Database access, SQL reruns, model inference, or external fetches",
            "Independent semantic validation of interpretations or scientific labels",
            "Independent human review",
        ],
    }
    pkg.write("numeric-validation.json", receipt)
    print("Receipt: reproduced/numeric-validation.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
