# Calculator-neutral simulation examples

This tree contains provider-independent simulation declarations owned by
`projectkoios.simulations`.

The maintained silicon primitive-cell material under
[`dft/pw/Si/primitive/`](dft/pw/Si/primitive/README.md) includes:

- the neutral primitive structure;
- the explicitly classified face-centered-cubic band path; and
- the Setyawan–Curtarolo 2010 path declaration.

These records neither select a calculator provider nor grant execution
authority. Provider-native inputs and retained observations belong under the
sibling [`integrations/`](../integrations/) example tree.
