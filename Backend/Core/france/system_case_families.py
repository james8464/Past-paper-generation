# Original E3 systems cases for the unreleased V32 assessment.
#
# These are explicit teaching models, not simulations of complete Internet
# protocols. Application algorithms are cross-checked against separate bounded
# walk, reachability and prefix-history oracles. No model code is executed.

import json
from copy import deepcopy
from hashlib import sha256

VERSION = "fr-nsi-system-cases-v1"
FAMILIES = ("routing", "locks", "delivery")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _adjacency(links, nodes):
    adjacent = {node: [] for node in nodes}
    seen = set()
    for left, right, cost in links:
        edge = tuple(sorted((left, right)))
        if (
            left not in adjacent
            or right not in adjacent
            or left == right
            or type(cost) is not int
            or cost <= 0
            or edge in seen
        ):
            raise ValueError("Invalid undirected link")
        seen.add(edge)
        adjacent[left].append((right, cost))
        adjacent[right].append((left, cost))
    return adjacent


# One synchronous distance-vector round; None means unreachable.
#
# All neighbours advertise the previous round, including obsolete estimates.
# This deliberately omits split horizon and poison reverse. Positive integer
# costs are supplied. The destination advertises zero every round.
def distance_round(links, previous, destination):
    if destination not in previous or previous[destination] != 0:
        raise ValueError("Missing destination")
    if any(v is not None and (type(v) is not int or v < 0) for v in previous.values()):
        raise ValueError("Invalid advertised distance")
    adjacent = _adjacency(links, previous)
    result = {}
    for node in previous:
        costs = [
            cost + previous[other]
            for other, cost in adjacent[node]
            if previous[other] is not None
        ]
        result[node] = 0 if node == destination else min(costs, default=None)
    return result


# Return cycle members, not processes merely blocked behind a cycle.
#
# Each resource has one owner; each process requests at most one resource.
# A process cannot acquire a resource it already owns (non-reentrant locks).
# A missing owner means a free resource, so that request has no wait edge.
def deadlocked_processes(owners, waiting):
    cycles = set()
    for process in waiting:
        path = []
        current = process
        while current in waiting:
            if current in path:
                cycles.update(path[path.index(current) :])
                break
            path.append(current)
            current = owners.get(waiting[current])
            if current is None:
                break
    return sorted(cycles)


# Application reassembly of positive numbered messages, beginning at 1.
#
# Events are [nonnegative time, positive sequence, string payload], sorted by
# time; equal times retain input order. Identical duplicates are ignored even
# after delivery. Conflicting duplicates are rejected. This is not TCP.
def delivery_trace(events):
    seen, buffer, trace = {}, {}, []
    next_number, last_time = 1, -1
    for time, number, payload in events:
        if (
            type(time) is not int
            or time < last_time
            or time < 0
            or type(number) is not int
            or number < 1
            or type(payload) is not str
        ):
            raise ValueError("Invalid delivery event")
        last_time = time
        if number in seen and seen[number] != payload:
            raise ValueError("Conflicting duplicate")
        duplicate = number in seen
        if not duplicate:
            seen[number] = payload
            buffer[number] = payload
        emitted = []
        while next_number in buffer:
            emitted.append(buffer.pop(next_number))
            next_number += 1
        trace.append(
            dict(
                time=time,
                next=next_number,
                buffer=sorted(buffer),
                emitted=emitted,
                duplicate=duplicate,
            )
        )
    return trace


# One non-preemptive consumer; [arrival, identifier, duration] in FIFO order.
def fifo_jobs(arrivals):
    clock, last_arrival, result = 0, -1, []
    for arrival, identifier, duration in arrivals:
        if (
            type(arrival) is not int
            or arrival < 0
            or arrival < last_arrival
            or type(duration) is not int
            or duration < 1
        ):
            raise ValueError("Invalid FIFO job")
        start = max(clock, arrival)
        clock = start + duration
        result.append(dict(message=identifier, start=start, end=clock))
        last_arrival = arrival
    return result


# Tick-by-tick server, independent of the max/start recurrence.
def _fifo_oracle(arrivals):
    pending = list(arrivals)
    result, time, queue = [], 0, []
    running, remaining, start = None, 0, 0
    while pending or queue or running is not None:
        if running is not None and remaining == 0:
            result.append(dict(message=running, start=start, end=time))
            running = None
        while pending and pending[0][0] <= time:
            queue.append(pending.pop(0))
        if running is None and queue:
            _, running, remaining = queue.pop(0)
            start = time
        if running is not None:
            remaining -= 1
        time += 1
    return result


def _checked_jobs(arrivals):
    jobs = fifo_jobs(arrivals)
    if jobs != _fifo_oracle(arrivals):
        raise ValueError("FIFO oracle disagreement")
    return jobs


# Expand walks of exactly r edges, stopping at destination immediately.
#
# A walk's final node supplies its initial advertisement. Keeping obsolete
# endpoint values is intentional: a transient route is not a shortest path.
def _walk_oracle(links, initial, destination, rounds):
    result = {}
    for start in initial:
        walks = [(start, 0)]
        completed = []
        for _ in range(rounds):
            following = []
            for node, cost in walks:
                if node == destination:
                    completed.append(cost)
                    continue
                for left, right, weight in links:
                    if node == left:
                        following.append((right, cost + weight))
                    elif node == right:
                        following.append((left, cost + weight))
            walks = following
        completed.extend(
            cost + initial[node] for node, cost in walks if initial[node] is not None
        )
        result[start] = min(completed, default=None)
    return result


# Transitive closure: a process belongs to a cycle iff it reaches itself.
def _cycle_oracle(owners, waiting):
    nodes = sorted(set(waiting) | set(owners.values()))
    reach = {
        (p, owners[resource]) for p, resource in waiting.items() if resource in owners
    }
    for middle in nodes:
        reach |= {
            (left, right)
            for left in nodes
            for right in nodes
            if (left, middle) in reach and (middle, right) in reach
        }
    return sorted(p for p in nodes if (p, p) in reach)


# Recompute the available prefix from every complete event-history slice.
def _delivery_oracle(events):
    output = []
    previous_prefix = 0
    for index, (time, number, _) in enumerate(events):
        history = events[: index + 1]
        values = {n: text for _, n, text in history}
        prefix = 0
        while prefix + 1 in values:
            prefix += 1
        output.append(
            dict(
                time=time,
                next=prefix + 1,
                buffer=sorted(n for n in values if n > prefix),
                emitted=[values[n] for n in range(previous_prefix + 1, prefix + 1)],
                duplicate=any(n == number for _, n, _ in events[:index]),
            )
        )
        previous_prefix = prefix
    return output


def _routing():
    links = [["A", "B", 1], ["B", "D", 1], ["A", "C", 2], ["B", "C", 1], ["C", "D", 2]]
    baseline = {"A": 2, "B": 1, "C": 2, "D": 0}
    surviving = [edge for edge in links if edge[:2] != ["B", "D"]]
    current = dict(baseline)
    states = [dict(round=0, distances=dict(current))]
    for count in range(1, 4):
        current = distance_round(surviving, current, "D")
        if current != _walk_oracle(surviving, baseline, "D", count):
            raise ValueError("Routing oracle disagreement")
        states.append(dict(round=count, distances=dict(current)))
    # Enumerate all simple paths independently for the converged cost.
    costs = []
    pending = [("A", ["A"], 0)]
    while pending:
        node, path, cost = pending.pop()
        if node == "D":
            costs.append(cost)
        else:
            for left, right, weight in surviving:
                other = right if left == node else left if right == node else None
                if other is not None and other not in path:
                    pending.append((other, [*path, other], cost + weight))
    if states[-1]["distances"]["A"] != min(costs):
        raise ValueError("Converged route oracle disagreement")
    arrival = 2 + min(costs)
    job = _checked_jobs([[arrival, "mesures", 2]])[0]
    report_arrival = job["end"] + 1
    return dict(
        title="Une panne et des annonces périmées",
        links=links,
        failed_link=["B", "D"],
        initial=baseline,
        destination="D",
        tie_rule="À coût égal, choisir le voisin de nom alphabétiquement premier.",
        emission=2,
        processing=2,
        report_delay=1,
        report_deadline=8,
    ), dict(
        states=states,
        final_cost=min(costs),
        arrival=arrival,
        process_end=job["end"],
        report_arrival=report_arrival,
        report_on_time=report_arrival <= 8,
    )


def _locks():
    owners = {"scanner": "P", "cache": "Q", "journal": "R"}
    waiting = {"P": "cache", "Q": "scanner", "R": "scanner", "S": "journal"}
    states = []
    for label, held, requests in (
        ("S0", owners, waiting),
        (
            "S1",
            {r: p for r, p in owners.items() if p != "Q"},
            {p: r for p, r in waiting.items() if p != "Q"},
        ),
        ("S2", {"journal": "R"}, {"R": "scanner", "S": "journal"}),
    ):
        actual = deadlocked_processes(held, requests)
        if actual != _cycle_oracle(held, requests):
            raise ValueError("Lock-cycle oracle disagreement")
        states.append(dict(label=label, owners=held, waiting=requests, cycle=actual))
    jobs = _checked_jobs([[4, "P", 3], [4, "R", 2], [4, "S", 1]])
    response_arrival = jobs[-1]["end"] + 2
    return dict(
        title="Un service bloqué sans panne de liaison",
        owners=owners,
        waiting=waiting,
        abort="Q",
        recovery_at=4,
        durations={"P": 3, "R": 2, "S": 1},
        schedule=["P", "R", "S"],
        response_delay=2,
        deadline=11,
    ), dict(
        states=states,
        cycle=["P", "Q"],
        followers=["R", "S"],
        finishes={job["message"]: job["end"] for job in jobs},
        response_arrival=response_arrival,
        response_on_time=response_arrival <= 11,
    )


def _delivery():
    events = [
        [0, 2, "B"],
        [1, 2, "B"],
        [3, 1, "A"],
        [4, 4, "D"],
        [6, 3, "C"],
        [7, 1, "A"],
    ]
    states = delivery_trace(events)
    if states != _delivery_oracle(events):
        raise ValueError("Delivery oracle disagreement")
    # One non-preemptive FIFO consumer, two time units per emitted message.
    jobs = _checked_jobs(
        [
            [state["time"], message, 2]
            for state in states
            for message in state["emitted"]
        ]
    )
    clock = jobs[-1]["end"]
    return dict(
        title="Des messages reçus mais pas encore exploitables",
        events=events,
        service_time=2,
        acknowledge_delay=1,
        deadline=11,
    ), dict(
        states=states,
        jobs=jobs,
        acknowledgement=clock + 1,
        acknowledged_on_time=clock + 1 <= 11,
    )


def build_case(seed):
    if type(seed) is not int:
        raise ValueError("Integer system case seed required")
    family = FAMILIES[(seed - 270100) % len(FAMILIES)]
    public, expected = {"routing": _routing, "locks": _locks, "delivery": _delivery}[
        family
    ]()
    data = dict(
        version=VERSION, seed=seed, family=family, public=public, expected=expected
    )
    data["sha256"] = sha256(_canonical(data).encode()).hexdigest()
    return deepcopy(data)


def verify_case(case):
    try:
        return _canonical(case) == _canonical(build_case(case["seed"]))
    except (ValueError, TypeError, KeyError):
        return False
