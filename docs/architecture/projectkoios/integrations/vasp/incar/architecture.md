# INCAR I/O architecture

```mermaid
flowchart LR
    Authority["Official VASP INCAR format<br/>and evolving tag category"]
    Source["Plain-ASCII INCAR text"]
    Parser["IncarParser.parse()"]
    Record["IncarFile<br/>ordered immutable assignments"]
    Assignment["IncarAssignment<br/>normalized tag + lexical value"]
    Writer["IncarWriter.render()"]
    Normalized["Deterministic direct-tag<br/>INCAR text"]
    Calculator["VASP execution<br/>outside this I/O boundary"]

    Authority -. "syntax authority" .-> Parser
    Source --> Parser
    Parser --> Record
    Record -->|"contains"| Assignment
    Record --> Writer
    Writer --> Normalized
    Normalized -. "separately authorized staging" .-> Calculator
```

## Boundary

`IncarParser` validates bounded generic syntax but does not freeze the evolving VASP tag inventory, apply defaults, resolve duplicate tags, or determine tag compatibility. `IncarFile` and `IncarAssignment` are immutable data. `IncarWriter` normalizes syntax without filesystem access. Calculator staging, execution, OUTCAR inspection, numerical verification, and scientific validation remain separate operations.
