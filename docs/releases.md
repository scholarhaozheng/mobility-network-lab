# Release channels

## Current public integration R1

This cumulative source update adds the [Hong Kong bounded GMNS/data pilot](cases/hong-kong-gmns-pilot.md) and accepted [Sioux Lagrangian R2 / ADMM R1 selected-OD evidence](methods/distributed-assignment.md), while retaining the Boston/Sioux CG case-parallel structure and earlier public content. Bush/OBA, Boston Lagrangian and Boston ADMM transfers remain visibly gated. Scientific models were not rerun for this integration. The Hong Kong instance is not assignment-ready.

## Source repository

The source tree contains the selected engine, user-facing entry point, synthetic reference inputs and documentation. `catalog/source-files.json` identifies retained engine files. The public wrapper and documentation are maintained separately from the numerical engine.

## Windows portable runtime

The existing engine artifact is `gmns_cg_0.3.0-rc5_win_x64.zip`.

SHA-256:

```text
03bab302074f52d418723bfc25c8c2b3719478219e806922e4fc6274397f90a7
```

Its manifest and third-party notices belong to that exact ZIP. If the maintainer publishes it through GitHub Releases, download it as an asset rather than expecting it inside the Git source tree. This documentation does not assert that a release asset has already been uploaded.

## Verification scope

The engine has documented Windows build-environment tests and independent Linux source checks. The selected source assembly receives its own smoke tests. Neither a static homepage nor a local source check proves independent Windows portability.
