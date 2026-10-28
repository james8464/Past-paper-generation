# bounded data-only postfix semantics for experimental French task synthesis
#
# no Python or model-authored code is executed. This is independent of the tree
# oracle and doesn't change historical cases or the public generation route

LIMIT = 127
MAX_VALUE = 1_000_000
OPERATORS = ("+", "-", "*")


def _integer(value):
    return type(value) is int and abs(value) <= MAX_VALUE


# return the stack after each instruction, with the top at the right
def execute(program):
    if type(program) is not list or not 1 <= len(program) <= LIMIT:
        raise ValueError("Postfix program must be a bounded nonempty list")
    stack, trace = [], []
    for token in program:
        if _integer(token):
            stack.append(token)
        elif type(token) is str and token in OPERATORS and len(stack) >= 2:
            right = stack.pop()
            left = stack.pop()
            result = (
                left + right
                if token == "+"
                else left - right
                if token == "-"
                else left * right
            )
            if not _integer(result):
                raise ValueError("Postfix intermediate value exceeds the bound")
            stack.append(result)
        else:
            raise ValueError("Invalid postfix instruction or stack underflow")
        trace.append(stack.copy())
    if len(stack) != 1:
        raise ValueError("Postfix program must leave exactly one result")
    return dict(answer=stack[0], trace=trace, peak_depth=max(map(len, trace)))


# compile a strict full binary tree using an iterative postorder walk
#
# reject shared children, cycles, disconnected nodes and ambiguous rows
# Validated inputs are never modified; traversal is bounded by node count
def compile_tree(rows, root):
    if type(rows) is not list or not 1 <= len(rows) <= LIMIT or type(root) is not str:
        raise ValueError("Invalid bounded expression tree")
    nodes = {}
    for row in rows:
        if type(row) is not list or len(row) != 4:
            raise ValueError("Invalid expression row")
        node, value, left, right = row
        if type(node) is not str or not node or node in nodes:
            raise ValueError("Invalid or duplicate node identifier")
        if left is None and right is None:
            if not _integer(value):
                raise ValueError("Expression leaves must contain bounded integers")
        elif not (
            type(value) is str
            and value in OPERATORS
            and type(left) is str
            and type(right) is str
        ):
            raise ValueError("Internal nodes require an operator and two children")
        nodes[node] = (value, left, right)
    pending, seen, program = [(root, False)], set(), []
    while pending:
        node, expanded = pending.pop()
        if node not in nodes:
            raise ValueError("Missing tree node")
        value, left, right = nodes[node]
        if expanded:
            program.append(value)
            continue
        if node in seen:
            raise ValueError("Cycle or shared child in expression tree")
        seen.add(node)
        pending.append((node, True))
        if left is not None:
            pending.extend(((right, False), (left, False)))
    if len(seen) != len(nodes):
        raise ValueError("Disconnected expression nodes")
    return program
