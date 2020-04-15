"""Tests for io module"""

import pytest

from hashlife.core import State, StateMap
from hashlife.io import str_to_state_map, state_map_to_str

def test_str_to_state_map():
    with pytest.raises(ValueError):
        str_to_state_map("")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "", "0")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "1", "")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "12", "0")
    with pytest.raises(ValueError):
        str_to_state_map("0110", "1", "01")
    with pytest.raises(ValueError):
        str_to_state_map("123")
    with pytest.raises(ValueError):
        str_to_state_map("123456789")
    m = str_to_state_map("0110", '1', '0')
    assert m.rows == [[State.DEAD, State.ALIVE], [State.ALIVE, State.DEAD]]
    assert m.level == 1


def test_state_map_to_str():
    state_map = StateMap(1, [[State.DEAD, State.ALIVE], [State.ALIVE, State.DEAD]])
    assert state_map_to_str(state_map) == "0110"
