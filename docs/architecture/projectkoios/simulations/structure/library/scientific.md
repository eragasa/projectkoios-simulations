# Structure library scientific semantics

## Purpose

A structure record preserves geometry and provenance. It does not establish that
the geometry is stable, experimentally realized, relaxed, or scientifically
appropriate for a calculation. Those meanings arise only from explicit
derivation or observation provenance.

## Primitive and conventional source cells

`primitive` and `conventional` describe exact PhysKit cell types and their
stored representations. They do not prove that a selected cell is the unique or
preferred crystallographic representation of a phase. External phase selection,
standardization choices, and thermodynamic qualifications remain separate
records.

## Pristine supercells

A pristine supercell is a deterministic replication of one exact source cell.
Its `UnitCellSiteOrigin` values preserve which source atom and translation
created each site. “Pristine” means the derivation contains no declared defect;
it does not mean zero temperature, zero stress, absence of impurities in an
experimental sample, or a scientifically converged supercell size.

## Ideal defect structures

An ideal host-geometry defect preserves the exact host-supercell lattice and
host positions while applying one `UnitCellDefectDelta`. Removed indices refer
to the original host atom tuple and are applied simultaneously; additions follow
in declared order.

The ideal record is not relaxed. `charge_state` is configuration metadata and is
not encoded in atomic positions or lattice bytes. Spin, compensating charge,
and an electronic state are simulation properties rather than structure bytes.

## Relaxed structures

An ion-relaxed record is published only from qualifying fixed-cell relaxation
evidence. A fully relaxed record is published only from qualifying ion-and-cell
relaxation evidence. Each is a new exact structure record and retains the exact
starting structure and calculation/evidence references.

The words “ion-relaxed” and “fully relaxed” identify the degrees of freedom
allowed by the source calculation. They do not prove that a global minimum was
found, that all forces or stresses satisfy a later policy, or that another spin
or symmetry initialization would reach the same geometry.

## External structures

A structure retrieved from Materials Project or another external database is a
retained external observation. Its exact bytes and retrieval snapshot can be
preserved, but database provenance alone does not make it a converged local
calculation input. Local use requires a separate simulation specification and,
where required, relaxation evidence.

## Scientific acceptance boundary

The structure library verifies identity, bytes, representation, derivation, and
provenance. Scientific acceptance remains outside the library. A workflow may
require exact records with specified derivation roles, but library resolution
cannot decide whether a phase, defect site, supercell size, charge, spin, or
geometry is scientifically valid.
