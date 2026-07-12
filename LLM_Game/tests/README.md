# LLM_Game tests

Initial Nitro tests for the recovered perception-oriented LLM game engine idea.

`llama8b_structured_output_smoke.py` calls the local Nitro llama.cpp server on `/completion` with a closed JSON schema. The schema follows the infra constraint-decoding guideline where practical: object root, closed objects, required fields, no raw GBNF, no generic JSON mode. For local llama.cpp the request uses the `/completion` `json_schema` field, because the devtests local llama.cpp experiments show that endpoint is the reliable path for schema enforcement.

`llama8b_strict_named_contract_smoke.py` uses named closed objects instead of variable-length arrays so the schema itself can enforce exactly two objects, one unresolved exit, one return exit, and enum-constrained affordances/directions.
