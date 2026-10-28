# Visual survey explorer

The [live explorer](https://duyvuleo.github.io/au_survey_code/) provides a literature map, searchable reading list, paper evidence panels, and a benchmark audit table. It uses recognizable names such as CLARITY, SCARE, and TrustSQL. Full titles and source IDs remain available in the evidence panels and JSON exports. A [local version](site/index.html) is included.

## Open locally

Open `site/index.html` directly in a modern browser, or serve only the site directory:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory site
```

Visit <http://127.0.0.1:8765/>. No package installation, backend, external fonts, CDN, or model calls are required. All scripts and data are included. Source links navigate to the recorded papers or GitHub files. Copy-view links preserve filters and the selected paper in the URL fragment; a localhost/file link is useful only on a machine that has the same local site. On a hosted copy, the same feature produces shareable links.

## What the views represent

- **Literature map:** 64 technical studies and five related surveys, grouped by the reading list. Branches indicate reading-group membership, not citations, influence, or measured relationships. Hollow dots identify FALCON and PlanPool, the two literature-only additions outside the fixed analysis cutoff.
- **Perspective filters:** include a paper when at least one of its mapped settings has a recorded **P** (present) for that perspective. Counts are distinct papers across the complete map, not additive counts or claims about all settings of a paper. **N** means absent in the inspected setting; **U** means unclear. Neither is treated as P.
- **Reading list:** combines name/title/ID/setting search with reading group, year, corpus, and perspective filters. Filters intersect. Export JSON includes the selected papers, original IDs, complete included setting records, audit qualifications, corpus scope, and source hashes.
- **Paper evidence:** presents the contract and source version for each included direct NL2SQL setting. Supporting verification remains separate from direct comparison of alternative answers. Strict relationship assignments reflect the retained resolutions; source rationales and review decisions remain separately accessible.
- **Benchmark audit:** exposes the 12 audited settings from 10 studies, including all finding qualifications. Null findings appear as “Not assessed,” not capability failures. BIRD-History is a context-only comparison and does not enter these 12 settings.

The fixed quantitative corpus has 62 papers and 108 settings. Only its 88 direct NL2SQL settings from 49 papers have the detailed setting records presented here. The literature cutoff is 05 October 2026; the fixed analysis publication cutoff is 01 October 2026. The explorer preserves those populations. It does not expand the survey, regenerate annotations, rerun models, or certify interpretations or deployment.

## Rebuild and verify

From the repository root:

```sh
python3 scripts/build_explorer.py
python3 scripts/build_explorer.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/explorer.test.cjs
python3 analysis/run.py
```

Python 3.10+ is sufficient for generation and data tests. JavaScript tests use Node.js 18+. The browser itself needs no Node.js. The deterministic builder joins the existing reading list, analysis scope, source setting records, strict assignments, supporting-verification roles, benchmark audit, and `site/paper-names.json`. It fails on population or endpoint disagreements. `site/data.js` is generated and should not be edited by hand.

`site/paper-names.json` is a presentation-only name map. It uses project/method names recorded in the titles, taxonomy, or setting evidence where available, and shortened descriptive titles otherwise. A shortened title is not a new official method name. Update this file when adding a reading-list entry; IDs remain the stable join keys. All scientific records remain in their existing files.

Keyboard users can activate map nodes, use arrow/Home/End keys between views, and close paper panels with Escape. The interface includes a text alternative to the map, explicit status text, light/dark themes, reduced-motion support, and layouts that adapt to narrow screens.

## Hosting

The explorer is published at <https://duyvuleo.github.io/au_survey_code/>. The `site/` directory is a standalone static site that works at a root URL or project subpath.

The [Pages workflow](.github/workflows/explorer-pages.yml) validates the publication inventory, generated explorer data, filter tests, and recorded numerical analyses before uploading only `site/`. It runs for relevant changes on `main` and can also be started with **Run workflow** in GitHub Actions. Pages uses **GitHub Actions** as its publishing source. Deployment uses the `github-pages` environment, with Pages write permission confined to the deployment job.

The explorer is hosted directly from this public companion repository. The website includes paper metadata and setting evidence, with links to the repository's source records and original papers. To update the site, regenerate `site/data.js` when its inputs change, run the documented checks, refresh `PUBLICATION.json` from the reviewed Git index using `python3 analysis/publication.py --from-index`, and push the reviewed changes to `main`.

Visual inspiration: [Awesome Reliable Text-to-SQL](https://duyvuleo.github.io/awesome-reliable-text-to-sql/) and [Awesome AI Co-Scientist](https://duyvuleo.github.io/awesome-ai-co-scientist/). This explorer implements its own interface for this survey's fixed records.
