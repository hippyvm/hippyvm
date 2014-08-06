def recognize(runner, i):
    #auto-generated code, don't edit
    assert i >= 0
    input = runner.text
    state = 0
    while 1:
        if state == 0:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 0
                return ~i
            if 'A' <= char <= 'Z':
                state = 1
            elif 'a' <= char <= 'z':
                state = 1
            elif char == '_':
                state = 1
            elif char == ' ':
                state = 2
            elif char == '$':
                state = 3
            elif '0' <= char <= '9':
                state = 4
            elif char == '[':
                state = 5
            elif char == ']':
                state = 6
            else:
                break
        if state == 1:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 1
                return i
            if 'A' <= char <= 'Z':
                state = 1
                continue
            elif 'a' <= char <= 'z':
                state = 1
                continue
            elif '0' <= char <= '9':
                state = 1
                continue
            elif char == '_':
                state = 1
                continue
            else:
                break
        if state == 3:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 3
                return ~i
            if 'A' <= char <= 'Z':
                state = 7
            elif 'a' <= char <= 'z':
                state = 7
            elif char == '_':
                state = 7
            else:
                break
        if state == 4:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 4
                return i
            if '0' <= char <= '9':
                state = 4
                continue
            else:
                break
        if state == 7:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 7
                return i
            if 'A' <= char <= 'Z':
                state = 7
                continue
            elif 'a' <= char <= 'z':
                state = 7
                continue
            elif '0' <= char <= '9':
                state = 7
                continue
            elif char == '_':
                state = 7
                continue
            else:
                break
        runner.last_matched_state = state
        runner.last_matched_index = i - 1
        runner.state = state
        if i == len(input):
            return i
        else:
            return ~i
        break
    runner.state = state
    return ~i
from rpython.rlib.parsing.deterministic import DFA
automaton = DFA(8,
 {(0, ' '): 2,
  (0, '$'): 3,
  (0, '0'): 4,
  (0, '1'): 4,
  (0, '2'): 4,
  (0, '3'): 4,
  (0, '4'): 4,
  (0, '5'): 4,
  (0, '6'): 4,
  (0, '7'): 4,
  (0, '8'): 4,
  (0, '9'): 4,
  (0, 'A'): 1,
  (0, 'B'): 1,
  (0, 'C'): 1,
  (0, 'D'): 1,
  (0, 'E'): 1,
  (0, 'F'): 1,
  (0, 'G'): 1,
  (0, 'H'): 1,
  (0, 'I'): 1,
  (0, 'J'): 1,
  (0, 'K'): 1,
  (0, 'L'): 1,
  (0, 'M'): 1,
  (0, 'N'): 1,
  (0, 'O'): 1,
  (0, 'P'): 1,
  (0, 'Q'): 1,
  (0, 'R'): 1,
  (0, 'S'): 1,
  (0, 'T'): 1,
  (0, 'U'): 1,
  (0, 'V'): 1,
  (0, 'W'): 1,
  (0, 'X'): 1,
  (0, 'Y'): 1,
  (0, 'Z'): 1,
  (0, '['): 5,
  (0, ']'): 6,
  (0, '_'): 1,
  (0, 'a'): 1,
  (0, 'b'): 1,
  (0, 'c'): 1,
  (0, 'd'): 1,
  (0, 'e'): 1,
  (0, 'f'): 1,
  (0, 'g'): 1,
  (0, 'h'): 1,
  (0, 'i'): 1,
  (0, 'j'): 1,
  (0, 'k'): 1,
  (0, 'l'): 1,
  (0, 'm'): 1,
  (0, 'n'): 1,
  (0, 'o'): 1,
  (0, 'p'): 1,
  (0, 'q'): 1,
  (0, 'r'): 1,
  (0, 's'): 1,
  (0, 't'): 1,
  (0, 'u'): 1,
  (0, 'v'): 1,
  (0, 'w'): 1,
  (0, 'x'): 1,
  (0, 'y'): 1,
  (0, 'z'): 1,
  (1, '0'): 1,
  (1, '1'): 1,
  (1, '2'): 1,
  (1, '3'): 1,
  (1, '4'): 1,
  (1, '5'): 1,
  (1, '6'): 1,
  (1, '7'): 1,
  (1, '8'): 1,
  (1, '9'): 1,
  (1, 'A'): 1,
  (1, 'B'): 1,
  (1, 'C'): 1,
  (1, 'D'): 1,
  (1, 'E'): 1,
  (1, 'F'): 1,
  (1, 'G'): 1,
  (1, 'H'): 1,
  (1, 'I'): 1,
  (1, 'J'): 1,
  (1, 'K'): 1,
  (1, 'L'): 1,
  (1, 'M'): 1,
  (1, 'N'): 1,
  (1, 'O'): 1,
  (1, 'P'): 1,
  (1, 'Q'): 1,
  (1, 'R'): 1,
  (1, 'S'): 1,
  (1, 'T'): 1,
  (1, 'U'): 1,
  (1, 'V'): 1,
  (1, 'W'): 1,
  (1, 'X'): 1,
  (1, 'Y'): 1,
  (1, 'Z'): 1,
  (1, '_'): 1,
  (1, 'a'): 1,
  (1, 'b'): 1,
  (1, 'c'): 1,
  (1, 'd'): 1,
  (1, 'e'): 1,
  (1, 'f'): 1,
  (1, 'g'): 1,
  (1, 'h'): 1,
  (1, 'i'): 1,
  (1, 'j'): 1,
  (1, 'k'): 1,
  (1, 'l'): 1,
  (1, 'm'): 1,
  (1, 'n'): 1,
  (1, 'o'): 1,
  (1, 'p'): 1,
  (1, 'q'): 1,
  (1, 'r'): 1,
  (1, 's'): 1,
  (1, 't'): 1,
  (1, 'u'): 1,
  (1, 'v'): 1,
  (1, 'w'): 1,
  (1, 'x'): 1,
  (1, 'y'): 1,
  (1, 'z'): 1,
  (3, 'A'): 7,
  (3, 'B'): 7,
  (3, 'C'): 7,
  (3, 'D'): 7,
  (3, 'E'): 7,
  (3, 'F'): 7,
  (3, 'G'): 7,
  (3, 'H'): 7,
  (3, 'I'): 7,
  (3, 'J'): 7,
  (3, 'K'): 7,
  (3, 'L'): 7,
  (3, 'M'): 7,
  (3, 'N'): 7,
  (3, 'O'): 7,
  (3, 'P'): 7,
  (3, 'Q'): 7,
  (3, 'R'): 7,
  (3, 'S'): 7,
  (3, 'T'): 7,
  (3, 'U'): 7,
  (3, 'V'): 7,
  (3, 'W'): 7,
  (3, 'X'): 7,
  (3, 'Y'): 7,
  (3, 'Z'): 7,
  (3, '_'): 7,
  (3, 'a'): 7,
  (3, 'b'): 7,
  (3, 'c'): 7,
  (3, 'd'): 7,
  (3, 'e'): 7,
  (3, 'f'): 7,
  (3, 'g'): 7,
  (3, 'h'): 7,
  (3, 'i'): 7,
  (3, 'j'): 7,
  (3, 'k'): 7,
  (3, 'l'): 7,
  (3, 'm'): 7,
  (3, 'n'): 7,
  (3, 'o'): 7,
  (3, 'p'): 7,
  (3, 'q'): 7,
  (3, 'r'): 7,
  (3, 's'): 7,
  (3, 't'): 7,
  (3, 'u'): 7,
  (3, 'v'): 7,
  (3, 'w'): 7,
  (3, 'x'): 7,
  (3, 'y'): 7,
  (3, 'z'): 7,
  (4, '0'): 4,
  (4, '1'): 4,
  (4, '2'): 4,
  (4, '3'): 4,
  (4, '4'): 4,
  (4, '5'): 4,
  (4, '6'): 4,
  (4, '7'): 4,
  (4, '8'): 4,
  (4, '9'): 4,
  (7, '0'): 7,
  (7, '1'): 7,
  (7, '2'): 7,
  (7, '3'): 7,
  (7, '4'): 7,
  (7, '5'): 7,
  (7, '6'): 7,
  (7, '7'): 7,
  (7, '8'): 7,
  (7, '9'): 7,
  (7, 'A'): 7,
  (7, 'B'): 7,
  (7, 'C'): 7,
  (7, 'D'): 7,
  (7, 'E'): 7,
  (7, 'F'): 7,
  (7, 'G'): 7,
  (7, 'H'): 7,
  (7, 'I'): 7,
  (7, 'J'): 7,
  (7, 'K'): 7,
  (7, 'L'): 7,
  (7, 'M'): 7,
  (7, 'N'): 7,
  (7, 'O'): 7,
  (7, 'P'): 7,
  (7, 'Q'): 7,
  (7, 'R'): 7,
  (7, 'S'): 7,
  (7, 'T'): 7,
  (7, 'U'): 7,
  (7, 'V'): 7,
  (7, 'W'): 7,
  (7, 'X'): 7,
  (7, 'Y'): 7,
  (7, 'Z'): 7,
  (7, '_'): 7,
  (7, 'a'): 7,
  (7, 'b'): 7,
  (7, 'c'): 7,
  (7, 'd'): 7,
  (7, 'e'): 7,
  (7, 'f'): 7,
  (7, 'g'): 7,
  (7, 'h'): 7,
  (7, 'i'): 7,
  (7, 'j'): 7,
  (7, 'k'): 7,
  (7, 'l'): 7,
  (7, 'm'): 7,
  (7, 'n'): 7,
  (7, 'o'): 7,
  (7, 'p'): 7,
  (7, 'q'): 7,
  (7, 'r'): 7,
  (7, 's'): 7,
  (7, 't'): 7,
  (7, 'u'): 7,
  (7, 'v'): 7,
  (7, 'w'): 7,
  (7, 'x'): 7,
  (7, 'y'): 7,
  (7, 'z'): 7},
 set([1, 2, 4, 5, 6, 7]),
 set([1, 2, 4, 5, 6, 7]),
 ['0, 0, 0, 0, 0, 0, 0, 0, start|, 0, start|, 0, 0',
  'T_STRING',
  'H_WHITESPACE',
  '1, 0, start|, 0, start|, 0',
  'T_NUM_STRING',
  '[',
  ']',
  'T_VARIABLE'])