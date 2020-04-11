import pytest

from node import eval_rule, State, StateMap, str_to_state_map, Node

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
        str_to_state_map("", "1")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "12")
    with pytest.raises(ValueError):
        str_to_state_map("123", "1")
    with pytest.raises(ValueError):
        str_to_state_map("123456789", "1")
    m = str_to_state_map("0110", '1')
    assert m.rows == ((State.DEAD, State.ALIVE), (State.ALIVE, State.DEAD))
    assert m.level == 1
        
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
        n = Node.from_state_map(str_to_state_map("0" * onehot + "1" + "0" * (3 - onehot), "1"))
        assert n.level == 1
        assert (n.nw, n.ne, n.sw, n.se) == states

    def test_neighbors_alive_not_level_2(self):
        n = Node.from_state_map(str_to_state_map("0110", "1"))
        with pytest.raises(ValueError):
            n.neighbors_alive()

    @pytest.mark.parametrize("row", range(4))
    @pytest.mark.parametrize("col", range(4))
    def test_neighbors_alive_onehot(self, row, col):
        strmap = "0" * 4 * row + "0" * col + "1" + "0" * (3 - col) + "0" * 4 * (3 - row)
        n = Node.from_state_map(str_to_state_map(strmap, "1"))
        alive = tuple(n.neighbors_alive())
        assert len(alive) == 4
        assert alive[0] == int((row < 3 and col < 3) and (row != 1 or col != 1))
        assert alive[1] == int((row < 3 and col > 0) and (row != 1 or col != 2))
        assert alive[2] == int((row > 0 and col < 3) and (row != 2 or col != 1))
        assert alive[3] == int((row > 0 and col > 0) and (row != 2 or col != 2))

    def test_neighbors_alive_all_alive(self):
        strmap = "1" * 4 * 4
        n = Node.from_state_map(str_to_state_map(strmap, "1"))
        assert tuple(n.neighbors_alive()) == (8, 8, 8, 8)

    def test_neighbors_alive_border(self):
        strmap = "1111100110011111"
        n = Node.from_state_map(str_to_state_map(strmap, "1"))
        assert tuple(n.neighbors_alive()) == (5, 5, 5, 5)
