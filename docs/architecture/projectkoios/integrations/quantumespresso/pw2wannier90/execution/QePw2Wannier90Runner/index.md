# `QePw2Wannier90Runner`

`run(request)` verifies the executable, `.nnkp`, manifest, and every selected
saved-state file before creating the output directory. It can render without
execution. Explicitly authorized execution stages only manifest-selected files,
retains the exact parent saved-state manifest, invokes `pw2wannier90.x`, and
writes exact input and artifact manifests.
