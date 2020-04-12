import pytest

from node import eval_rule, State, StateMap, str_to_state_map, state_map_to_str, Node

def test_state():
    assert bool(State.ALIVE)
    assert State.ALIVE
    assert State.ALIVE.level == 0  # pylint: disable=no-member
    assert not bool(State.DEAD)
    assert not State.DEAD
    assert State.DEAD.level == 0  # pylint: disable=no-member

def test_eval_rule_birth():
    assert eval_rule(State.DEAD, 3)
    for i in (1, 2, 4, 5, 6, 7, 8):
        assert not eval_rule(State.DEAD, i)
    
def test_eval_rule_survive():
    for i in (2, 3):
        assert eval_rule(State.ALIVE, i)
    for i in (1, 4, 5, 6, 7, 8):
        assert not eval_rule(State.ALIVE, i)

def test_map_2x2():
    m = StateMap(1, ((State.DEAD, State.ALIVE), (State.ALIVE, State.DEAD)))
    assert m.nw.val == State.DEAD
    assert m.ne.val == State.ALIVE
    assert m.sw.val == State.ALIVE
    assert m.se.val == State.DEAD

def test_str_to_state_map():
    with pytest.raises(ValueError):
        str_to_state_map("", "1", "0")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "", "0")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "1", "")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "12", "0")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "1", "01")
    with pytest.raises(ValueError):
        str_to_state_map("123", "1", "0")
    with pytest.raises(ValueError):
        str_to_state_map("123456789", "1", "0")
    m = str_to_state_map("0110", '1', '0')
    assert m.rows == [[State.DEAD, State.ALIVE], [State.ALIVE, State.DEAD]]
    assert m.level == 1
        
def test_state_map_to_str():
    state_map = StateMap(1, [[State.DEAD, State.ALIVE], [State.ALIVE, State.DEAD]])
    assert state_map_to_str(state_map, "1", "0") == "0110"

class TestNode:
    @pytest.mark.parametrize("onehot", range(4))
    def test_init_level1_onehot(self, onehot):
        states = (State.DEAD,) * onehot + (State.ALIVE,) + (State.DEAD,) * (3 - onehot)
        n = Node(*states)
        assert n.level == 1
        assert (n.nw, n.ne, n.sw, n.se) == states

    @pytest.mark.parametrize("onehot", range(4))
    def test_from_state_map_2x2_onehot(self, onehot):
        states = (State.DEAD,) * onehot + (State.ALIVE,) + (State.DEAD,) * (3 - onehot)
        n = Node.from_state_map(str_to_state_map("0" * onehot + "1" + "0" * (3 - onehot), "1", "0"))
        assert n.level == 1
        assert (n.nw, n.ne, n.sw, n.se) == states

    def test_neighbors_alive_not_level_2(self):
        n = Node.from_state_map(str_to_state_map("0110", "1", "0"))
        with pytest.raises(ValueError):
            n.neighbors_alive()

    @pytest.mark.parametrize("row", range(4))
    @pytest.mark.parametrize("col", range(4))
    def test_neighbors_alive_onehot(self, row, col):
        strmap = "0" * 4 * row + "0" * col + "1" + "0" * (3 - col) + "0" * 4 * (3 - row)
        n = Node.from_state_map(str_to_state_map(strmap, "1", "0"))
        alive = tuple(n.neighbors_alive())
        assert len(alive) == 4
        assert alive[0] == int((row < 3 and col < 3) and (row != 1 or col != 1))
        assert alive[1] == int((row < 3 and col > 0) and (row != 1 or col != 2))
        assert alive[2] == int((row > 0 and col < 3) and (row != 2 or col != 1))
        assert alive[3] == int((row > 0 and col > 0) and (row != 2 or col != 2))

    def test_neighbors_alive_all_alive(self):
        strmap = "1" * 4 * 4
        n = Node.from_state_map(str_to_state_map(strmap, "1", "0"))
        assert tuple(n.neighbors_alive()) == (8, 8, 8, 8)

    def test_neighbors_alive_border(self):
        strmap = "1111100110011111"
        n = Node.from_state_map(str_to_state_map(strmap, "1", "0"))
        assert tuple(n.neighbors_alive()) == (5, 5, 5, 5)

    @pytest.mark.parametrize("onehot", range(4))
    @pytest.mark.parametrize("existing", [True, False])
    def test_as_state_map_2x2_onehot(self, onehot, existing):
        states = (State.DEAD,) * onehot + (State.ALIVE,) + (State.DEAD,) * (3 - onehot)
        n = Node(*states)
        if existing:
            state_map = StateMap(1, [[State.DEAD, State.DEAD], [State.DEAD, State.DEAD]], row_slice=slice(0, 2), col_slice=slice(0, 2))
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

    def test_centered_subnode_4x4(self):
        strmap = (
            "0000"
            "0110"
            "0110"
            "0000"
        )
        node = Node.from_state_map(str_to_state_map(strmap, "1", "0"))
        assert state_map_to_str(node.centered_subnode().as_state_map(), "1", "0") == (
            "11"
            "11"
        )
        
    def test_centered_horizontal_subnode_4x4(self):
        west = (
            "0000"
            "0001"
            "0001"
            "0000"
        )
        east = (
            "0000"
            "1000"
            "1000"
            "0000"
        )
        west_node = Node.from_state_map(str_to_state_map(west, "1", "0"))
        east_node = Node.from_state_map(str_to_state_map(east, "1", "0"))
        centered_node = Node.centered_horizontal_subnode(west_node, east_node)
        assert state_map_to_str(centered_node.as_state_map(), "1", "0") == (
            "11"
            "11"
        )

    def test_centered_vertical_subnode_4x4(self):
        north = (
            "0000"
            "0000"
            "0000"
            "0110"
        )
        south = (
            "0110"
            "0000"
            "0000"
            "0000"
        )
        north_node = Node.from_state_map(str_to_state_map(north, "1", "0"))
        south_node = Node.from_state_map(str_to_state_map(south, "1", "0"))
        centered_node = Node.centered_vertical_subnode(north_node, south_node)
        assert state_map_to_str(centered_node.as_state_map(), "1", "0") == (
            "11"
            "11"
        )

    def test_centered_subsubnode_8x8(self):
        strmap = (
            "00000000"
            "00000000"
            "00000000"
            "00011000"
            "00011000"
            "00000000"
            "00000000"
            "00000000"
        )
        node = Node.from_state_map(str_to_state_map(strmap, "1", "0"))
        assert state_map_to_str(node.centered_subsubnode().as_state_map(), "1", "0") == (
            "11"
            "11"
        )
