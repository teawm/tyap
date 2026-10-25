from collections import deque

class Automaton:
    def __init__(self, states, alphabet, delta, start, finals):
        self.states = set(states)
        self.alphabet = list(alphabet)
        self.delta = {k: frozenset(v) for k, v in delta.items()}
        self.start = start
        self.finals = set(finals)


def check_deterministic(aut):
    """Проверка на детерминированность"""
    problems = []
    for (s, a), t in sorted(aut.delta.items()):
        if len(t) > 1:
            problems.append((s, a, t))
    return problems


def subset_construction(nfa):
    """НКА -> ДКА (метод подмножеств)"""
    start = frozenset({nfa.start})
    states, delta, queue = {start}, {}, deque([start])
    name = lambda sub: "".join(sorted(sub)) if sub else "∅"
    
    while queue:
        cur = queue.popleft()
        for a in nfa.alphabet:
            tgt = frozenset(
                set().union(*[set(nfa.delta.get((s, a), set())) for s in cur])
            )
            delta[(name(cur), a)] = frozenset({name(tgt)})
            if tgt not in states:
                states.add(tgt)
                queue.append(tgt)
    
    names = {name(s) for s in states}
    finals = {n for n in names if set(n) & nfa.finals and n != "∅"}
    return Automaton(names, nfa.alphabet, delta, name(start), finals)


def remove_unreachable(aut):
    """Удаление недостижимых состояний"""
    reached, queue = {aut.start}, deque([aut.start])
    while queue:
        s = queue.popleft()
        for a in aut.alphabet:
            for t in aut.delta.get((s, a), ()):
                if t not in reached:
                    reached.add(t)
                    queue.append(t)
    delta = {k: v for k, v in aut.delta.items() if k[0] in reached}
    return Automaton(reached, aut.alphabet, delta, aut.start, aut.finals & reached)


def make_total(aut):
    """Делаем автомат полным (добавляем ловушку ∅)"""
    states, delta = set(aut.states), dict(aut.delta)
    missing = [(s, a) for s in states for a in aut.alphabet if not delta.get((s, a))]
    if not missing:
        return aut, None
    states.add("∅")
    for s, a in missing:
        delta[(s, a)] = frozenset({"∅"})
    for a in aut.alphabet:
        delta[("∅", a)] = frozenset({"∅"})
    return Automaton(states, aut.alphabet, delta, aut.start, aut.finals), "∅"


def minimize(aut):
    """Минимизация алгоритмом Мура"""
    blocks = [b for b in (aut.finals & aut.states, aut.states - aut.finals) if b]
    blocks = [frozenset(b) for b in blocks]
    
    while True:
        block_of = {s: i for i, b in enumerate(blocks) for s in b}
        new_blocks, changed = [], False
        for b in blocks:
            groups = {}
            for s in b:
                sig = tuple(
                    block_of[next(iter(aut.delta[(s, a)]))] 
                    for a in aut.alphabet
                )
                groups.setdefault(sig, set()).add(s)
            if len(groups) > 1:
                changed = True
            new_blocks += [frozenset(g) for g in groups.values()]
        if not changed:
            break
        blocks = new_blocks
    
    name_of = {s: b for b in blocks for s in b}
    delta = {
        (b, a): frozenset({
            name_of[next(iter(aut.delta[(next(iter(b)), a)]))]
        })
        for b in blocks 
        for a in aut.alphabet
    }
    return Automaton(
        set(blocks), aut.alphabet, delta, 
        name_of[aut.start], 
        {b for b in blocks if b & aut.finals}
    )


def remove_sink(aut, dead):
    """Удаляем ловушку"""
    if dead is None:
        return aut
    sink = next((b for b in aut.states if dead in b), None)
    if sink is None or sink in aut.finals:
        return aut
    delta = {k: v for k, v in aut.delta.items() if k[0] != sink and sink not in v}
    return Automaton(aut.states - {sink}, aut.alphabet, delta, aut.start, aut.finals - {sink})


def rename(aut):
    """Переименование состояний в A, B, C..."""
    order, seen, queue = [], {aut.start}, deque([aut.start])
    while queue:
        s = queue.popleft()
        order.append(s)
        for a in aut.alphabet:
            for t in sorted(aut.delta.get((s, a), ()), key=str):
                if t not in seen:
                    seen.add(t)
                    queue.append(t)
    names = {s: (chr(65 + i) if i < 26 else f"Q{i}") for i, s in enumerate(order)}
    delta = {
        (names[s], a): frozenset(names[t] for t in v) 
        for (s, a), v in aut.delta.items()
    }
    return Automaton(
        set(names.values()), aut.alphabet, delta,
        names[aut.start], {names[s] for s in aut.finals}
    )


def print_table(aut):
    """Печать таблицы переходов"""
    rows = []
    for s in sorted(aut.states, key=lambda x: (x != aut.start, x)):
        mark = ("->" if s == aut.start else "  ") + ("*" if s in aut.finals else " ")
        rows.append((mark + s, [aut.delta.get((s, a), frozenset()) for a in aut.alphabet]))
    w = max(len(r[0]) for r in rows) + 1
    cw = max(4, max((len(",".join(sorted(t))) for r in rows for t in r[1]), default=3) + 1)
    print(" " * w + "".join(a.rjust(cw) for a in aut.alphabet))
    for label, ts in rows:
        print(label.ljust(w) + "".join(
            (",".join(sorted(t)) if t else "—").rjust(cw) for t in ts
        ))
    print()


def process(aut, title):
    """Полный конвейер обработки"""
    print(f"=== {title} ===")
    print("Входной автомат (НКА):")
    print_table(aut)
    
    problems = check_deterministic(aut)
    if problems:
        print("Проверка на детерминированность: НЕ детерминирован")
        for s, a, t in problems:
            print(f"  б({s},{a}) = {{{','.join(sorted(t))}}} — несколько переходов")
        dfa = subset_construction(aut)
        print("\nДКА (метод подмножеств):")
        print_table(dfa)
    else:
        print("Проверка на детерминированность: детерминирован")
        dfa = aut
    
    dfa, dead = make_total(remove_unreachable(dfa))
    if dead is None and "∅" in dfa.states:
        dead = "∅"
    
    result = rename(remove_sink(minimize(dfa), dead))
    print("\nМинимизированный ДКА:")
    print_table(result)


# ========== ПРИМЕР ==========
# M = ({A,B,C}, {0,1}, б, A, {C}) для регулярного выражения (0+1)*11
# НКА для строк, оканчивающихся на "11":
#   б(A, 0) = {A}
#   б(A, 1) = {A, B}
#   б(B, 1) = {C}

if __name__ == "__main__":
    process(
        Automaton(
            {"A", "B", "C"},
            ["0", "1"],
            {
                ("A", "0"): {"A"},
                ("A", "1"): {"A", "B"},
                ("B", "1"): {"C"},
            },
            "A",
            {"C"},
        ),
        "Пример: (0+1)*11  (строки, оканчивающиеся на 11)",
    )