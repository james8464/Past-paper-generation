# Bounded scheduling model for a new, not-yet-public French case.
#
# Arrivals during a slice join the queue before its unfinished process returns.
# This is an explicit teaching model, not a simulation of a real operating system.

from collections import deque
from copy import deepcopy


# Return nonempty CPU slices, finish times and the queue after each slice.
#
# Jobs are (name, arrival, CPU duration), sorted by arrival. Equal arrivals
# retain input order. There is no I/O or switching cost. New arrivals do not
# interrupt a slice. Intervals include their start and exclude their end.
def schedule(jobs, quantum):
    if type(quantum) is not int or not 1 <= quantum <= 16:
        raise ValueError("Quantum must be an integer from 1 to 16")
    if type(jobs) not in (list, tuple) or len(jobs) > 32:
        raise ValueError("At most 32 jobs are supported")
    names, previous_arrival = set(), -1
    for job in jobs:
        if type(job) not in (list, tuple) or len(job) != 3:
            raise ValueError("A job needs a name, arrival and duration")
        name, arrival, duration = job
        if (
            type(name) is not str
            or not name.strip()
            or len(name) > 32
            or name in names
            or type(arrival) is not int
            or not 0 <= arrival <= 100
            or arrival < previous_arrival
            or type(duration) is not int
            or not 1 <= duration <= 100
        ):
            raise ValueError("Invalid or unordered job")
        names.add(name)
        previous_arrival = arrival
    remaining = {name: duration for name, _, duration in jobs}
    ready, slices, queues, finished = deque(), [], [], {}
    next_job, time = 0, 0
    while ready or next_job < len(jobs):
        if not ready:
            time = max(time, jobs[next_job][1])
        while next_job < len(jobs) and jobs[next_job][1] <= time:
            ready.append(jobs[next_job][0])
            next_job += 1
        current = ready.popleft()
        end = time + min(quantum, remaining[current])
        remaining[current] -= end - time
        slices.append([current, time, end])
        time = end
        # A process arriving exactly at the boundary goes ahead of the one
        # whose quantum has just expired. The exercise states this convention.
        while next_job < len(jobs) and jobs[next_job][1] <= time:
            ready.append(jobs[next_job][0])
            next_job += 1
        if remaining[current]:
            ready.append(current)
        else:
            finished[current] = time
        queues.append(list(ready))
    return {"slices": slices, "finished": finished, "ready_after": queues}


# One structural family; a new seed does not mean a new question family.
def build_case(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("A signed 64-bit integer seed is required")
    jobs = [["A", 0, 5], ["B", 1, 3], ["C", 2, 1], ["D", 7, 2]]
    return deepcopy(
        {
            "family": "round_robin",
            "jobs": jobs,
            "quantum": 2,
            "baseline": schedule(jobs, 2),
            "revised": schedule(jobs, 1),
        }
    )
