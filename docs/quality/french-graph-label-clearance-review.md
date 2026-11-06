# Graph-label clearance and retained print policies

An owned four-node directed graph reproduced a presentation defect: the opaque
background for weight 11 on A to C covered part of B to D, making the weight look
attached to the wrong connection. Normal and enlarged figures were affected.
The existing vector check accepted the retained lines and label origins; those
checks alone did not establish visual separation.

The new graph option precomputes the complete connection geometry before placing
labels. Each bounded candidate must clear foreign segments and arrow triangles,
including stroke clearance. Candidates remain at the existing perpendicular
offset beside their own edge, within its existing search fractions. If none fits,
the existing bounded congestion refusal applies. No edge, weight, answer, mark,
font size or node is rewritten to make a figure pass.

Current V36 printing uses `fr-nsi-v36-model-review-v4`. Retained v2 and v3 use the
original geometry. V3 retains its inline prose and fenced-code treatment through
an explicit policy set; the renderer and PDF validator choose the same geometry
option. Current packages cannot claim the previous print policy.

## Evidence

- The graph author read the original 201-line module and final 311-line module
  through EOF. Root reviewed the geometry delta and complete new geometry tests.
- Owned before/after normal and enlarged figures show the misplaced label moved
  beside its own connection. Uncongested controls retain identical page rasters.
- Geometry controls cover crossings, finite segments, triangle intersection,
  stroke clearance, own-edge association and unchanged legacy geometry.
- Root policy tests cover current/retained inline grammar and matching renderer
  and validator options. An initial test incorrectly expected Markdown bold;
  it was corrected to the established underline/backtick grammar, without adding
  syntax or changing production behavior.
- Separate baseline/current v3 rendering produced eight owned PDFs. All 36 page
  pairs match in complete 100-dpi RGB rasters and extracted text, including normal
  and enlarged subjects and corrections. No footer or other region was excluded.
  The earlier literal-asterisk comparison remains as superseded evidence.

This is a source-bound geometry and print-compatibility repair. The owned
fixtures are not live AI papers, official-paper equivalence, calibrated demand
or learner timing. The large shared renderer received a scoped delta review,
not a new whole-file audit.
