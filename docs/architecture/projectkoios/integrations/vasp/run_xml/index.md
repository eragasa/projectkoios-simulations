# `vasprun.xml` data

`VaspRunXmlParser` performs bounded incremental `xml.etree.ElementTree.iterparse`
extraction and clears each completed top-level element. It rejects DTD/entity
declarations and oversized input before parsing.

`VaspRunXmlData` retains:

- generator program and version;
- `IBRION`, `NSW`, and `ISIF` mode values;
- atom labels;
- initial and final structures;
- k-points and integration weights;
- every ionic `calculation` and all nested electronic iterations;
- free, entropy-free, and sigma-to-zero energies in eV;
- forces in eV/Å and stress in kbar;
- final eigenvalues in eV, occupations, and optional Fermi energy in eV.

The parser preserves native source order and units. It does not merge XML data
with `OUTCAR`, `CONTCAR`, process streams, or execution records.

Native format references:

- [vasprun.xml](https://www.vasp.at/wiki/index.php/Vasprun.xml)
- [OUTCAR](https://www.vasp.at/wiki/index.php/OUTCAR)
- [ISIF](https://www.vasp.at/wiki/index.php/ISIF)
