from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.run_xml import (
    VaspRunXmlError,
    VaspRunXmlParser,
)

VASPRUN_XML = b"""<?xml version="1.0" encoding="ISO-8859-1"?>
<modeling>
  <generator>
    <i name="program" type="string">vasp</i>
    <i name="version" type="string">6.4.3</i>
  </generator>
  <incar>
    <i name="IBRION">2</i><i name="NSW">5</i><i name="ISIF">3</i>
  </incar>
  <kpoints>
    <varray name="kpointlist">
      <v>0.0 0.0 0.0</v><v>0.5 0.0 0.0</v>
    </varray>
    <varray name="weights"><v>0.5</v><v>0.5</v></varray>
  </kpoints>
  <atominfo>
    <array name="atoms"><set>
      <rc><c>Si</c><c>1</c></rc><rc><c>Si</c><c>1</c></rc>
    </set></array>
  </atominfo>
  <structure name="initialpos">
    <crystal><varray name="basis">
      <v>2.7 0.0 2.7</v><v>2.7 2.7 0.0</v><v>0.0 2.7 2.7</v>
    </varray></crystal>
    <varray name="positions"><v>0.0 0.0 0.0</v><v>0.25 0.25 0.25</v></varray>
  </structure>
  <calculation>
    <scstep><energy>
      <i name="e_fr_energy">-10.0</i>
      <i name="e_wo_entrp">-9.9</i>
      <i name="e_0_energy">-9.95</i>
    </energy></scstep>
    <scstep><energy>
      <i name="e_fr_energy">-10.8</i>
      <i name="e_wo_entrp">-10.7</i>
      <i name="e_0_energy">-10.75</i>
    </energy></scstep>
    <structure>
      <crystal><varray name="basis">
        <v>2.8 0.0 2.8</v><v>2.8 2.8 0.0</v><v>0.0 2.8 2.8</v>
      </varray></crystal>
      <varray name="positions"><v>0.0 0.0 0.0</v><v>0.24 0.24 0.24</v></varray>
    </structure>
    <varray name="forces"><v>0.01 0.0 0.0</v><v>-0.01 0.0 0.0</v></varray>
    <varray name="stress">
      <v>1.0 0.0 0.0</v><v>0.0 2.0 0.0</v><v>0.0 0.0 3.0</v>
    </varray>
    <energy>
      <i name="e_fr_energy">-10.8</i>
      <i name="e_wo_entrp">-10.7</i>
      <i name="e_0_energy">-10.75</i>
    </energy>
    <eigenvalues><array><set><set comment="spin 1">
      <set comment="kpoint 1"><r>-1.0 1.0</r><r>0.5 0.0</r></set>
      <set comment="kpoint 2"><r>-0.8 1.0</r><r>0.7 0.0</r></set>
    </set></set></array></eigenvalues>
    <dos><i name="efermi">0.1</i></dos>
  </calculation>
  <structure name="finalpos">
    <crystal><varray name="basis">
      <v>2.8 0.0 2.8</v><v>2.8 2.8 0.0</v><v>0.0 2.8 2.8</v>
    </varray></crystal>
    <varray name="positions"><v>0.0 0.0 0.0</v><v>0.24 0.24 0.24</v></varray>
  </structure>
</modeling>
"""


class VaspRunXmlParserTest(unittest.TestCase):
    def test_extracts_structures_trajectory_and_spectrum(self) -> None:
        data = VaspRunXmlParser().parse(VASPRUN_XML)

        self.assertEqual(data.program, "vasp")
        self.assertEqual(data.program_version, "6.4.3")
        self.assertEqual(data.atom_labels, ("Si", "Si"))
        self.assertEqual(data.incar_ibrion, 2)
        self.assertEqual(data.incar_nsw, 5)
        self.assertEqual(data.incar_isif, 3)
        self.assertEqual(len(data.k_points), 2)
        self.assertEqual(data.k_point_weights, (0.5, 0.5))
        self.assertEqual(len(data.ionic_steps), 1)
        step = data.ionic_steps[0]
        self.assertEqual(len(step.electronic_steps), 2)
        self.assertEqual(step.free_energy_ev, -10.8)
        self.assertEqual(step.forces_ev_per_angstrom[0], (0.01, 0.0, 0.0))
        self.assertEqual(step.stress_kbar[2], (0.0, 0.0, 3.0))
        self.assertEqual(
            data.final_structure.positions_fractional[1], (0.24, 0.24, 0.24)
        )
        assert data.eigenvalues_ev is not None
        assert data.occupations is not None
        self.assertEqual(data.eigenvalues_ev[0][1], (-0.8, 0.7))
        self.assertEqual(data.occupations[0][0], (1.0, 0.0))
        self.assertEqual(data.fermi_energy_ev, 0.1)

    def test_rejects_document_type_declarations(self) -> None:
        with self.assertRaisesRegex(VaspRunXmlError, "DTD or entity"):
            VaspRunXmlParser().parse(b"<!DOCTYPE modeling><modeling />")

    def test_rejects_truncated_xml(self) -> None:
        with self.assertRaisesRegex(VaspRunXmlError, "invalid vasprun.xml"):
            VaspRunXmlParser().parse(VASPRUN_XML[:-20])


if __name__ == "__main__":
    unittest.main()
