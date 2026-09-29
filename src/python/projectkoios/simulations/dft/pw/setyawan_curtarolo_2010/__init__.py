"""Setyawan--Curtarolo standard cells and reciprocal band paths.

The mathematical convention, special-point coordinates, and path topologies
implemented by this package come from Appendix A of Setyawan and Curtarolo,
Computational Materials Science 49 (2010) 299--312,
https://doi.org/10.1016/j.commatsci.2010.05.010. The Python implementation,
record architecture, validation, basis binding, tests, and provider projections
are Project Koios work; they are not source code transferred from the paper's
authors or from AFLOW.

Mathematical conventions
------------------------
All direct-lattice matrices use lattice vectors as *rows*::

    A = [a1; a2; a3]

and reciprocal-fractional coordinates are row vectors.  Factors of ``2*pi``
do not affect any fractional-coordinate transformation, so the reciprocal
basis used for the derivations below is

``B = A**(-T)``.

Appendix A specifies a standard primitive direct basis ``S``.  A simulation
basis may differ by an integer-unimodular direct-basis change ``U`` and a
proper Cartesian rotation ``R``::

    A = U S R,       U in GL(3, Z),       det(R) = +1.

``U`` changes the ordered lattice basis; ``R`` only changes the external
Cartesian frame.  Since ``R R**T = I``, this relation can be checked without
choosing Cartesian axes through the direct-basis Gram matrices::

    A A**T = U (S S**T) U**T.

The implementation performs the equivalent comparison of the six invariant
lengths ``|a_i|`` and ``|a_i-a_j|``.  Those quantities have units of angstrom,
so ``lattice_tolerance_angstrom`` keeps its stated dimensional meaning.  The
signs of ``det(A)`` and ``det(U S)`` must also agree, excluding an improper
Cartesian reflection from ``R``.

The reciprocal basis of the simulation is

``B_A = A**(-T) = U**(-T) B_S R``.

Equating the same physical wave vector in the rotated Cartesian frame,
``q_A B_A = q_S B_S R``, gives the fractional-coordinate rule used here::

    q_A = q_S U**T.

Thus a Cartesian rotation never changes reciprocal-fractional coordinates;
only the integer direct-basis change does.  Path coordinates are always bound
to the exact ordered basis of :class:`PwDftSimulation` before provider input is
constructed.

Object and action boundaries
----------------------------
Declared metrics, selected Appendix-A cases, path definitions, binding requests,
and bound paths are immutable ``DataObject`` records. Case selection is
performed only by ``SetyawanCurtaroloAppendixACaseSelector.action()`` over a
``SetyawanCurtaroloAppendixACaseSelectionRequest``. Cell binding is performed
only by ``SetyawanCurtaroloPathBinder.action()`` over a
``SetyawanCurtaroloPathBindingRequest``. Each action returns a frozen result
that retains its complete request and correlated output. This keeps
cross-object case-selection and basis-equivalence policy out of the input data
records without discarding action provenance.

Appendix-A case mathematics
---------------------
Lengths ``a``, ``b``, and ``c`` and direct angles ``alpha``, ``beta``, and
``gamma`` follow the crystallographic convention.  Reciprocal angles are
computed from ``B = A**(-T)``.  Appendix-A boundary cases are selected by the
following dimensionless discriminants, with equality interpreted using the
module tolerances:

* ``BCT1/BCT2``: ``c < a`` / ``c > a``;
* ``ORCF1/2/3``: the sign of ``1 - a**2/b**2 - a**2/c**2``;
* ``RHL1/RHL2``: ``alpha < 90 degrees`` / ``alpha > 90 degrees``;
* ``MCLC1/2``: reciprocal ``gamma > 90 degrees`` / ``= 90 degrees``;
* ``MCLC3/4/5``: reciprocal ``gamma < 90 degrees`` and the sign around one of
  ``b*cos(alpha)/c + b**2*sin(alpha)**2/a**2``;
* ``TRI1/TRI2``: reciprocal ``gamma != 90 degrees`` / ``= 90 degrees``;
  suffix ``a`` requires reciprocal ``alpha,beta > 90 degrees`` and suffix
  ``b`` requires both to be smaller than 90 degrees.

The point parameters ``eta``, ``zeta``, ``delta``, ``phi``, ``psi``, ``mu``,
``nu``, ``omega``, and ``rho`` are evaluated immediately beside the Appendix-A
point tables that use them.  No interpolation-count or symmetry-discovery
mathematics is added to the cited convention.
"""

from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.binding import (
    SetyawanCurtaroloBasisTransformSource,
    SetyawanCurtaroloPathBinder,
    SetyawanCurtaroloPathBindingRequest,
    SetyawanCurtaroloPathBindingResult,
    SetyawanCurtaroloPathDefinition,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.lattice import (
    SetyawanCurtaroloLattice,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.model import (
    SETYAWAN_CURTAROLO_CITATION,
    SETYAWAN_CURTAROLO_CONVENTION_NAME,
    SETYAWAN_CURTAROLO_DOI,
    SETYAWAN_CURTAROLO_REVISION,
    SetyawanCurtaroloAppendixACase,
    SetyawanCurtaroloBravaisLattice,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.selection import (
    SetyawanCurtaroloAppendixACaseSelectionRequest,
    SetyawanCurtaroloAppendixACaseSelectionResult,
    SetyawanCurtaroloAppendixACaseSelector,
)

__all__ = (
    "SETYAWAN_CURTAROLO_CITATION",
    "SETYAWAN_CURTAROLO_CONVENTION_NAME",
    "SETYAWAN_CURTAROLO_DOI",
    "SETYAWAN_CURTAROLO_REVISION",
    "SetyawanCurtaroloBasisTransformSource",
    "SetyawanCurtaroloBravaisLattice",
    "SetyawanCurtaroloLattice",
    "SetyawanCurtaroloAppendixACaseSelectionRequest",
    "SetyawanCurtaroloAppendixACaseSelectionResult",
    "SetyawanCurtaroloAppendixACaseSelector",
    "SetyawanCurtaroloPathBinder",
    "SetyawanCurtaroloPathBindingRequest",
    "SetyawanCurtaroloPathBindingResult",
    "SetyawanCurtaroloPathDefinition",
    "SetyawanCurtaroloAppendixACase",
)
