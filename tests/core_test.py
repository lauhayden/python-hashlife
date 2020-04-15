"""Tests for core module"""

import pytest

from hashlife.core import State, StateMap, Node
from hashlife.io import str_to_state_map, state_map_to_str


def test_state():
    assert bool(State.ALIVE)
    assert State.ALIVE
    assert State.ALIVE.level == 0  # pylint: disable=no-member
    assert not bool(State.DEAD)
    assert not State.DEAD
    assert State.DEAD.level == 0  # pylint: disable=no-member


def test_map_2x2():
    m = StateMap(1, ((State.DEAD, State.ALIVE), (State.ALIVE, State.DEAD)))
    assert m.nw.val == State.DEAD
    assert m.ne.val == State.ALIVE
    assert m.sw.val == State.ALIVE
    assert m.se.val == State.DEAD


class TestNode:

    @pytest.fixture(autouse=True)
    def clear_all_nodes(self):
        try:
            yield
        finally:
            Node.ALL_NODES = {}

    @pytest.mark.parametrize("onehot", range(4))
    def test_new_2x2_onehot(self, onehot):
        # pylint: disable=no-member
        states = (State.DEAD,) * onehot + (State.ALIVE,) + (State.DEAD,) * (3 - onehot)
        n = Node(*states)
        assert n.level == 1
        assert (n.nw, n.ne, n.sw, n.se) == states

    def test_new_canonization(self):
        n1 = Node(State.DEAD, State.DEAD, State.DEAD, State.DEAD)
        n2 = Node(State.DEAD, State.DEAD, State.DEAD, State.DEAD)
        assert n1 is n2
        assert len(Node.ALL_NODES) == 1
        n3 = Node(State.DEAD, State.ALIVE, State.DEAD, State.DEAD)
        assert n1 is not n3
        assert len(Node.ALL_NODES) == 2

    def test_empty_4x4(self):
        n2 = Node.empty(2)
        assert len(Node.ALL_EMPTY) == 2
        n1 = Node.ALL_EMPTY[1]
        assert (n1.nw, n1.ne, n1.sw, n1.se) == (State.DEAD, State.DEAD, State.DEAD, State.DEAD)
        assert (n2.nw, n2.ne, n2.sw, n2.se) == (n1, n1, n1, n1)

    @pytest.mark.parametrize("onehot", range(4))
    def test_from_state_map_2x2_onehot(self, onehot):
        states = (State.DEAD,) * onehot + (State.ALIVE,) + (State.DEAD,) * (3 - onehot)
        n = Node.from_state_map(StateMap(1, [[states[0], states[1]], [states[2], states[3]]]))
        assert n.level == 1
        assert (n.nw, n.ne, n.sw, n.se) == states

    def test_neighbors_alive_not_2x2(self):
        n = Node.from_state_map(StateMap(1, [[State.DEAD, State.ALIVE], [State.ALIVE, State.DEAD]]))
        with pytest.raises(ValueError):
            n._neighbors_alive()

    @pytest.mark.parametrize("row", range(4))
    @pytest.mark.parametrize("col", range(4))
    def test_neighbors_alive_4x4_onehot(self, row, col):
        strmap = "0" * 4 * row + "0" * col + "1" + "0" * (3 - col) + "0" * 4 * (3 - row)
        n = Node.from_state_map(str_to_state_map(strmap))
        alive = tuple(n._neighbors_alive())
        assert len(alive) == 4
        assert alive[0] == int((row < 3 and col < 3) and (row != 1 or col != 1))
        assert alive[1] == int((row < 3 and col > 0) and (row != 1 or col != 2))
        assert alive[2] == int((row > 0 and col < 3) and (row != 2 or col != 1))
        assert alive[3] == int((row > 0 and col > 0) and (row != 2 or col != 2))

    def test_neighbors_alive_all_alive(self):
        strmap = "1" * 4 * 4
        n = Node.from_state_map(str_to_state_map(strmap))
        assert tuple(n._neighbors_alive()) == (8, 8, 8, 8)

    def test_neighbors_alive_border(self):
        strmap = (  # yapf: disable
            "1111"
            "1001"
            "1001"
            "1111"
        )
        n = Node.from_state_map(str_to_state_map(strmap))
        assert tuple(n._neighbors_alive()) == (5, 5, 5, 5)

    def test_eval_rule_birth(self):
        assert Node._eval_rule(State.DEAD, 3)
        for i in (1, 2, 4, 5, 6, 7, 8):
            assert not Node._eval_rule(State.DEAD, i)

    def test_eval_rule_survive(self):
        for i in (2, 3):
            assert Node._eval_rule(State.ALIVE, i)
        for i in (1, 4, 5, 6, 7, 8):
            assert not Node._eval_rule(State.ALIVE, i)

    @pytest.mark.parametrize("onehot", range(4))
    @pytest.mark.parametrize("existing", [True, False])
    def test_as_state_map_2x2_onehot(self, onehot, existing):
        states = (State.DEAD,) * onehot + (State.ALIVE,) + (State.DEAD,) * (3 - onehot)
        n = Node(*states)
        if existing:
            state_map = StateMap(
                1, [[State.DEAD, State.DEAD], [State.DEAD, State.DEAD]],
                row_slice=slice(0, 2),
                col_slice=slice(0, 2)
            )
        else:
            state_map = None
        state_map = n.as_state_map(state_map)
        assert state_map.rows == [[states[0], states[1]], [states[2], states[3]]]

    def test_as_state_map_4x4(self):
        states = (State.DEAD, State.ALIVE, State.ALIVE, State.DEAD)
        n1 = Node(*states)
        n2 = Node(n1, n1, n1, n1)
        state_map = n2.as_state_map()
        n1_state_map = [[State.DEAD, State.ALIVE], [State.ALIVE, State.DEAD]]
        assert state_map.nw.val == n1_state_map
        assert state_map.ne.val == n1_state_map
        assert state_map.sw.val == n1_state_map
        assert state_map.se.val == n1_state_map

    def test_centered_horizontal_2x2(self):
        west = (  #yapf: disable
            "01"
            "01"
        )
        east = ("10" "10")
        west_node = Node.from_state_map(str_to_state_map(west))
        east_node = Node.from_state_map(str_to_state_map(east))
        centered_node = Node.centered_horizontal(west_node, east_node)
        assert state_map_to_str(centered_node.as_state_map()) == (  # yapf: disable
            "11"
            "11"
        )

    def test_centered_vertical_2x2(self):
        north = (  #yapf: disable
            "00"
            "11"
        )
        south = ("11" "00")
        north_node = Node.from_state_map(str_to_state_map(north))
        south_node = Node.from_state_map(str_to_state_map(south))
        centered_node = Node.centered_vertical(north_node, south_node)
        assert state_map_to_str(centered_node.as_state_map()) == (  # yapf: disable
            "11"
            "11"
        )

    def test_centered_subnode_4x4(self):
        strmap = (  # yapf: disable
            "0000"
            "0110"
            "0110"
            "0000"
        )
        node = Node.from_state_map(str_to_state_map(strmap))
        assert state_map_to_str(node.centered_subnode().as_state_map()) == (
            # yapf: disable
            "11"
            "11"
        )

    def test_expand_2x2(self):
        strmap = (  # yapf: disable
            "11"
            "11"
        )
        node = Node.from_state_map(str_to_state_map(strmap))
        assert state_map_to_str(node.expand().as_state_map()) == (
            # yapf: disable
            "0000"
            "0110"
            "0110"
            "0000"
        )

    def test_shrink_4x4(self):
        strmap = (  # yapf: disable
            "0000"
            "0110"
            "0110"
            "0000"
        )
        node = Node.from_state_map(str_to_state_map(strmap))
        assert state_map_to_str(node.shrink().as_state_map()) == (
            # yapf: disable
            "11"
            "11"
        )

    def test_next_gen_glider(self):
        strmap = (
            "00000000"
            "00000000"
            "00|0100|00"
            "00|0010|00"
            "00|1110|00"
            "00|0000|00"
            "00000000"
            "00000000"
        )
        node = Node.from_state_map(str_to_state_map(strmap))
        assert node._next_gen is None
        n_next = node.next_gen()
        assert state_map_to_str(n_next.as_state_map()) == (
            # yapf: disable
            "0000"
            "1010"
            "0110"
            "0100"
        )
        assert node._next_gen is n_next

    def test_leap_gen_glider(self):
        # level 3 node, therefore computes 2 generations ahead
        strmap = (
            "00000000"
            "00000000"
            "00|0100|00"
            "00|0010|00"
            "00|1110|00"
            "00|0000|00"
            "00000000"
            "00000000"
        )
        node = Node.from_state_map(str_to_state_map(strmap))
        assert node._leap_gen is None
        n_next = node.leap_gen()
        assert state_map_to_str(n_next.as_state_map()) == (
            # yapf: disable
            "0000"
            "0010"
            "1010"
            "0110"
        )
        assert node._leap_gen is n_next
