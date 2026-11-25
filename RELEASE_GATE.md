# Release gate

Written because V0.2 was tagged before a release record existed, and because its dedup "gate" could
not fail. The gate exists so a tag carries a file, not a claim.

## Rule

No version is tagged and no package is published until `tools/release_preflight.py` exits zero and
writes `releases/<version>/preflight.json` next to the frozen manifest. A gate record is a file,
not a claim.

## Order

1. `python3 tools/freeze_release.py --version v0.4 --tag v0.4`
   Writes `releases/v0.4/manifest.json`, hashing every tracked file except `releases/` and
   `SHA256SUMS`. It refuses to overwrite an existing release directory.
2. `python3 tools/release_preflight.py --version v0.4`
   Recomputes every manifest hash and size, checks `SHA256SUMS`, runs the validator self-test,
   the full example/schema check set, and the cosine smoke test. Writes
   `releases/v0.4/preflight.json`; refuses to overwrite an existing record.
3. Commit the manifest and the gate record. Confirm `main` carries what you think it carries.
4. Create the annotated tag (`git tag -a v0.4 -m ...`).
5. Push `main`, then the tag. Do not push any other tag from a bundle.
6. Read back what the remote serves: `git ls-remote` for `main`, the tag object and its peeled
   commit. Compare the tag's tree with the local tree.
7. Publish the package and `SHA256SUMS` only after the read-back matches.

## Tag immutability

- A release tag is annotated and points at one commit forever. It is never moved, deleted, or
  force-pushed.
- A correction is a new version and a new tag. The earlier tag stays citable; its files are not
  rewritten.
- Enforce on the remote with a tag ruleset: target `v*`, restrict updates, restrict deletions, block force pushes.
  This is separate from branch protection on `main`. If the ruleset is absent, the policy still
  binds the maintainer, but the remote does not enforce it.
- Never rewrite a commit to add a signature or fix metadata. `SIGNING.md` in the Archive records
  the same rule: losing a key or missing a signature is a new release, not a history rewrite.

## What the checks mean

| Check | Blocks when |
|---|---|
| manifest | a tracked file differs from its recorded sha256 or size, or is missing |
| checksums | `SHA256SUMS` cannot be verified, or omits a tracked file outside `releases/` |
| self-test | `validate_record.py --self-test` is not all-pass |
| examples | any record example, observation example, or JSON Schema cross-check fails |
| smoke | the cosine helper does not run at the declared W |
| gate record | a preflight record already exists, or is written while a check is `BLOCK` |

## Limits

The gate checks that the published bytes match the frozen manifest and that the code still runs.
It does not establish that the method is statistically sound, does not replace a reader re-running
the tooling, and does not create a dedup calibration that does not exist. `calibration_status` stays
`not_established` until a real detector and its hard-negative fixture exist.
