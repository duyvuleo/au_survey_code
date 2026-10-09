"""Independently verify a pairwise SCARE trade-off from frozen aggregate inputs.

Uses exact rational arithmetic and explicit feasible class-matrix enumeration.
No model inference, SQL execution, or modification of canonical inputs.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product, combinations
import argparse
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
FIELDS = ("C_AC", "A_AC", "C_AI", "A_AI", "TP_M", "predicted_M", "TP_U", "predicted_U")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frac(value):
    return {"exact": str(value), "decimal": float(value)}


def envelope(lines):
    """Check each exact crossing and every intervening open interval."""
    points = {F(0)}
    for (_, ca, wa), (_, cb, wb) in combinations(lines, 2):
        if wa != wb and F(ca-cb, wa-wb) >= 0:
            points.add(F(ca-cb, wa-wb))
    points = sorted(points)
    def winners(penalty):
        values = [(name, F(c)-penalty*w) for name,c,w in lines]
        best = max(v for _,v in values)
        return sorted(name for name,v in values if v == best)
    intervals = []
    for i, lo in enumerate(points):
        hi = points[i+1] if i+1 < len(points) else None
        probe = (lo+hi)/2 if hi is not None else lo+1
        win = winners(probe)
        if intervals and intervals[-1]["winners"] == win:
            intervals[-1]["upper_exclusive"] = str(hi) if hi is not None else None
        else:
            intervals.append({"lower_exclusive": str(lo), "upper_exclusive": str(hi) if hi is not None else None, "winners": win})
    boundary_points = [{"lambda": str(p), "winners": winners(p)} for p in points if len(winners(p)) > 1 or p == 0]
    return {"domain": "lambda >= 0", "open_intervals": intervals, "top_ties_and_zero": boundary_points,
            "all_line_crossings_checked": len(points)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", "--source-root", dest="repo_root", type=Path,
                    default=HERE.parents[1],
                    help="Repository root (defaults to the root containing this script).")
    root = ap.parse_args().repo_root.resolve()
    csv_path = root / "analysis/data/benchmarks/inputs/scare_table3.csv"
    json_path = root / "analysis/data/benchmarks/outputs/scare_reconstruction.json"
    before = {str(p.relative_to(root)): sha(p) for p in (csv_path, json_path)}
    assert before == {
        "analysis/data/benchmarks/inputs/scare_table3.csv": "a4cc60420f0115888cc1d5a00539694a78af67b9acd7468da76c84ddd06d8da5",
        "analysis/data/benchmarks/outputs/scare_reconstruction.json": "ca6ad17151f63f2be09557052d7921ff0559ed705f1b95aa77917a43fd6b0fb7",
    }, "SCARE input identity differs"
    with csv_path.open() as f:
        sources = list(csv.DictReader(f))
    saved = json.loads(json_path.read_text())
    methods, matrices = {}, 0
    for r in sources:
        name, n, half = r["method"], int(r["n_per_category"]), F(r["rounding_halfwidth_pp"])
        total = 4*n
        def within(k, d, field):
            return d > 0 and abs(F(100*k,d)-F(r[field])) <= half
        def candidates(field):
            return [k for k in range(n+1) if within(k,n,field)]
        def label_candidates(precision, recall):
            return [(tp,pred) for tp in candidates(recall) for pred in range(max(tp,1),total+1)
                    if within(tp,pred,precision)]
        feasible = []
        for ca,aa,ci,ai,(tm,pm),(tu,pu) in product(
                candidates("PR"), candidates("Cov_AC"), candidates("CR"), candidates("Cov_AI"),
                label_candidates("Prec_M","Rec_M"), label_candidates("Prec_U","Rec_U")):
            if ca > aa or ci > ai:
                continue
            refused = 2*n-aa-ai
            valid_matrices = []
            # Merge the two true answerable strata only for class-label margins.
            # Enumerating their refused-to-M allocation independently verifies
            # feasibility without the original closed-form interval helper.
            for f_to_m in range(refused+1):
                f_to_u = refused-f_to_m
                u_to_m = pm-tm-f_to_m
                m_to_u = pu-tu-f_to_u
                m_to_sql = n-tm-m_to_u
                u_to_sql = n-tu-u_to_m
                if min(u_to_m,m_to_u,m_to_sql,u_to_sql) >= 0:
                    valid_matrices.append((f_to_m,f_to_u,u_to_m,m_to_u,m_to_sql,u_to_sql))
            if not valid_matrices:
                continue
            matrices += len(valid_matrices)
            feasible.append((ca,aa,ci,ai,tm,pm,tu,pu))
        original_options = {tuple(o[k] for k in FIELDS) for o in saved[name]["options"]}
        assert set(feasible) == original_options, name
        assert len(feasible) == saved[name]["compatible_aggregates"]
        answerable = sorted({(ca,aa,ci,ai) for ca,aa,ci,ai,*_ in feasible})
        option_rows = []
        for ca,aa,ci,ai in answerable:
            c, returned = ca+ci, aa+ai
            option_rows.append({"C_AC":ca,"returned_AC":aa,"wrong_AC":aa-ca,"withheld_AC":n-aa,
                                "C_AI":ci,"returned_AI":ai,"wrong_AI":ai-ci,"withheld_AI":n-ai,
                                "N":2*n,"correct":c,"wrong":returned-c,"returned":returned,"withheld":2*n-returned})
        for o in saved[name]["options"]:
            assert o["C"] == o["C_AC"] + o["C_AI"]
            assert o["Af"] == o["A_AC"] + o["A_AI"]
        methods[name] = {"model":r["model"], "n_per_answerable_stratum":n,
                         "verified_full_reconstruction_options":len(feasible),
                         "distinct_answerable_count_options":option_rows,
                         "rounding_tolerance_percentage_points":str(half),
                         "published_source":r["source"], "recorded_pdf_sha256":r["source_sha256"]}
    n_values = {o["N"] for m in methods.values() for o in m["distinct_answerable_count_options"]}
    assert n_values == {2100}
    a, b = "Two-Stage", "Single-Turn-Veri-Cls"
    comparisons = []
    for x,y in product(saved[a]["options"],saved[b]["options"]):
        dc, dw = y["C"]-x["C"], (y["Af"]-y["C"])-(x["Af"]-x["C"])
        comparisons.append((dc,dw,y["Af"]-x["Af"]))
    assert set(comparisons) == {(282,62,344)}
    crossing = F(282,62)
    x,y = methods[a]["distinct_answerable_count_options"][0], methods[b]["distinct_answerable_count_options"][0]
    assert len(methods[a]["distinct_answerable_count_options"]) == len(methods[b]["distinct_answerable_count_options"]) == 1
    common_utility = (F(x["correct"])-crossing*x["wrong"])/2100
    assert common_utility == (F(y["correct"])-crossing*y["wrong"])/2100
    assert common_utility < 0
    scenario_rows = []
    names = list(methods)
    for scenario_id,opts in enumerate(product(*(methods[k]["distinct_answerable_count_options"] for k in names)),1):
        lines = [(k,o["correct"],o["wrong"]) for k,o in zip(names,opts)]
        scenario_rows.append({"scenario":scenario_id,
                              "count_choices":{k:{"correct":o["correct"],"wrong":o["wrong"]} for k,o in zip(names,opts)},
                              "among_seven_reported_methods":envelope(lines),
                              "with_analytic_always_withhold":envelope(lines+[("Always-Withhold (analytic comparator)",0,0)])})
    ref = methods["Multi-Turn-SelfRef-Cls"]["distinct_answerable_count_options"]
    low_crossings = sorted({F(z["correct"]-y["correct"],z["wrong"]-y["wrong"]) for z in ref})
    assert low_crossings == [F(11,49),F(1,4)]
    zero_crossings = {k:sorted({F(o["correct"],o["wrong"]) for o in v["distinct_answerable_count_options"]}) for k,v in methods.items()}
    max_zero = max(v for vv in zero_crossings.values() for v in vv)
    assert max_zero == F(786,221) and max_zero < crossing
    result = {
        "status":"passed independent exact-arithmetic check of frozen aggregate inputs",
        "population":{"N":2100,"initially_correct_answerable_triples":1050,"initially_incorrect_answerable_triples":1050,
                      "unit":"question-candidate triple, not necessarily a unique question","model":"Gemini-2.5-Flash"},
        "methods":methods,
        "verification":{"all_seven_methods_enumerated":len(methods),"full_rounding_compatible_options":sum(v["verified_full_reconstruction_options"] for v in methods.values()),
                        "feasible_class_matrices":matrices,"saved_options_exact_match":True,
                        "pairwise_full_option_combinations":len(comparisons),"distinct_global_answerable_count_scenarios":len(scenario_rows)},
        "pairwise_result":{"reference_method":a,"comparison_method":b,"correct_difference":282,"wrong_difference":62,
                           "returned_difference":344,"withheld_difference":-344,
                           "correct_difference_percentage_points":frac(F(282*100,2100)),
                           "wrong_difference_percentage_points":frac(F(62*100,2100)),
                           "returned_difference_percentage_points":frac(F(344*100,2100)),
                           "utility":"U_lambda = (C - lambda * W) / 2100, correct reward 1, wrong reward -lambda, withheld reward 0, lambda >= 0",
                           "difference":"U_lambda(Single-Turn-Veri-Cls) - U_lambda(Two-Stage) = (282 - 62 * lambda) / 2100",
                           "equal_utility_lambda":frac(crossing),"common_utility_at_crossing":frac(common_utility),
                           "ranking_below_crossing":b,"ranking_at_crossing":"tie","ranking_above_crossing":a,
                           "invariant_across_all_saved_and_independently_enumerated_options":True},
        "other_method_boundary":{"low_penalty_competitor":"Multi-Turn-SelfRef-Cls",
                                 "low_penalty_crossings_vs_veri_cls":[frac(v) for v in low_crossings],
                                 "always_withhold_exceeds_all_seven_for_lambda_greater_than":frac(max_zero),
                                 "always_withhold_boundary_note":"Always-Withhold is an analytic zero-utility comparator, not one of the seven reported SCARE methods. It ties Single-Turn-Veri-Cls at the boundary.",
                                 "scenarios":scenario_rows},
        "assumptions":["Published percentages are interpreted with the frozen plus/minus 0.05 percentage-point compatibility rule.",
                       "Per-category denominators are 1050 and category statistics are reconstructed as pooled counts.",
                       "All method outcomes, benchmark examples and the equal AC/AI mixture remain fixed while lambda varies.",
                       "Only answerable triples enter this utility. Ambiguity/unanswerability classification rewards and costs are excluded.",
                       "The utility is an analytical choice, not a native SCARE metric or an estimated deployment cost.",
                       "Aggregate differences do not identify paired case-level fixes, newly caused errors or individual outcome transitions.",
                       "Rounding compatibility is not sampling uncertainty or a confidence interval."],
        "source_locators":[{"path":"analysis/data/benchmarks/inputs/scare_table3.csv","lines":[1,8]},
                           {"recorded_source_text":"S14.txt","source_text_included":False,"source_url":"https://raw.githubusercontent.com/mlresearch/v297/main/assets/lee26b/lee26b.pdf", "source_pdf_sha256":"abd9c0c84ff22d2d5dc09b611ae68446178041717b0c044179e0d51efade733c","lines":[364,382],"supports":"Coverage, preservation and correction denominator definitions"},
                           {"recorded_source_text":"S14.txt","source_text_included":False,"source_url":"https://raw.githubusercontent.com/mlresearch/v297/main/assets/lee26b/lee26b.pdf", "source_pdf_sha256":"abd9c0c84ff22d2d5dc09b611ae68446178041717b0c044179e0d51efade733c","lines":[399,415],"supports":"Table 3 reported percentages"}],
        "input_sha256":before,
        "no_model_or_SQL_execution":True,
        "canonical_inputs_unchanged":all(sha(root/p)==h for p,h in before.items()),
    }
    assert result["canonical_inputs_unchanged"]
    (HERE / "reproduced").mkdir(exist_ok=True)
    (HERE/"reproduced/scare-tradeoff-receipt.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"verification":result["verification"],"pairwise_result":result["pairwise_result"],
                      "low_penalty_crossings":[str(x) for x in low_crossings],"always_withhold_boundary":str(max_zero)},indent=2))


if __name__ == "__main__":
    main()
