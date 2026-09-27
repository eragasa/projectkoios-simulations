# Silicon primitive-cell QE relaxation fixtures

This directory contains static fixtures for the maintained QE relaxation
loading and rendering boundary:

- `Si.primitive.json` is the right-handed structure declaration;
- `Si.primitive.left-handed.json` is an explicit exception fixture;
- `relax/calculation.toml` exercises fixed-cell native controls; and
- `vc_relax/calculation.toml` exercises variable-cell native controls.

The calculation declarations bind structures, calculator and pseudopotential
identities, sampling values, and QE-native settings for deterministic software
tests. Historical qualification strings are retained as source observations,
not as current Project Koios acceptance policy.

No application runner or workflow recipe is included. Loading or rendering a
fixture does not authorize calculator execution, establish runnable resources,
demonstrate convergence, or provide numerical or scientific validation.
