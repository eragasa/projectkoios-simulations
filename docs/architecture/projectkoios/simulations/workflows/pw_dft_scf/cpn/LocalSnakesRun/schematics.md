# `LocalSnakesRun` schematics

```text
typed event -> add_token(place)
                    |
                    v
              private marking
                    |
             drain_unique()
          /         |           no mode: stop   one: fire   many: reject
                    |
             maximum bound
```

Token reads return sorted tuples detached from the mutable SNAKES multiset.
