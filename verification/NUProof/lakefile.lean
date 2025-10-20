import Lake
open Lake DSL

package «NUProof» where
  -- Package metadata (updated for Lean 4.14.0 and mathlib compatibility)

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.14.0"

@[default_target]
lean_lib «NUProof» where
  -- Library source directory contains all proof modules
  srcDir := "NUProof"
