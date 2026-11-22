import Lake
open Lake DSL

package «TopoSpine» where
  -- leanOptions := #[]

-- `lake build` must build the whole library (a bare `lean_lib` without a default
-- target silently built nothing in Loops 1-2; fixed in Loop 3).
@[default_target]
lean_lib «TopoSpine» where
  -- root := `TopoSpine
