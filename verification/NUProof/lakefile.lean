import Lake
open Lake DSL

package «NUProof» where
  -- Package metadata
  version := v!"0.1.0"

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"

@[default_target]
lean_lib «NUProof» where
  -- Library configuration
  roots := #[`NUProof]
