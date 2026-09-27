from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.lammps import inspect_lammps_templates
from projectkoios.integrations.lammps.models import ObservedSetting, SourceFileEvidence


def evidence(path: str, text: str = "") -> SourceFileEvidence:
    payload = text.encode("utf-8")
    return SourceFileEvidence(path, hashlib.sha256(payload).hexdigest(), len(payload))


class InspectLammpsTemplatesTest(unittest.TestCase):
    def test_normalizes_a_historical_absolute_lammps_executable(self) -> None:
        runner_path = "lmp_scripts_db/single_point/runsimulation.sh"
        input_path = "lmp_scripts_db/single_point/in.single_point"
        runner_text = "/home/example/bin/lmp_intx_comb -i in.single_point > out.dat\n"
        observation = inspect_lammps_templates(
            simulation_settings=(
                ObservedSetting(
                    key="lmps_sim_type",
                    values=("sp", "single_point"),
                    evidence_path="pyposmat.config",
                    line_number=1,
                ),
            ),
            evidence_by_path={
                runner_path: evidence(runner_path, runner_text),
                input_path: evidence(input_path),
            },
            text_by_path={runner_path: runner_text},
        )

        intent = observation.templates[0].command_intent
        self.assertEqual(intent.executable_environment_variable, "LAMMPS_BIN")
        self.assertEqual(intent.input_script, "in.single_point")
        self.assertEqual(intent.stdout_artifact, "out.dat")
        self.assertFalse(intent.execution_authorized)

    def test_rejects_an_unrecognized_absolute_program(self) -> None:
        runner_path = "lmp_scripts_db/single_point/runsimulation.sh"
        input_path = "lmp_scripts_db/single_point/in.single_point"
        runner_text = "/bin/echo -i in.single_point > out.dat\n"
        with self.assertRaisesRegex(ValueError, "executable is unsupported"):
            inspect_lammps_templates(
                simulation_settings=(
                    ObservedSetting(
                        key="lmps_sim_type",
                        values=("sp", "single_point"),
                        evidence_path="pyposmat.config",
                        line_number=1,
                    ),
                ),
                evidence_by_path={
                    runner_path: evidence(runner_path, runner_text),
                    input_path: evidence(input_path),
                },
                text_by_path={runner_path: runner_text},
            )

    def test_rejects_runner_text_that_does_not_match_its_evidence(self) -> None:
        runner_path = "lmp_scripts_db/single_point/runsimulation.sh"
        input_path = "lmp_scripts_db/single_point/in.single_point"
        runner_text = "$LAMMPS_BIN -i in.single_point > out.dat\n"
        with self.assertRaisesRegex(ValueError, "hash does not match"):
            inspect_lammps_templates(
                simulation_settings=(
                    ObservedSetting(
                        key="lmps_sim_type",
                        values=("sp", "single_point"),
                        evidence_path="pyposmat.config",
                        line_number=1,
                    ),
                ),
                evidence_by_path={
                    runner_path: evidence(
                        runner_path, runner_text.replace("out.dat", "out.dax")
                    ),
                    input_path: evidence(input_path),
                },
                text_by_path={runner_path: runner_text},
            )

    def test_rejects_an_evidence_map_key_that_disagrees_with_the_evidence(self) -> None:
        runner_path = "lmp_scripts_db/single_point/runsimulation.sh"
        with self.assertRaisesRegex(ValueError, "evidence-map key"):
            inspect_lammps_templates(
                simulation_settings=(),
                evidence_by_path={runner_path: evidence("different/path")},
                text_by_path={},
            )


if __name__ == "__main__":
    unittest.main()
