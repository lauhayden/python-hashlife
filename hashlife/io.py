"""Helper functions for serializing/deserializing simulation state"""

import math

from hashlife.core import State, StateMap

def str_to_state_map(strmap, alive_char="1", dead_char="0"):
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
        str_row = strmap[row * sidelen:(row + 1) * sidelen]
        rows.append(list(State.ALIVE if char == alive_char else State.DEAD for char in str_row))
    level = 0
    while sidelen > 1:
        sidelen = sidelen // 2
        level += 1
    return StateMap(level, rows)


def state_map_to_str(state_map, alive_char="1", dead_char="0"):
    char_list = []
    for row in state_map.rows:
        for state in row:
            if state.value:
                char_list.append(alive_char)
            else:
                char_list.append(dead_char)
    return "".join(char_list)