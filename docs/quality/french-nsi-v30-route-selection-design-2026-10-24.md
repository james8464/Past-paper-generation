# French NSI V30 route-selection design

The V29 comparison found repeated shortest-path calculations across E1 and E3. V30 retains the initial weighted-graph reasoning and the independent E3 routing/process/security case, but replaces E1's two repeated outage calculations with a connected filtering and selection task.

An original four-route catalogue uses the printed graph. Candidates calculate route costs and classify availability after each of two closures. A supplied helper defines undirected closure handling. Candidates then write a complete selector over arbitrary valid route/cost lists, retain the first minimum on ties, return `None` when no route remains, and justify the loop invariant. The question explicitly distinguishes the best listed route from a guaranteed global graph optimum. This is more than renaming a scenario or increasing page count.

The tree-construction task and E2 construction/invariant work remain. Three independent exercises, 18 technical points, a distinct 2-point language rubric and 70 indicative E1 minutes are preserved. Half a point moves from initial tracing to selection construction; tracing criteria are combined rather than discarded. These allocations remain uncalibrated.

Implementation is versioned. V13–V29 packages retain their old catalogue and replay paths. New deterministic facts bind the route list, costs, two availability vectors and selected index. Tests compare the trusted selector with an independent filtering/minimum oracle, including reversed closures, ties, empty/all-blocked lists and input preservation. No model code is executed. PDF checks bind public tables/helper source and reject solution leakage, missing credit and wrong phase placement.

After red/green tests, review dispatch and identity changes, refresh Graphify/inventory, freeze source, run a new pinned French diagnostic and inspect the subject/correction against relevant official progression. Record all attempts and limitations. Merge only through protected Backend/macOS checks. This change does not establish catalogue breadth, student timing, expert approval or model-independent equivalence.
