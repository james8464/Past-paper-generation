# atomic one-slot model, not OS emulation. P sends A, sends B, then optionally closes; C
# receives three times. Blocked instructions keep their position and wake when
# conditions change. Closing keeps the slot; EOF requires an empty closed channel


# return status, delivered value and the slot after an atomic receive
def recevoir(case, ferme):
    if case is not None:
        return ("valeur", case, None)
    if ferme:
        return ("fin", None, None)
    return ("attente", None, None)


def simulate(schedule, *, close=True):
    if (
        type(schedule) is not list
        or len(schedule) > 64
        or any(type(actor) is not str or actor not in {"P", "C"} for actor in schedule)
        or type(close) is not bool
    ):
        raise ValueError("Use at most 64 P/C steps and a Boolean close flag")
    slot, closed = None, False
    positions = {"P": 0, "C": 0}
    blocked = set()
    received, trace = [], []
    producer_length = 3 if close else 2
    for actor in schedule:
        if actor in blocked:
            raise ValueError("Cannot schedule a blocked process")
        limit = producer_length if actor == "P" else 3
        if positions[actor] == limit:
            raise ValueError("Cannot schedule a terminated process")
        if actor == "P":
            if positions["P"] == 2:
                closed = True
                positions["P"] += 1
                blocked.discard("C")
                event = "close"
            elif slot is not None:
                blocked.add("P")
                event = "blocked full"
            else:
                slot = ["A", "B"][positions["P"]]
                positions["P"] += 1
                blocked.discard("C")
                event = f"send {slot}"
        elif slot is not None:
            event = f"receive {slot}"
            received.append(slot)
            slot = None
            positions["C"] += 1
            blocked.discard("P")
        elif closed:
            received.append(None)
            positions["C"] += 1
            event = "eof"
        else:
            blocked.add("C")
            event = "blocked empty"
        trace.append({
            "actor": actor, "event": event, "slot": slot, "closed": closed,
            "positions": [positions["P"], positions["C"]],
            "blocked": sorted(blocked),
        })
    return {"trace": trace, "received": received}
