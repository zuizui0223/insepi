# Open-source licence decision gate for PolliPi + InsePi

This document records a **copyright-holder decision that automation must not make**. It is operational guidance for preparing the methods-paper software release, not legal advice.

## Current audit

At the time of this gate:

- PolliPi has no root `LICENSE`, `LICENSE.txt`, `LICENSE.md` or `COPYING`.
- InsePi has no root `LICENSE`, `LICENSE.txt`, `LICENSE.md` or `COPYING`.
- PolliPi's root `package.json` is marked `private: true` and contains no licence field.
- InsePi's `pyproject.toml` contains no project licence metadata.
- repository code search found no existing project-wide SPDX, Copyright or licence notice that already determines the outgoing licence.

Therefore both repositories remain **all-rights-reserved by default** until the copyright holder explicitly grants a licence.

## Why both repositories matter

The manuscript's method depends on two independently executable observer programs. Public reproducibility therefore requires permissions for both codebases, not only the repository that contains the final manuscript package.

The two repositories may legally use the same or different compatible licences, but using one consistent permissive licence usually makes the reproducibility story easier to explain. That consistency is a convenience, not a requirement.

## Common choices

| Licence | Main practical effect | Patent grant | Copyleft | Typical reason to choose |
|---|---|---|---|---|
| MIT | Very short permissive licence; reuse/modification/distribution allowed with notice | no explicit patent clause | no | simplest permissive release |
| BSD-3-Clause | Permissive; adds non-endorsement clause | no explicit patent clause | no | common academic/research software style |
| Apache-2.0 | Permissive plus explicit patent licence/termination and NOTICE mechanics | **yes, explicit** | no | useful where explicit patent permissions matter |
| GPL-3.0 | Strong copyleft; redistributed derivative works must remain GPL-compatible/open | explicit patent provisions | **yes, strong** | choose when downstream derivatives should remain open under GPL terms |

This table is only a high-level comparison. If institutional IP ownership, patents, contributor agreements or third-party copied code are relevant, confirm the choice with the rights holder/institution before release.

## Decision questions

Before adding a licence, explicitly answer:

1. Is the intended goal **maximum downstream reuse**, including commercial reuse? If yes, a permissive licence (MIT/BSD-3-Clause/Apache-2.0) is usually the relevant family.
2. Is an **explicit patent grant** important? If yes, Apache-2.0 is the clearest of the common permissive options listed here.
3. Must downstream modified distributions remain open under the same family of terms? If yes, consider GPL-3.0 rather than a permissive licence.
4. Does a university, employer, funder or collaborator own or share copyright in either repository? If yes, confirm authority before granting the licence.
5. Is any substantial code copied from another project rather than merely linked as a dependency? If yes, audit that code's licence before choosing an outgoing licence.

## Required explicit record

Before submission/release, record:

- PolliPi chosen licence: `UNDECIDED`
- InsePi chosen licence: `UNDECIDED`
- copyright holder / authority confirmed: `NO`
- date of decision: `UNSET`

Do not change these fields through automated result-generation or V7 workflows.

## After the decision

For **each repository**:

1. add the canonical licence text at repository root (`LICENSE` preferred);
2. add package metadata where applicable (`pyproject.toml` / npm package metadata) so tooling can identify the licence;
3. run a repository search to ensure there is no contradictory project-wide licence statement;
4. rerun unit/packaging CI;
5. rebuild the anonymous peer-review bundle and confirm `license_ready=true`;
6. include the licence file in the final immutable archive/DOI deposit.

If different licences are selected for PolliPi and InsePi, the final Data/Code Availability statement should name each one explicitly.

## Interaction with V7

The licence decision is independent of scientific validation. It must not:

- alter observer code;
- alter V6 weights or V7 baselines;
- regenerate V7;
- change claim level;
- modify evidence hashes.

V7 can remain scientifically blocked by missing frozen git objects even after licensing, and licensing can remain a submission blocker even after V7 succeeds. Treat the two gates separately.