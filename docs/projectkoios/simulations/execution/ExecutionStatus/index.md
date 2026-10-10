# `ExecutionStatus`

Terminal process-attempt classification. `succeeded` records return code zero; `failed` records a nonzero return code; `failed_preflight` records an unavailable required input before process launch; `failed_to_start` records an operating-system launch failure; `failed_to_terminate` records failure of bounded process-group cleanup after launch; `failed_output` records a retained-stream failure; `timed_out` records expiration of the explicit timeout. A live-emission failure does not reclassify the process attempt.
