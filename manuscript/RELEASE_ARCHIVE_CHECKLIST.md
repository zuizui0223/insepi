# Software release and archival checklist

This checklist begins **after** the locked V7 evidence bundle exists. It separates scientific validation from publication/release packaging.

## A. Scientific freeze

- [ ] exact V5 Observer-E frozen commit is externally reachable;
- [ ] exact V5 Observer-O frozen commit is externally reachable;
- [ ] V7 one-shot workflow executed once;
- [ ] V7 evidence artifact retained even if scientific gate = FAIL;
- [ ] V7 execution ledger/report hashes recorded;
- [ ] claim level A–E assigned mechanically;
- [ ] post-V7 finalization workflow run from the immutable V7 artifact;
- [ ] finalization receipt recorded;
- [ ] no method/weight/threshold change is labelled as the same V7 generation.

## B. Open-source licence — explicit copyright-holder choice

**Currently unresolved.** Do not release the code archive until a root licence file has been chosen explicitly.

Common permissive options to consider:

- **MIT:** short, broad reuse permission, simple attribution/copyright notice;
- **BSD-3-Clause:** similarly permissive, with an additional non-endorsement clause;
- **Apache-2.0:** permissive plus an explicit patent licence, but longer/more complex;
- copyleft options such as GPL impose materially different redistribution obligations and should be selected only deliberately.

The repository automation does not choose among these licences.

- [ ] chosen licence added at repository root;
- [ ] copyright holder/year checked;
- [ ] third-party code/model licences checked for compatibility;
- [ ] generated anonymous review bundle reports `license_ready=true`.

## C. Versioned release

- [ ] decide semantic release version (suggest a first methods-paper release such as `v1.0.0` only after scientific freeze);
- [ ] tag the exact release commit;
- [ ] release notes distinguish V1–V7 development history from the released method;
- [ ] release notes state the locked V7 claim level;
- [ ] verify generic guarded-portfolio API example runs from a clean environment;
- [ ] verify Python version/dependency metadata;
- [ ] retain canonical PolliPi/InsePi names only in the public post-review release, not in double-anonymous files.

## D. Stable archive / DOI

- [ ] connect the release repository to a stable archival service (e.g. institutional archive or Zenodo-compatible workflow);
- [ ] archive the exact tagged source release;
- [ ] archive or include deterministic regeneration instructions for simulation evidence;
- [ ] include V7 world fingerprint, pixel/trace/report hashes and finalization receipt;
- [ ] record DOI in title page and final Data Availability statement;
- [ ] verify DOI resolves to the exact release version, not a moving branch.

## E. Final reviewer/public files

- [ ] final double-anonymous manuscript has no unresolved V7 placeholders;
- [ ] final SI has no unresolved V7 placeholders;
- [ ] Figure 6 generated from the immutable report using the preregistered layout;
- [ ] Figure 1–5 regenerated from frozen pre-V7 evidence;
- [ ] references generated from `REFERENCES_VERIFIED.bib` and DOI-checked once more;
- [ ] separate title page completed with authors/affiliations/correspondence;
- [ ] author contributions completed;
- [ ] acknowledgements/conflicts/funding completed;
- [ ] Data Availability points to stable archive/DOI;
- [ ] AI-assistance disclosure retained in Methods;
- [ ] cover letter result placeholder replaced with ledger-derived claim summary.

## F. Field-data boundary

The release and paper must not imply that simulation validation establishes:

- real visit-rate accuracy;
- real taxon-classification accuracy;
- real device power/storage performance;
- ecological effect sizes.

Those remain empirical external-validation targets.
