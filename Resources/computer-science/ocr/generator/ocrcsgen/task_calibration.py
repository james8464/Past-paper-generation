"""Original tasks supporting the inferred OCR item budgets.

AO2 rows analyse an actual implementation or constraint. They are not generic
recall with a business name appended. AO3 coding rows specify observable code
features; the separate discussion tasks retain best-fit evaluation.
"""
from __future__ import annotations

# Keys are (component, group, part); marks and syllabus coverage live in configs.
TASKS: dict[tuple[int, str, int], tuple[str, list[str]]] = {
    (1, "1", 1): (
        "Explain the separate roles of the address, data and control buses in reading a value from memory, including how the processor indicates that a read is required.",
        ["The address bus carries the address of the required memory location from the processor.",
         "The data bus carries the value returned from memory to the processor.",
         "The control bus carries signals coordinating the transfer.",
         "A memory-read control signal requests reading rather than writing the addressed location."]),
    (1, "1", 3): (
        "Explain how a larger cache, a higher clock speed and additional processor cores can each improve processor performance.",
        ["A larger cache can retain more frequently needed instructions or data, reducing slower main-memory accesses.",
         "A higher clock speed provides more clock cycles per second, potentially executing more instructions per second.",
         "Additional cores can execute independent tasks in parallel when the workload and software permit it."]),
    (1, "1", 6): (
        "Explain the fetch stage of the fetch-decode-execute cycle. Include how the instruction address is selected, how the instruction reaches the current instruction register and how the next address is prepared.",
        ["The program counter's address is copied to the memory address register and sent to memory.",
         "The memory-read signal retrieves the instruction into the memory data register, then the current instruction register.",
         "The program counter is incremented to address the next sequential instruction."]),
    (1, "1", 8): (
        "Explain why capacity, access speed and durability are separate considerations when selecting a secondary-storage device.",
        ["Capacity determines whether the required quantity of data can be retained.",
         "Access speed affects the time taken to retrieve or save data.",
         "Durability affects whether data remains available despite wear or physical handling."]),
    (1, "2", 2): (
        "Explain the fetch, decode and execute stages for an instruction that adds a stored operand to the accumulator.",
        ["The program counter identifies the instruction address, copied to the memory address register.",
         "The instruction is read through the memory data register into the current instruction register.",
         "The control unit decodes the opcode and identifies the operand address.",
         "The operand is fetched and the arithmetic logic unit adds it to the accumulator, storing the result there."]),
    (1, "2", 3): (
        "Explain why increasing clock speed, cache size or core count does not guarantee a proportional performance improvement.",
        ["A processor may wait for memory or input/output, so faster clock cycles do not remove every delay.",
         "Increasing cache size gives little benefit if the working set already fits or has poor reuse.",
         "Sequential dependencies prevent all work being divided between additional cores."]),
    (1, "2", 5): (
        "Explain how address-bus width and data-bus width affect a processor's memory transfers, and distinguish the directions of information flow on these buses.",
        ["An n-bit address bus can identify at most 2 to the power n distinct addresses.",
         "A wider data bus can transfer more bits in one transfer.",
         "Addresses are sent from the processor to the addressed device.",
         "The data bus is bidirectional because data can be read from or written to memory."]),
    (1, "3", 3): (
        "Describe the separate roles of a translator, a linker and a loader when preparing and running a program.",
        ["A translator converts source code into an executable or intermediate form.",
         "A linker combines object code with required library code and resolves external references.",
         "A loader places the executable and its required data into memory ready for execution."]),
    (1, "6", 2): (
        "Describe the conditions for first, second and third normal form, and one purpose of normalising a relational database.",
        ["First normal form uses atomic attribute values with no repeating groups.",
         "Second normal form is in first normal form with no partial dependency on a composite key.",
         "Third normal form is in second normal form with no transitive non-key dependency.",
         "Normalisation reduces redundant storage and the associated update, insertion or deletion anomalies."]),
    (1, "10", 1): (
        "Describe two data-protection principles and the unauthorised-access offence under computer-misuse legislation.",
        ["Personal data is collected for specified legitimate purposes and not incompatibly reused.",
         "Personal data must be protected against unauthorised processing or accidental loss.",
         "Knowingly securing unauthorised access to computer programs or data is an offence."]),
    (1, "10", 2): (
        "Describe how copyright protects software and how proprietary and open-source licences differ in permitted use of source code.",
        ["Copyright restricts unauthorised copying or adaptation of the software.",
         "A proprietary licence normally withholds permission to inspect, modify or redistribute the source.",
         "An open-source licence permits source inspection, modification and redistribution subject to its stated conditions."]),
    (1, "5", 1): (
        "Draw a labelled logic circuit for a warning system. The warning W must be on when sensor A is on and sensor B is off, or whenever override C is on. Show the intermediate signal and all gate connections.",
        ["A NOT gate produces NOT B.", "An AND gate combines A and NOT B.",
         "An OR gate combines the AND output with C.", "A, B, C and W are labelled and connected without ambiguity."]),
    (1, "8", 3): (
        "Evaluate the suitability of a queue for a service required to process accepted requests in arrival order, but also to respond quickly to urgent requests. Explain the queue's operation and reach a conditional conclusion.",
        ["The queue inserts requests at the rear.", "Removing from the front processes requests in arrival order.",
         "A queue meets the fairness requirement, but an urgent arrival still waits behind earlier requests.",
         "It is suitable if arrival order has priority; a priority queue is preferable if urgency must override that order."]),
    (1, "6", 4): (
        "Develop pseudocode for a web-log routine that reads URL strings until end of file, counts visits to each URL and outputs every URL with its count. Use a dictionary and do not discard repeat visits.",
        ["Initialise an empty dictionary.", "Read each line until end of file.", "Use the URL string as the dictionary key.",
         "Initialise a previously unseen URL's count.", "Increment the count on each occurrence.", "Iterate over dictionary entries and output each URL and count."]),
    (1, "9", 1): (
        "Develop pseudocode for a record-transfer routine. For each received record, compare its supplied digest with hash(record.data). Store only records whose digests match, and report a failed check without stopping later records.",
        ["Iterate over all received records.", "Compute the hash of each record's data.", "Compare the computed and supplied digest.",
         "Store the record only on a matching digest.", "Report a mismatch and continue processing subsequent records."]),
    (2, "1", 3): (
        "Explain why a reading equal to the threshold does not change total in the supplied code, and how replacing > with >= would change this boundary behaviour.",
        ["Equality fails the strict greater-than condition, so the addition is skipped.",
         "With greater-than-or-equal, equality passes and the boundary reading is added."]),
    (2, "1", 4): (
        "Develop a function firstAbove(values, limit) that returns the zero-based index of the first reading above limit, or -1 when none qualifies. Stop searching once a qualifying reading is found.",
        ["Accept the values array and limit as parameters.", "Examine array elements in index order.",
         "Return the current index immediately when its value exceeds limit.", "Return -1 only after the search finishes without a match."]),
    (2, "3", 1): (
        "Develop pseudocode to search an unsorted array of record identifiers for a target. Return both the number of matches and the last matching index. Return an index of -1 if there is no match.",
        ["Accept the array and target.", "Initialise the match count to zero.", "Initialise the last index to -1.",
         "Visit each valid index.", "Compare the identifier at that index with the target.",
         "On a match, increment the count and retain that index.", "Return the count and last index after completing the search."]),
    (2, "3", 2): (
        "Explain why a recursive route search can fail on a graph containing a cycle if it records each visited vertex only after exploring its neighbours. Explain why recording it before recursion prevents that failure.",
        ["A cycle leads back to a vertex already on the current recursive path.", "That vertex is not yet recorded as visited.",
         "The search can recurse around the cycle repeatedly instead of terminating.", "Recording before recursive calls lets the visited test reject the repeated vertex."]),
    (2, "5", 1): (
        "Explain the consequences of this record-entry sequence using parallel arrays: append the name; validate the score; append the score only if valid. Consider a rejected score followed by an accepted entry.",
        ["The rejected entry leaves a name without a corresponding score.", "The array lengths can differ.",
         "A later accepted score can occupy the index of the rejected name.", "Looking up matching indices can associate a score with the wrong person."]),
    (2, "5", 2): (
        "Explain the two separate roles of modulo arithmetic and the full-queue test in a circular queue. The implementation reserves one empty position and advances tail using (tail + 1) MOD capacity.",
        ["Modulo wraps the tail index to the start of the array.", "It keeps the index within the allocated array.",
         "The full test detects when advancing tail would meet head.", "Reserving the empty position distinguishes full from empty and prevents overwriting unread entries."]),
    (2, "5", 3): (
        "Explain why inserting new before current in a linked list must preserve the old link. Compare new.next = previous.next followed by previous.next = new with performing those assignments in the opposite order.",
        ["In the stated order, new.next retains the old successor.", "previous.next then makes the new node reachable.",
         "In the opposite order, previous.next already refers to new when copied.", "This makes a self-link and loses the route to the original successor."]),
    (2, "6", 1): (
        "Explain why the update low = mid can fail to make progress in a binary search when low and high are adjacent and the target is above the lower item. Contrast low = mid + 1.",
        ["Integer midpoint calculation can select the current low index.", "Assigning that same index leaves the search interval unchanged.",
         "Adding one removes the tested item and makes the interval shrink."]),
    (2, "6", 3): (
        "Explain the operation of merge sort, including its base case, division, recursive sorting, merge comparison and handling of remaining items.",
        ["A list of at most one item is the base case.", "Split a larger list into two sublists.",
         "Sort each sublist recursively.", "Repeatedly copy the smaller front item while both sublists contain items.",
         "Copy the remaining items once the other sublist is exhausted."]),
    (2, "7", 4): (
        "Explain the effect of backup = active when active refers to a mutable record. A later statement changes backup.status. Contrast this with constructing a new record containing copies of active's fields.",
        ["Assignment copies the object reference.", "Both names therefore identify the same record.",
         "Changing status through backup also changes the status seen through active.",
         "A separately constructed record has a different identity.", "Changing its copied scalar status field does not change the original record."]),
    (2, "7", 5): (
        "Explain why a file-processing routine must handle conversion errors around each record rather than around the whole loop when the requirement is to reject invalid lines but process all later valid lines.",
        ["An exception exits the protected block.", "A handler outside the loop therefore skips the remaining records after the first failure.",
         "A per-record handler rejects that line and permits the next iteration."]),
    (2, "8", 1): (
        "Explain which information is relevant to checking whether a booking overlaps an existing booking. The records contain resource ID, start time, end time, customer name and invoice colour. Justify excluding irrelevant fields.",
        ["The resource ID establishes whether the bookings compete for the same resource.", "Start and end times establish interval overlap.",
         "Customer name does not change whether the resource is occupied.", "Invoice colour has no bearing on resource availability; omitting it simplifies the model without losing the required decision."]),
    (2, "8", 2): (
        "Explain why the sequence save(record); validate(record) violates a requirement that invalid records must never be stored. Identify the dependency between these two operations.",
        ["The record is persisted before its validity is known.", "A failed validation does not undo that earlier write.",
         "Saving must depend on successful validation, rather than merely following an unconditional validation call."]),
    (2, "8", 3): (
        "Explain how two threads can lose an update when each reads the same counter, increments its local copy and writes back without coordination.",
        ["Both threads can read the same original value before either writes.", "They compute their updates independently from that same starting state.",
         "The later write overwrites the other update instead of combining both increments."]),
    (2, "9", 1): (
        "Explain why index < length AND values[index] > limit must use short-circuit evaluation, in that order, when index might be outside the array.",
        ["The bounds test is evaluated before accessing the element.", "If it fails, short-circuit evaluation skips the array access.",
         "Evaluating the element test first or evaluating both operands can cause an out-of-bounds error."]),
    (2, "9", 3): (
        "Explain why placing one mutable bookings list on the class, rather than creating a list for each object, can mix different customers' bookings.",
        ["The class-level list is a single shared object.", "Appending through one customer's object changes that shared list.",
         "Other customers' objects therefore observe entries not belonging exclusively to them."]),
    (2, "9", 4): (
        "Explain why returning from inside a file-reading loop immediately after storing a valid record fails the requirement to import the entire file.",
        ["Return exits the whole routine, not just the current iteration.", "The first valid record can therefore end the import.",
         "Later lines are never read or validated, so the stored data is incomplete."]),
    (2, "9", 5): (
        "Develop a Record class constructor that accepts an identifier and name, stores both in instance fields, sets status to 'new' and creates a separate empty bookings list for each instance.",
        ["Define the constructor in Record.", "Accept identifier and name parameters.", "Assign both supplied values to the corresponding instance fields.",
         "Initialise the instance status to 'new'.", "Create a new empty list for that instance's bookings."]),
    (2, "9", 6): (
        "Explain the behaviour of visit(node): if node is not null, call visit(node.next), then print node.name. Consider output order, termination and memory for a long acyclic linked list.",
        ["The recursive call happens before printing the current node.", "Each call waits for the remaining suffix of the list.",
         "Names are printed as calls return, so their order is reversed.", "The null link ends recursion.",
         "Suspended calls occupy stack space proportional to the list length."]),
    (2, "9", 7): (
        "Explain why a shallow copy of an object with a mutable bookings list does not provide an independent backup. Contrast copying scalar fields and copying the list's contents; consider both appending an entry and editing a mutable entry.",
        ["A shallow copy creates a separate outer object.", "Its list field still references the same list.",
         "Appending via either object changes the shared list.", "Copying the list itself separates later appends.",
         "Mutable entries can still be shared between the two lists.", "Independent edits to those entries require copying the relevant nested objects too."]),
    (2, "9", 8): (
        "Explain why a routine that validates a file path and then opens the file must still handle an open error. Another process may rename the file between these operations.",
        ["Validation and opening are separate operations.", "The path can become invalid after the successful check.",
         "The open can therefore fail despite earlier validation.", "Handling the open failure permits a controlled error report instead of an unhandled exception."]),
}


def calibrated_task(topic_id: str, group: str, index: int) -> tuple[str, list[str]] | None:
    component = 1 if topic_id.startswith("systems-") else 2
    value = TASKS.get((component, group, index))
    return (value[0], list(value[1])) if value else None
