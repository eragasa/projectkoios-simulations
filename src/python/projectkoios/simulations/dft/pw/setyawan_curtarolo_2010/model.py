"""Citation identity and Appendix-A lattice names."""

from enum import StrEnum

SETYAWAN_CURTAROLO_CONVENTION_NAME = "Setyawan-Curtarolo"
SETYAWAN_CURTAROLO_REVISION = "2010 Appendix A"
SETYAWAN_CURTAROLO_DOI = "10.1016/j.commatsci.2010.05.010"
SETYAWAN_CURTAROLO_CITATION = (
    "W. Setyawan and S. Curtarolo, Computational Materials Science 49 "
    "(2010) 299-312, doi:10.1016/j.commatsci.2010.05.010"
)


class SetyawanCurtaroloBravaisLattice(StrEnum):
    """Name one of the 14 Bravais lattices using its Pearson lattice code."""

    cubic_primitive = "cP"
    cubic_face_centered = "cF"
    cubic_body_centered = "cI"
    tetragonal_primitive = "tP"
    tetragonal_body_centered = "tI"
    orthorhombic_primitive = "oP"
    orthorhombic_face_centered = "oF"
    orthorhombic_body_centered = "oI"
    orthorhombic_base_centered = "oS"
    hexagonal_primitive = "hP"
    rhombohedral = "hR"
    monoclinic_primitive = "mP"
    monoclinic_base_centered = "mS"
    triclinic_primitive = "aP"


class SetyawanCurtaroloAppendixACase(StrEnum):
    """Name one band-path case defined by Appendix A."""

    cub = "CUB"
    fcc = "FCC"
    bcc = "BCC"
    tet = "TET"
    bct1 = "BCT1"
    bct2 = "BCT2"
    orc = "ORC"
    orcf1 = "ORCF1"
    orcf2 = "ORCF2"
    orcf3 = "ORCF3"
    orci = "ORCI"
    orcc = "ORCC"
    hex = "HEX"
    rhl1 = "RHL1"
    rhl2 = "RHL2"
    mcl = "MCL"
    mclc1 = "MCLC1"
    mclc2 = "MCLC2"
    mclc3 = "MCLC3"
    mclc4 = "MCLC4"
    mclc5 = "MCLC5"
    tri1a = "TRI1a"
    tri1b = "TRI1b"
    tri2a = "TRI2a"
    tri2b = "TRI2b"
