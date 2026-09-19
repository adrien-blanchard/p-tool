# Maintenance notes

## 1.1.1 — September 2026

- Restore object visibility before selection after viewport captures. Previously, hidden objects could disappear from the restored selection.
- Add a real-window regression covering two PNG captures, selected/active objects, pre-hidden objects, overlays, render settings, overwrite refusal and recovery from a simulated render error.
- Run viewport tests under Xvfb in CI, in addition to the existing scene/export tests. Local regressions passed in Blender 5.0.1 and 5.2.0 LTS on Windows.

## 1.1.0 — September 2026

Maintenance release of the 2023 TOTB toolkit. The Gumroad archive remains linked in the README and has not been replaced.

- Load configuration relative to the installed package, not a hard-coded Windows add-on path.
- Restore selection after exports; join output paths correctly and refuse existing files.
- Handle unsaved projects, missing output folders, missing armatures and empty selections.
- Keep regular empties when localizing links; do not purge unrelated scene data.
- Restrict naming and cleanup to the selection. Keep positive vertex weights, including small weights.
- Correct keymap cleanup and reverse class unregistration; make scene edits undoable.
- Replace the bundled team roster with an optional initials field.

Tests run in factory-startup scenes and temporary folders. They cover register/unregister, repeated version saves, an actual FBX export, overwrite refusal, missing armatures, data-less objects, cleanup and preserved unrelated datablocks. Blender 5.0.1 and 5.2.0 LTS were exercised on Windows.

Complex production rigs still need artist review in a copied scene. There is no claim that every Blender version or studio rig has been tested. FBX batches can leave completed earlier outputs if a later item fails.

The thumbnail in the README is historical Gumroad artwork, not a screenshot of this maintenance version. The supplied source archive contains July–September 2023 timestamps; no Git history was backdated.
