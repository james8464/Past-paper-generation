# French live diagnostic on installed release 182

One fresh, free local trial used the installed release at
`eec9eb463e0991b3dbc9d0bff423a5535404eb11`, public V36 route, Ollama
`gpt-oss:20b`, and seed `27011110`. It ended after 203.88 seconds with exit 1,
no completion event and no published PDF. This is a failed diagnostic, not a
qualification result. It was not retried or manually repaired.

| Pinned input | SHA-256 / digest |
| --- | --- |
| Installed backend | `70a2071752e2235c1760bc59c99aeb2d51b200a3569d2fb3e73b6ddaacd68cff` |
| French reference index | `36a1700d851ae23bc88b7315dbe456ce2591142f1aada6e7b82ee53e5425a71d` |
| Local model | `f38aa0c53da5f8c49d08c43a99df24ff53167fe68e24664a7777288e7656fdfe` |
| Retained recovery checkpoint | `41d13aa9e12b04027b454bfb4b7abe7ced8cf1d6f914a4232eec029b0bc48cf2` |

The returned third answer began with `from collections import defaultdict`.
That is legitimate Python syntax, not evidence of malicious access. It
nonetheless violates this route's explicit no-import display contract and was
correctly refused by its syntax policy. No model code was executed, and the
check was not weakened or bypassed. The error shown in the diagnostic was
“Fragment Python avec accès non autorisé”.

Independent inspection also found substantive mathematical errors. The
proposed seven-edge set cannot span nine vertices and contains a cycle. It
leaves R6 isolated and R8–R9 in a separate component. The correct eight-edge minimum spanning tree is
C8, C5, C3, C10, C6, C1, C7 and C4, with total weight 31, not the proposed 34.
The answer also wrongly classified R5–R6 as a cycle-forming edge. Its estimated
question timings totalled 35 minutes rather than the required 70. All four
verification entries were marked `human`; none constitutes observed teacher
review or learner calibration.

The backend, reference database and strict app signature were checked before
and after the run. The independent owner imposed a 1,950-second wall limit on
its own process group; that timeout was not reached. It did not change the
shared Ollama service. Evidence remains under
`tmp/nov6-final-app-acceptance/french-gptoss-installed182`, including the raw
response, event stream, pinned inputs and result. Full French/provider paper
quality remains unqualified. No every-page comparison is claimed when no PDF
was published.
