import Lake
open Lake DSL

package «NUProof» where
  -- Package metadata (version field removed for Lean 4.3.0 compatibility)

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.14.0"

@[default_target]
lean_lib «NUProof» where
  -- Library configuration
  roots := #[`NUProof]
