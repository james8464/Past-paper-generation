"""Original, source-comparable topic-bank tasks. Full-paper templates are untouched.

Tariffs/AOs describe the actual work, not a scaled whole-paper target. Source
comparability is independently checked by Backend.Core.topic_reference_evidence.
"""
from __future__ import annotations

import random

from cspapergen.models import MarkingGuidance, Question, QuestionPart, Stimulus


def _part(label, marks, prompt, points, operation, ao="AO1", answers=None, options=None, dependency="self-contained"):
    part = QuestionPart(
        label=str(label), marks=marks, prompt=prompt, answer_lines=max(4, marks * 2),
        task_operation=operation, assessment_objectives={ao: marks},
        reference_source_dependency=dependency,
        marking=MarkingGuidance(ao=ao, points=points), options=options or [],
    )
    if answers:
        part.set_closed_answers({key: [value] for key, value in answers.items()})
    return part


def _question(number, topic, style, title, stem, parts, code=None):
    return Question(number=number, topic_id=topic, style_id=style, title=title,
                    stem=stem, parts=parts,
                    stimulus=Stimulus(kind="code", title="Task data", code=code) if code else None)


def build_reference_bank_questions(topic: str, rng: random.Random) -> list[Question]:
    if topic == "4.2":
        nodes = sorted(rng.sample(range(10, 90), 7))
        a, b, c = nodes[1], nodes[3], nodes[5]
        return [
            _question(1, topic, "data_structures_stack_queue", "Circular queues", "A fixed-capacity circular queue uses an array, a front pointer and a count.", [
                _part(1, 4, "Describe a safe dequeue operation for this circular queue, including how an empty queue is handled.", ["Check whether count is zero; report underflow without reading/removing an item.", "Otherwise return the item at the front index.", "Advance front by one, wrapping modulo the array capacity.", "Decrease count by one; the new front identifies the next available item."], "describe"),
                _part(2, 2, "Explain why a circular queue can use a fixed array more effectively than a linear queue.", ["Positions freed at the beginning can be reused after the rear wraps.", "This avoids a false full condition at the final index or shifting existing items."], "explain"),
            ]),
            _question(2, topic, "data_structures_hash", "Hash-table insertion and load", "Integer keys are stored in a fixed-size hash table with linear probing.", [
                _part(1, 4, "Describe how to insert a new key into a hash table using linear probing. Include collision handling and the full-table case.", ["Apply the hash function to obtain the initial index.", "If occupied, inspect successive indices with wraparound until an empty slot is found.", "Store the key at that empty slot.", "Detect that all slots have been checked and report a full table rather than looping forever."], "describe"),
                _part(2, 2, "Explain why a hash table that is almost full can have slow insertion and search operations.", ["Collisions produce long clusters of occupied slots.", "Many probes may be needed, approaching linear rather than expected constant-time access."], "explain"),
            ]),
            _question(3, topic, "data_structures_tree", "Tree structure and traversal", "A rooted binary tree is supplied as parent/child links. A missing link is marked none.", [
                _part(1, 2, "State two characteristics that distinguish a binary tree from an arbitrary graph.", ["There is a designated root and no cycles, with every other node having one parent.", "Each node has at most two children."], "retrieve"),
                _part(2, 2, "State the in-order traversal of the supplied tree.", ["Visit the left subtree, then its parent, then the right subtree.", f"The order is {', '.join(map(str, nodes))}."], "analyse", "AO2", {f"visit-{i}":str(v) for i,v in enumerate(nodes, 1)}),
                _part(3, 2, "Describe the shape of a binary tree that would require a traversal's stack capacity to equal the number of nodes when descending left links before visiting nodes.", ["Every node except the last has only a left child, producing a single left chain.", "The descent stores every node before any node is removed/visited."], "analyse", "AO2"),
            ], f"Root: {b}\nNode {b}: left={a}, right={c}\nNode {a}: left={nodes[0]}, right={nodes[2]}\nNode {c}: left={nodes[4]}, right={nodes[6]}\nAll other nodes have no children."),
            _question(4, topic, "data_structures_graph", "Graph representations", "An undirected graph has vertices A, B, C and D. Each listed edge joins two distinct vertices.", [
                _part(1, 2, "Complete an adjacency matrix for this graph using the vertex order A, B, C, D. Use 1 for an edge and 0 otherwise.", ["Rows A and B are 0,1,0,1 and 1,0,1,0.", "Rows C and D are 0,1,0,1 and 1,0,1,0; the matrix is symmetric."], "represent", "AO2", {"row-A":"0,1,0,1","row-B":"1,0,1,0","row-C":"0,1,0,1","row-D":"1,0,1,0"}),
                _part(2, 2, "State two reasons why these graph properties do not define a tree: the graph contains a cycle and an additional isolated vertex E is then introduced.", ["The cycle violates the acyclic requirement for a tree.", "The isolated vertex makes the extended graph disconnected."], "analyse", "AO2"),
                _part(3, 2, "Complete the adjacency matrix after adding isolated vertex E to the graph by stating its new row E and new column E, including the diagonal.", ["All five entries of row E are zero.", "All five entries of column E are zero because E is isolated."], "represent", "AO2", {"row-E":"0,0,0,0,0","column-E":"0,0,0,0,0"}),
            ], "Edges: A-B, B-C, C-D, D-A"),
            _question(5, topic, "data_structures_choice", "Storage and stacks", "A queue and a stack support a service whose workload varies. Dynamically linked implementations use references between nodes; static alternatives reserve array capacity.", [
                _part(1, 2, "Explain how a stack can reverse the order of all items in a queue.", ["Dequeue each item and push it onto the stack.", "Pop all items and enqueue them; LIFO produces the reverse of the original queue order."], "explain"),
                _part(2, 4, "Discuss the advantages and disadvantages of dynamic data structures compared with static data structures.", ["Dynamic allocation can grow as needed without reserving unused maximum capacity.", "Unused storage can be released as the workload shrinks.", "Linked implementations require extra storage for references and may have slower direct access than arrays.", "Allocation/deallocation adds overhead and unreleased storage can cause memory leaks; weigh these costs against flexible capacity."], "judge"),
            ]),
        ]
    if topic == "4.10":
        from cspapergen.question_bank import QUESTION_STYLES, build_question
        # Keep the independently executable SELECT/INSERT intents and original
        # scenario, but put the previously unsupported DELETE into error analysis.
        style = next(s for s in QUESTION_STYLES if s.id == "sql_normalisation")
        sql = build_question(style, 1, 12, rng)
        selected = sql.parts[1].model_copy(deep=True)
        selected.label = "1"
        selected.marks = 5
        selected.task_operation = "program"
        selected.assessment_objectives = {"AO2":3,"AO3":2}
        selected.marking.points = ["Join SESSION to BOOKING on SessionID.", "Select Activity and COUNT(*).", "Group by Activity.", "Use HAVING COUNT(*) >= 5.", "Sort COUNT(*) descending."]
        inserted = sql.parts[2].model_copy(deep=True)
        inserted.label = "2"
        inserted.assessment_objectives = {"AO3":2}
        inserted.task_operation = "program"
        updated = sql.parts[3].model_copy(deep=True)
        updated.label = "3"
        updated.assessment_objectives = {"AO3":3}
        updated.task_operation = "program"
        deleted = _part(4, 2, "Describe two errors in this DELETE statement intended to remove only unattended bookings for session 27:\nDELETE FROM BOOKING, SESSION WHERE SessionID = 27 OR Attended = FALSE;", ["DELETE must target BOOKING only, not two tables.", "Use AND, not OR, so both session and attendance restrictions apply."], "analyse", "AO2")
        sql.parts = [selected, inserted, updated, deleted]
        return [sql,
            _question(2, topic, "erd_keys", "Relationships, keys and redundancy", "Each member may make many bookings. Each session may have many bookings. A booking belongs to exactly one member and one session; members may rebook the same session after cancellation.", [
                _part(1, 2, "Draw an entity-relationship diagram showing MEMBER, BOOKING and SESSION, and label both relationships with their degrees.", ["MEMBER one-to-many BOOKING.", "SESSION one-to-many BOOKING; no direct many-to-many link is needed once BOOKING resolves it."], "represent", "AO2"),
                _part(2, 2, "Describe the limitation of using the composite primary key (MemberID, SessionID) when all booking attempts, including cancelled attempts, must be retained.", ["A second booking by the same member for the same session repeats the key.", "It cannot be stored separately; a BookingID or attempt identifier is needed."], "analyse", "AO2"),
                _part(3, 2, "Describe two problems that can occur when a database is not fully normalised.", ["Repeated facts can become inconsistent when only some copies are updated.", "Insertion/deletion anomalies can prevent storing a fact independently or remove an unrelated fact."], "describe"),
                _part(4, 2, "Describe one advantage and one disadvantage of an additional redundant Activity field in BOOKING when SESSION already stores the activity for each session.", ["Queries about bookings can obtain the activity without joining SESSION.", "Changing an activity requires consistent updates to every redundant copy, otherwise conflicting values arise."], "analyse", "AO2"),
            ], "MEMBER(MemberID, FullName)\nSESSION(SessionID, Activity)\nBOOKING(MemberID, SessionID, Attended)"),
            _question(3, topic, "database_extended", "Relational design and concurrent access", "A workshop provider records clients and their registrations. A client has a unique ClientID, name and email. Each registration has a unique RegistrationID, one client, and a booking date. A registration may include several workshops; each workshop has a unique WorkshopID and title. Record the number of places reserved on each registration/workshop combination.", [
                _part(1, 5, "Develop a fully normalised relational design by giving the three additional relations needed besides WORKSHOP(WorkshopID, Title). List their attributes, identify primary keys, and identify foreign keys.", ["CLIENT(ClientID, Name, Email), primary key ClientID.", "REGISTRATION(RegistrationID, ClientID, BookingDate), primary key RegistrationID.", "REGISTRATION_LINE(RegistrationID, WorkshopID, Places).", "The line relation has composite primary key (RegistrationID, WorkshopID).", "Foreign keys: REGISTRATION.ClientID, LINE.RegistrationID and LINE.WorkshopID reference their corresponding parent relations."], "represent", "AO2", dependency="task-context"),
                _part(2, 3, "Write a CREATE TABLE statement for WORKSHOP with integer WorkshopID as its primary key, a text Title up to 80 characters, and an integer Capacity.", ["WorkshopID INTEGER PRIMARY KEY.", "Title VARCHAR(80) and Capacity INTEGER.", "CREATE TABLE WORKSHOP (...) with correct separators and complete syntax."], "program", "AO3"),
                _part(3, 2, "Describe how simultaneous updates to the same database record can cause a lost update when concurrent access is unmanaged.", ["Two users read the same original value and compute different updates.", "The later write overwrites the earlier write, losing one user's change."], "describe"),
            ]),
        ]
    if topic == "4.12":
        x, y, z = rng.sample(range(2, 10), 3)
        filtered = [v for v in (x, y, z) if v > 4]
        filtered_answer = ",".join(map(str, filtered)) if filtered else "[]"
        return [
            _question(1, topic, "functional_programming", "Higher-order list processing", "The functions below are pure. map applies its function to each item; fold combines a list using the given initial value.", [
                _part(1, 4, "Complete a trace table giving the result of each call: filtered values; mapped values; total values; total (mapped values).", [f"filtered values = {filtered}.", f"mapped values = [{2*x}, {2*y}, {2*z}].", f"total values = {x+y+z}.", f"total (mapped values) = {2*(x+y+z)}."], "trace", "AO2", {"filtered-values":filtered_answer,"mapped-values":f"{2*x},{2*y},{2*z}","total-values":str(x+y+z),"total-mapped":str(2*(x+y+z))}),
                _part(2, 2, "Explain what makes a function a higher-order function.", ["It accepts a function as an argument.", "It can instead or additionally return a function as a result."], "explain"),
                _part(3, 2, "Describe partial function application.", ["Fix some, but not all, arguments of a function.", "The result is a new function taking the remaining arguments."], "describe"),
            ], f"values = [{x}, {y}, {z}]\ndouble n = 2 * n\nfiltered xs = filter (>4) xs\nmapped xs = map double xs\ntotal xs = fold (+) 0 xs"),
            _question(2, topic, "functional_recursion", "Recursive accumulation", "In the functional code below, [] is empty and (x:xs) splits a list into head x and tail xs.", [
                _part(1, 3, f"Complete a trace table showing the argument and returned value for every call when total [{x}, {y}, {z}] is evaluated.", [f"Arguments are [{x},{y},{z}], [{y},{z}], [{z}], [].", f"Returned values in call order are {x+y+z}, {y+z}, {z}, 0.", "The empty-list base case is reached and returned values accumulate while calls unwind."], "trace", "AO2", {"arguments":f"[{x},{y},{z}];[{y},{z}];[{z}];[]","returns":f"{x+y+z},{y+z},{z},0"}),
                _part(2, 3, "Describe how the recursive total function processes the list, including its termination condition.", ["It separates the current list into head and tail.", "It adds the head to a recursive call on the tail.", "The empty list returns zero, stopping further recursion."], "analyse", "AO2"),
                _part(3, 1, "State the purpose of the function total.", ["It sums all numeric values in its input list."], "analyse", "AO2"),
                _part(4, 1, f"State the result of fold (+) 0 [{x}, {y}, {z}].", [f"{x+y+z}."], "analyse", "AO2", {"result":str(x+y+z)}),
            ], "total [] = 0\ntotal (x:xs) = x + total xs"),
            _question(3, topic, "functional_type_short", "Function types and distribution", "The function f maps natural numbers to real numbers.", [
                _part(1, 1, "Describe the co-domain of function f.", ["The set of real numbers."], "analyse", "AO2"),
                _part(2, 3, "Describe features of functional languages that support distributing processing across servers, including why shared-state conflicts are reduced.", ["Immutable values cannot be changed after creation.", "Pure functions depend on inputs rather than shared mutable state, avoiding conflicting writes.", "Higher-order mapping operations apply independent computations across data partitions and combine the results."], "describe"),
            ], "f: Natural -> Real"),
            _question(4, topic, "functional_extended", "Recursive cost and composition", "The code below is functional. The positive-integer function ways counts routes with step sizes one or two; h is applied to integer lists.", [
                _part(1, 4, "Complete a trace table giving the returned value for h [2], h [3,2], h [1,3,2], and h [].", ["h [2] = 2.", "h [3,2] = 7.", "h [1,3,2] = 15.", "h [] = 0."], "trace", "AO2", {"call-1":"2","call-2":"7","call-3":"15","call-4":"0"}),
                _part(2, 2, "Explain why the recursive ways function is inefficient for large arguments because of repeated calculations.", ["Each non-base call makes two recursive calls.", "Overlapping subproblems repeatedly evaluate the same arguments, so the number of calls grows exponentially without memoisation."], "analyse", "AO2"),
                _part(3, 2, "Describe partial application of a two-argument function add a b = a + b when its first argument is fixed to 7.", ["Fixing a to 7 creates a new one-argument function.", "The remaining argument b is accepted later and the new function returns 7 + b."], "describe"),
                _part(4, 2, "Explain what makes a function higher-order, using map as an example.", ["A higher-order function takes a function as an argument or returns one.", "map takes a supplied function and applies it to list elements."], "explain"),
            ], "ways 1 = 1\nways 2 = 2\nways n = ways (n - 1) + ways (n - 2)\nh [] = 0\nh (x:xs) = x + 2 * h xs"),
        ]
    raise ValueError(f"No reviewed bank for topic {topic}")
