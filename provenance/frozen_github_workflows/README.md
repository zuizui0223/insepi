# Frozen GitHub workflow provenance

These workflow YAML files are preserved byte-for-byte from the accumulated V6–V14b scientific stack but are intentionally stored outside `.github/workflows/` so generic future pull requests cannot re-run locked scientific generations.

Policy:
- `.github/workflows/test.yml` remains the normal active CI.
- `.github/workflows/v13-manual-preflight.yml` is the only active generation-specific workflow and is `workflow_dispatch` only because V13 physical validation is still result-pending.
- V6–V12 and V14–V14b workflow definitions are historical provenance only. Their committed protocols, receipts, results, scripts and exact YAML remain available here, but no generic PR/push event can execute them.
- The original V13 workflow YAML files are also preserved here. The active manual V13 preflight is a non-scientific verification gate and must not materialise a V13 result.

This relocation changes repository execution plumbing only. It does not alter any frozen observer, threshold, alpha, seed, scientific result, artifact hash, claim, or protocol.
