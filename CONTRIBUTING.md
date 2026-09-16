# Contributing

Keep one numerical engine and add instances through explicit configuration. A contribution should be usable without access to the contributor's home directory or old outputs.

## Add an instance

Follow [Add a network](docs/add-a-network.md). Include source metadata, a data-access statement, identifiers, units, the input profile and a reproducible command. Do not describe synthetic or inferred demand as observed traffic.

## Change code

Keep solver changes separate from data transformations. Add a small focused test and preserve the distinction between a feasible solution, a stopping condition, reference agreement and a pricing certificate. Never relax a tolerance merely to turn a result green.

Run `python tools/check_repository.py`, `python -B -m unittest discover -s tests -v`, and the affected input/verification tests. Include expected-rejection tests when they protect the input contract. Large benchmark runs are not required for documentation changes.

## Public artifacts

Submit selected source, small permitted examples, concise results and reproducible scripts. Exclude credentials, private trajectories, unlicensed input copies, raw personal paths, archived builds and temporary debugging output. Preserve source attribution and record any transformation of upstream data.

## Discuss a change

Use a repository issue to describe the input, expected behavior and a minimal reproducible case. Use a pull request for a focused change; do not replace the full project for a small fix.
