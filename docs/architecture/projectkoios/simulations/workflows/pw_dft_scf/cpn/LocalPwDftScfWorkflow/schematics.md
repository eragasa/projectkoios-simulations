# `LocalPwDftScfWorkflow` schematics

```text
pending_actions() -> Register / Submit / Analyze action
                           |
                    external handler
                           |
                           v
accept(typed event) -> place mapping -> bounded internal drain
                           |
                 status() / outcome()
```

Unsupported event types are rejected before token insertion. A terminal marking
projects to `terminated` and contains exactly one success or failure outcome.
