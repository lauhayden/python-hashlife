"""Core datastructures for HashLife"""

import enum
import math


class State(enum.Enum):
    ALIVE = True
    DEAD = False

    def __init__(self, _):
        self.level = 0

    def __bool__(self):
        return self.value


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
        return self.__class__(
            self.level - 1, self.rows, self._first_half(self.row_slice),
            self._first_half(self.col_slice)
        )

    @property
    def ne(self):
        return self.__class__(
            self.level - 1, self.rows, self._first_half(self.row_slice),
            self._second_half(self.col_slice)
        )

    @property
    def sw(self):
        return self.__class__(
            self.level - 1, self.rows, self._second_half(self.row_slice),
            self._first_half(self.col_slice)
        )

    @property
    def se(self):
        return self.__class__(
            self.level - 1, self.rows, self._second_half(self.row_slice),
            self._second_half(self.col_slice)
        )


class Node:
    # pylint: disable=no-member,access-member-before-definition
    # since we're initializing stuff in __new__, pylint can't detect members
    ALL_NODES = {}
    ALL_EMPTY = {}
    RULE_BIRTH = frozenset((3,))
    RULE_SURVIVE = frozenset((2, 3))

    def __new__(cls, nw, ne, sw, se):
        canonized = cls.ALL_NODES.get((nw, ne, sw, se), None)
        if canonized is not None:
            return canonized
        if not (nw.level == ne.level == sw.level == se.level):
            raise ValueError("Inconsistent subnode levels")
        instance = super().__new__(cls)
        cls.ALL_NODES[(nw, ne, sw, se)] = instance
        instance.level = nw.level + 1
        instance.nw = nw
        instance.ne = ne
        instance.sw = sw
        instance.se = se
        instance._next_gen = None
        instance._leap_gen = None
        return instance

    @classmethod
    def empty(cls, level):
        if level == 0:
            return State.DEAD
        n_empty = cls.ALL_EMPTY.get(level, None)
        if n_empty is not None:
            return n_empty
        n_empty = cls(
            cls.empty(level - 1), cls.empty(level - 1), cls.empty(level - 1), cls.empty(level - 1)
        )
        cls.ALL_EMPTY[level] = n_empty
        return n_empty

    @classmethod
    def from_state_map(cls, state_map):
        if state_map.level == 0:
            return state_map.val
        return cls(
            cls.from_state_map(state_map.nw), cls.from_state_map(state_map.ne),
            cls.from_state_map(state_map.sw), cls.from_state_map(state_map.se)
        )

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
            empty_rows = [[State.DEAD for _ in range(2**self.level)] for _ in range(2**self.level)]
            state_map = StateMap(self.level, empty_rows)
        self.nw.as_state_map(state_map.nw)
        self.ne.as_state_map(state_map.ne)
        self.sw.as_state_map(state_map.sw)
        self.se.as_state_map(state_map.se)
        return state_map

    def _neighbors_alive(self):
        """Evaluate how many neighbors are alive for a level 2 node"""
        if self.level != 2:
            raise ValueError("neighbors_alive only relevant for level 2 node")
        all_neighbors = (
            (
                self.nw.nw, self.nw.ne, self.nw.sw, self.ne.nw, self.ne.sw, self.sw.nw, self.sw.ne,
                self.se.nw
            ),
            (
                self.nw.ne, self.nw.se, self.ne.nw, self.ne.ne, self.ne.se, self.sw.ne, self.se.nw,
                self.se.ne
            ),
            (
                self.nw.sw, self.nw.se, self.ne.sw, self.sw.nw, self.sw.sw, self.sw.se, self.se.nw,
                self.se.sw
            ),
            (
                self.nw.se, self.ne.sw, self.ne.se, self.sw.ne, self.sw.se, self.se.ne, self.se.sw,
                self.se.se
            ),
        )
        return (sum(bool(neighbor) for neighbor in neighbors) for neighbors in all_neighbors)

    @classmethod
    def _eval_rule(cls, cell, neighbors_alive):
        if bool(cell):
            if neighbors_alive in cls.RULE_SURVIVE:
                return True
            return False
        if neighbors_alive in cls.RULE_BIRTH:
            return True
        return False

    @classmethod
    def centered_horizontal(cls, west, east):
        return cls(west.ne, east.nw, west.se, east.sw)

    @classmethod
    def centered_vertical(cls, north, south):
        return cls(north.sw, north.se, south.nw, south.ne)

    def centered_subnode(self):
        return self.__class__(self.nw.se, self.ne.sw, self.sw.ne, self.se.nw)

    def expand(self):
        empty = self.empty(self.level - 1)
        nw = self.__class__(empty, empty, empty, self.nw)
        ne = self.__class__(empty, empty, self.ne, empty)
        sw = self.__class__(empty, self.sw, empty, empty)
        se = self.__class__(self.se, empty, empty, empty)
        return self.__class__(nw, ne, sw, se)

    def shrink(self):
        should_be_empty = (
            self.nw.nw, self.nw.ne, self.nw.sw, self.ne.nw, self.ne.ne, self.ne.se, self.sw.nw,
            self.sw.sw, self.sw.se, self.se.ne, self.se.sw, self.se.se
        )
        for node in should_be_empty:
            if node is not self.empty(self.level - 2):
                raise ValueError("Cannot shrink")
        return self.centered_subnode()

    def next_gen(self):
        if self._next_gen is not None:
            return self._next_gen
        if self.level == 1:
            raise ValueError("Cannot call next_gen() on a level 1 node")
        if self.level == 2:
            # base case simulation
            nw_alive, ne_alive, sw_alive, se_alive = self._neighbors_alive()
            n_next = self.__class__(
                State(self._eval_rule(self.nw.se, nw_alive)),
                State(self._eval_rule(self.ne.sw, ne_alive)),
                State(self._eval_rule(self.sw.ne, sw_alive)),
                State(self._eval_rule(self.se.nw, se_alive)),
            )
        else:
            # recursive simulation
            n00 = self.nw.centered_subnode()
            n01 = self.centered_horizontal(self.nw, self.ne).centered_subnode()
            n02 = self.ne.centered_subnode()
            n10 = self.centered_vertical(self.nw, self.sw).centered_subnode()
            n11 = self.centered_subnode().centered_subnode()
            n12 = self.centered_vertical(self.ne, self.se).centered_subnode()
            n20 = self.sw.centered_subnode()
            n21 = self.centered_horizontal(self.sw, self.se).centered_subnode()
            n22 = self.se.centered_subnode()
            n_next = self.__class__(
                self.__class__(n00, n01, n10, n11).next_gen(),
                self.__class__(n01, n02, n11, n12).next_gen(),
                self.__class__(n10, n11, n20, n21).next_gen(),
                self.__class__(n11, n12, n21, n22).next_gen(),
            )
        self._next_gen = n_next
        return n_next

    def leap_gen(self):
        if self._leap_gen is not None:
            return self._leap_gen
        if self.level == 1:
            raise ValueError("Cannot call next_gen() on a level 1 node")
        if self.level == 2:
            # base case simulation
            n_leap = self.next_gen()
        else:
            # leap 2 ** (self.level - 2) generations ahead
            n00 = self.nw.leap_gen()
            n01 = self.centered_horizontal(self.nw, self.ne).leap_gen()
            n02 = self.ne.leap_gen()
            n10 = self.centered_vertical(self.nw, self.sw).leap_gen()
            n11 = self.centered_subnode().leap_gen()
            n12 = self.centered_vertical(self.ne, self.se).leap_gen()
            n20 = self.sw.leap_gen()
            n21 = self.centered_horizontal(self.sw, self.se).leap_gen()
            n22 = self.se.leap_gen()
            n_leap = self.__class__(
                self.__class__(n00, n01, n10, n11).leap_gen(),
                self.__class__(n01, n02, n11, n12).leap_gen(),
                self.__class__(n10, n11, n20, n21).leap_gen(),
                self.__class__(n11, n12, n21, n22).leap_gen(),
            )
        self._leap_gen = n_leap
        return n_leap

    def __bool__(self):
        raise RuntimeError("Cannot evaluate state of Node")