import enum
import math

class State(enum.Enum):
    ALIVE = True
    DEAD = False

    def __init__(self, _):
        self.level = 0

    def __bool__(self):
        return self.value

def eval_rule(cell, neighbors_alive, birth=frozenset((3,)), survive=frozenset((2,3))):
    if bool(cell):
        if neighbors_alive in survive:
            return True
        return False
    if neighbors_alive in birth:
        return True
    return False

class StateMap:
    def __init__(self, level, rows, row_slice=None, col_slice=None):
        self.level = level
        self.rows = rows
        self.row_slice = row_slice
        self.col_slice = col_slice

    def _first_half(self, inslice):
        if inslice is None:
            return slice(0, len(self.rows) // 2)
        return slice(inslice.start, inslice.start + (inslice.stop - inslice.start) // 2)
    
    def _second_half(self, inslice):
        if inslice is None:
            return slice(len(self.rows) // 2, len(self.rows))
        return slice(inslice.start + (inslice.stop - inslice.start) // 2, inslice.stop)

    @property
    def val(self):
        sliced = list(map(lambda r: r[self.col_slice], self.rows[self.row_slice]))
        if len(sliced) == 1:
            return sliced[0][0]
        return sliced

    @property
    def nw(self):
        return self.__class__(self.level - 1, self.rows, self._first_half(self.row_slice), self._first_half(self.col_slice))
    
    @property
    def ne(self):
        return self.__class__(self.level - 1, self.rows, self._first_half(self.row_slice), self._second_half(self.col_slice))

    @property
    def sw(self):
        return self.__class__(self.level - 1, self.rows, self._second_half(self.row_slice), self._first_half(self.col_slice))

    @property
    def se(self):
        return self.__class__(self.level - 1, self.rows, self._second_half(self.row_slice), self._second_half(self.col_slice))

        

def str_to_state_map(strmap, alive_char, dead_char):
    if not strmap:
        raise ValueError("malformed")
    if len(alive_char) != 1:
        raise ValueError("alive_char must be length 1")
    if len(dead_char) != 1:
        raise ValueError("dead_char must be length 1")
    strmap = "".join(char if char in (alive_char, dead_char) else "" for char in strmap)
    sidelen = math.sqrt(len(strmap))
    if not sidelen.is_integer():
        raise ValueError("malformed")
    sidelen = int(sidelen)
    if sidelen % 2 != 0:
        raise ValueError("malformed")
    rows = []
    for row in range(sidelen):
        str_row = strmap[row * sidelen: (row + 1) * sidelen]
        rows.append(list(State.ALIVE if char == alive_char else State.DEAD for char in str_row))
    level = 0
    while sidelen > 1:
        sidelen = sidelen // 2
        level += 1
    return StateMap(level, rows)


def state_map_to_str(state_map, alive_char, dead_char):
    char_list = []
    for row in state_map:
        for state in row:
            if state.value:
                char_list.append(alive_char)
            else:
                char_list.append(dead_char)
    return "".join(char_list)


class Node:
    ALL_NODES = {State.ALIVE, State.DEAD}

    def __init__(self, nw, ne, sw, se):
        if not (nw.level == ne.level == sw.level == se.level):
            raise ValueError("Inconsistent subnode levels")
        self.level = nw.level + 1
        self.nw = nw
        self.ne = ne
        self.sw = sw
        self.se = se

    @classmethod
    def from_state_map(cls, state_map):
        if state_map.level == 0:
            return state_map.val
        return cls(cls.from_state_map(state_map.nw), cls.from_state_map(state_map.ne), cls.from_state_map(state_map.sw), cls.from_state_map(state_map.se))

    def as_state_map(self, state_map=None):
        if state_map is not None and state_map.level != self.level:
            raise ValueError("state_map level does not match")
        if self.level == 1:
            if state_map is None:
                return StateMap(self.level, [[self.nw, self.ne], [self.sw, self.se]])
            state_map.rows[state_map.row_slice.start][state_map.col_slice.start] = self.nw
            state_map.rows[state_map.row_slice.start][state_map.col_slice.start + 1] = self.ne
            state_map.rows[state_map.row_slice.start + 1][state_map.col_slice.start] = self.sw
            state_map.rows[state_map.row_slice.start + 1][state_map.col_slice.start + 1] = self.se
            return state_map
        if state_map is None:
            empty_rows = [[State.DEAD for _ in range(2 ** self.level)] for _ in range(2 ** self.level)]
            state_map = StateMap(self.level, empty_rows)
        self.nw.as_state_map(state_map.nw)
        self.ne.as_state_map(state_map.ne)
        self.sw.as_state_map(state_map.sw)
        self.se.as_state_map(state_map.se)
        return state_map

    def neighbors_alive(self):
        """Evaluate how many neighbors are alive for a level 2 node"""
        if self.level != 2:
            raise ValueError("neighbors_alive only relevant for level 2 node")
        all_neighbors = (
            (self.nw.nw, self.nw.ne, self.nw.sw, self.ne.nw, self.ne.sw, self.sw.nw, self.sw.ne, self.se.nw),
            (self.nw.ne, self.nw.se, self.ne.nw, self.ne.ne, self.ne.se, self.sw.ne, self.se.nw, self.se.ne),
            (self.nw.sw, self.nw.se, self.ne.sw, self.sw.nw, self.sw.sw, self.sw.se, self.se.nw, self.se.sw),
            (self.nw.se, self.ne.sw, self.ne.se, self.sw.ne, self.sw.se, self.se.ne, self.se.sw, self.se.se),
        )
        return (sum(bool(neighbor) for neighbor in neighbors) for neighbors in all_neighbors)

    def centered_subnode(self):
        return self.__class__(self.nw.se, self.ne.sw, self.sw.ne, self.se.nw)

    @classmethod
    def centered_horizontal(cls, w, e):
        return cls(w.ne.se, e.nw.sw, w.se.ne, e.sw.nw)

    @classmethod
    def centered_vertical(cls, n, s):
        return cls(n.sw.se, n.se.sw, s.nw.ne, s.ne.nw)

    def centered_subsubnode(self):
        return self.__class__(self.nw.se.se, self.ne.sw.sw, self.sw.ne.ne, self.se.nw.nw)

    def next_gen(self):
        if self.level == 1:
            raise ValueError("Cannot call next_gen() on a level 1 node")

        if self.level == 2:
            # base case simulation
            nw_alive, ne_alive, sw_alive, se_alive = self.neighbors_alive()
            return self.__class__(
                State(eval_rule(self.nw.se, nw_alive)),
                State(eval_rule(self.ne.sw, ne_alive)),
                State(eval_rule(self.sw.ne, sw_alive)),
                State(eval_rule(self.se.nw, se_alive)),
            )

        # recursive simulation
        n00 = self.nw.centered_subnode()
        n01 = self.centered_horizontal(self.nw, self.ne)
        n02 = self.ne.centered_subnode()
        n10 = self.centered_vertical(self.nw, self.sw)
        n11 = self.centered_subsubnode()
        n12 = self.centered_vertical(self.ne, self.se)
        n20 = self.sw.centered_subnode()
        n21 = self.centered_horizontal(self.sw, self.se)
        n22 = self.se.centered_subnode()
        return self.__class__(
            self.__class__(n00, n01, n10, n11).next_gen(),
            self.__class__(n01, n02, n11, n12).next_gen(),
            self.__class__(n10, n11, n20, n21).next_gen(),
            self.__class__(n11, n12, n21, n22).next_gen(),
        )

    def __bool__(self):
        raise RuntimeError("Cannot evaluate state of Node")