# Explicit blocking, retry and EOF traces for a one-slot teaching model.

import pytest


@pytest.mark.parametrize(
    "slot,closed,expected",
    [
        ("A", False, ("valeur", "A", None)),
        ("B", True, ("valeur", "B", None)),
        (None, True, ("fin", None, None)),
        (None, False, ("attente", None, None)),
    ],
)
def test_receive_distinguishes_value_eof_and_waiting(slot, closed, expected):
    from Backend.Core.france.channel_case import recevoir

    assert recevoir(slot, closed) == expected


def test_blocked_instructions_retry_without_advancing_the_program():
    from Backend.Core.france.channel_case import simulate

    result = simulate(["P", "P", "C", "C", "P", "C", "P", "C"])
    assert result["received"] == ["A", "B", None]
    assert result["trace"] == [
        {
            "actor": "P",
            "event": "send A",
            "slot": "A",
            "closed": False,
            "positions": [1, 0],
            "blocked": [],
        },
        {
            "actor": "P",
            "event": "blocked full",
            "slot": "A",
            "closed": False,
            "positions": [1, 0],
            "blocked": ["P"],
        },
        {
            "actor": "C",
            "event": "receive A",
            "slot": None,
            "closed": False,
            "positions": [1, 1],
            "blocked": [],
        },
        {
            "actor": "C",
            "event": "blocked empty",
            "slot": None,
            "closed": False,
            "positions": [1, 1],
            "blocked": ["C"],
        },
        {
            "actor": "P",
            "event": "send B",
            "slot": "B",
            "closed": False,
            "positions": [2, 1],
            "blocked": [],
        },
        {
            "actor": "C",
            "event": "receive B",
            "slot": None,
            "closed": False,
            "positions": [2, 2],
            "blocked": [],
        },
        {
            "actor": "P",
            "event": "close",
            "slot": None,
            "closed": True,
            "positions": [3, 2],
            "blocked": [],
        },
        {
            "actor": "C",
            "event": "eof",
            "slot": None,
            "closed": True,
            "positions": [3, 3],
            "blocked": [],
        },
    ]


def test_close_does_not_discard_an_unread_value():
    from Backend.Core.france.channel_case import simulate

    result = simulate(["P", "C", "P", "P", "C", "C"])
    assert result["received"] == ["A", "B", None]
    assert result["trace"][3]["slot"] == "B"
    assert result["trace"][3]["closed"] is True


def test_missing_close_leaves_receiver_waiting_instead_of_inventing_eof():
    from Backend.Core.france.channel_case import simulate

    result = simulate(["P", "C", "P", "C", "C"], close=False)
    assert result["received"] == ["A", "B"]
    assert result["trace"][-1]["blocked"] == ["C"]
    assert result["trace"][-1]["positions"] == [2, 2]


def test_scheduling_blocked_or_terminated_process_is_refused():
    from Backend.Core.france.channel_case import simulate

    with pytest.raises(ValueError, match="blocked"):
        simulate(["C", "C"])
    with pytest.raises(ValueError, match="terminated"):
        simulate(["P", "C", "P", "P", "P"])


@pytest.mark.parametrize("schedule", [["X"], [True], "PC", ["P"] * 65])
def test_invalid_or_unbounded_schedule_is_refused(schedule):
    from Backend.Core.france.channel_case import simulate

    with pytest.raises(ValueError):
        simulate(schedule)
