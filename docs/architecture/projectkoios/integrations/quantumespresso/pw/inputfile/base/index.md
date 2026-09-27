# `base`

For a `pw.x` component $C$, maintained projection is

$$
C \longmapsto (\mathrm{kind},\mathrm{tag},\mathrm{lines}).
$$

`QeAtomicSpecies` validates the species fields shared across calculation modes.

`QeCard` is the single nominal base for `QeControlCard`, `QeSystemCard`,
`QeElectronsCard`, `QeIonsCard`, `QeCellCard`, `QeFcpCard`, `QeRismCard`,
`QeAtomicSpeciesCard`, `QeAtomicPositionsCard`, `QeKpointsCard`,
`QeAdditionalKpointsCard`, `QeCellParametersCard`, `QeOccupationsCard`,
`QeConstraintsCard`, `QeAtomicVelocitiesCard`, `QeAtomicForcesCard`,
`QeSolventsCard`, and `QeHubbardCard`.

`QePwInputFileAssembler` consumes supported components and adds canonical
structure cards. Components without maintained semantic support are declared but
raise `NotImplementedError` before lexical projection.
