# Recover the exact frozen V5 observer commits without changing them

V7 remains blocked until the exact V5 observer commits are publicly reachable.
Do **not** recreate, cherry-pick, squash, amend, rebase or recommit these methods.
Those operations change the commit SHA and break the locked V5 -> V6 -> V7
provenance chain.

Expected immutable commits:

- PolliPi: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`
- InsePi: `980813bab996909020140fad5bd83b055eb3db9c`

The V7 one-shot workflow expects each exact commit to be advertised as the tip of
branch `frozen/v5-method` in its own repository.

## Recommended fail-closed helper

The current InsePi packaging branch contains `scripts/publish_frozen_v5_ref.py`.
It does not reconstruct any history and does not checkout/reset the worktree. It
first verifies that the required object exists locally and that `origin` identifies
the expected repository. **Without `--push` it performs verification only.**

From a checkout containing the helper script, run against the local PolliPi clone:

```bash
python scripts/publish_frozen_v5_ref.py pollipi /path/to/local/pollipi
```

If and only if that reports `FROZEN_V5_RECOVERY_STATUS verified-local-only`, publish
the exact ref:

```bash
python scripts/publish_frozen_v5_ref.py pollipi /path/to/local/pollipi --push
```

Then repeat for the local InsePi clone:

```bash
python scripts/publish_frozen_v5_ref.py insepi /path/to/local/insepi
python scripts/publish_frozen_v5_ref.py insepi /path/to/local/insepi --push
```

The `--push` mode verifies that the advertised remote branch tip equals the frozen
SHA exactly after push. It aborts if the required object is absent or repository
identity does not match.

## Equivalent manual PolliPi recovery

Run from the local PolliPi clone that still contains the frozen commit:

```bash
git cat-file -e d58d0a86034a6c2d53f90efbe4245370fd7cd2e9^{commit}
git show --no-patch --format='%H %s' d58d0a86034a6c2d53f90efbe4245370fd7cd2e9
git branch -f frozen/v5-method d58d0a86034a6c2d53f90efbe4245370fd7cd2e9
git push origin refs/heads/frozen/v5-method:refs/heads/frozen/v5-method
```

Then the public check must return exactly:

```bash
git ls-remote https://github.com/zuizui0223/pollipi.git refs/heads/frozen/v5-method
# d58d0a86034a6c2d53f90efbe4245370fd7cd2e9  refs/heads/frozen/v5-method
```

## Equivalent manual InsePi recovery

Run from the local InsePi clone that still contains the frozen commit:

```bash
git cat-file -e 980813bab996909020140fad5bd83b055eb3db9c^{commit}
git show --no-patch --format='%H %s' 980813bab996909020140fad5bd83b055eb3db9c
git branch -f frozen/v5-method 980813bab996909020140fad5bd83b055eb3db9c
git push origin refs/heads/frozen/v5-method:refs/heads/frozen/v5-method
```

Then the public check must return exactly:

```bash
git ls-remote https://github.com/zuizui0223/insepi.git refs/heads/frozen/v5-method
# 980813bab996909020140fad5bd83b055eb3db9c  refs/heads/frozen/v5-method
```

## Current remote diagnosis

The two frozen branches are currently absent. Direct GitHub attempts to create
`frozen/v5-method` from the expected SHAs return `422 Object does not exist` in
both repositories. This establishes that the commits are not merely unreferenced
remote objects: an original local clone that still contains each git object is
required.

## What happens after both branch tips match

No V7 pixels are generated immediately merely because the branches exist.
Before materialisation the one-shot workflow must:

1. verify both advertised branch tips equal the frozen SHAs;
2. clone and checkout those exact commits;
3. run image-only adapter smoke tests on both frozen APIs;
4. verify the ready V7 lock, frozen allocator, generator, baseline registry and
   world-spec fingerprints;
5. only then derive the deterministic V7 master seed and materialise the one
   canonical pixel artifact.

The two observers then process the same artifact in separate frozen checkouts and
the trace-only evaluator applies the preregistered hard gate and claim ceiling.

## If a frozen commit is no longer present locally

Do not substitute a semantically similar or reconstructed commit under the same
V7 generation. Preserve the V5 hashes and report the source-generation loss as a
reproducibility failure. Any reconstructed method must receive a new method SHA
and a new validation generation label.
