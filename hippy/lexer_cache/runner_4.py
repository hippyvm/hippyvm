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
            if char == ' ':
                state = 1
            elif char == '$':
                state = 2
            elif '0' <= char <= '9':
                state = 3
            elif 'A' <= char <= 'Z':
                state = 4
            elif 'a' <= char <= 'z':
                state = 4
            elif char == '_':
                state = 4
            elif char == '[':
                state = 5
            elif char == ']':
                state = 6
            else:
                break
        if state == 2:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 2
                return ~i
            if 'A' <= char <= 'Z':
                state = 7
            elif 'a' <= char <= 'z':
                state = 7
            elif char == '_':
                state = 7
            else:
                break
        if state == 3:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 3
                return i
            if '0' <= char <= '9':
                state = 3
                continue
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
            if 'A' <= char <= 'Z':
                state = 4
                continue
            elif 'a' <= char <= 'z':
                state = 4
                continue
            elif '0' <= char <= '9':
                state = 4
                continue
            elif char == '_':
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
 {(0, ' '): 1,
  (0, '$'): 2,
  (0, '0'): 3,
  (0, '1'): 3,
  (0, '2'): 3,
  (0, '3'): 3,
  (0, '4'): 3,
  (0, '5'): 3,
  (0, '6'): 3,
  (0, '7'): 3,
  (0, '8'): 3,
  (0, '9'): 3,
  (0, 'A'): 4,
  (0, 'B'): 4,
  (0, 'C'): 4,
  (0, 'D'): 4,
  (0, 'E'): 4,
  (0, 'F'): 4,
  (0, 'G'): 4,
  (0, 'H'): 4,
  (0, 'I'): 4,
  (0, 'J'): 4,
  (0, 'K'): 4,
  (0, 'L'): 4,
  (0, 'M'): 4,
  (0, 'N'): 4,
  (0, 'O'): 4,
  (0, 'P'): 4,
  (0, 'Q'): 4,
  (0, 'R'): 4,
  (0, 'S'): 4,
  (0, 'T'): 4,
  (0, 'U'): 4,
  (0, 'V'): 4,
  (0, 'W'): 4,
  (0, 'X'): 4,
  (0, 'Y'): 4,
  (0, 'Z'): 4,
  (0, '['): 5,
  (0, ']'): 6,
  (0, '_'): 4,
  (0, 'a'): 4,
  (0, 'b'): 4,
  (0, 'c'): 4,
  (0, 'd'): 4,
  (0, 'e'): 4,
  (0, 'f'): 4,
  (0, 'g'): 4,
  (0, 'h'): 4,
  (0, 'i'): 4,
  (0, 'j'): 4,
  (0, 'k'): 4,
  (0, 'l'): 4,
  (0, 'm'): 4,
  (0, 'n'): 4,
  (0, 'o'): 4,
  (0, 'p'): 4,
  (0, 'q'): 4,
  (0, 'r'): 4,
  (0, 's'): 4,
  (0, 't'): 4,
  (0, 'u'): 4,
  (0, 'v'): 4,
  (0, 'w'): 4,
  (0, 'x'): 4,
  (0, 'y'): 4,
  (0, 'z'): 4,
  (2, 'A'): 7,
  (2, 'B'): 7,
  (2, 'C'): 7,
  (2, 'D'): 7,
  (2, 'E'): 7,
  (2, 'F'): 7,
  (2, 'G'): 7,
  (2, 'H'): 7,
  (2, 'I'): 7,
  (2, 'J'): 7,
  (2, 'K'): 7,
  (2, 'L'): 7,
  (2, 'M'): 7,
  (2, 'N'): 7,
  (2, 'O'): 7,
  (2, 'P'): 7,
  (2, 'Q'): 7,
  (2, 'R'): 7,
  (2, 'S'): 7,
  (2, 'T'): 7,
  (2, 'U'): 7,
  (2, 'V'): 7,
  (2, 'W'): 7,
  (2, 'X'): 7,
  (2, 'Y'): 7,
  (2, 'Z'): 7,
  (2, '_'): 7,
  (2, 'a'): 7,
  (2, 'b'): 7,
  (2, 'c'): 7,
  (2, 'd'): 7,
  (2, 'e'): 7,
  (2, 'f'): 7,
  (2, 'g'): 7,
  (2, 'h'): 7,
  (2, 'i'): 7,
  (2, 'j'): 7,
  (2, 'k'): 7,
  (2, 'l'): 7,
  (2, 'm'): 7,
  (2, 'n'): 7,
  (2, 'o'): 7,
  (2, 'p'): 7,
  (2, 'q'): 7,
  (2, 'r'): 7,
  (2, 's'): 7,
  (2, 't'): 7,
  (2, 'u'): 7,
  (2, 'v'): 7,
  (2, 'w'): 7,
  (2, 'x'): 7,
  (2, 'y'): 7,
  (2, 'z'): 7,
  (3, '0'): 3,
  (3, '1'): 3,
  (3, '2'): 3,
  (3, '3'): 3,
  (3, '4'): 3,
  (3, '5'): 3,
  (3, '6'): 3,
  (3, '7'): 3,
  (3, '8'): 3,
  (3, '9'): 3,
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
  (4, 'A'): 4,
  (4, 'B'): 4,
  (4, 'C'): 4,
  (4, 'D'): 4,
  (4, 'E'): 4,
  (4, 'F'): 4,
  (4, 'G'): 4,
  (4, 'H'): 4,
  (4, 'I'): 4,
  (4, 'J'): 4,
  (4, 'K'): 4,
  (4, 'L'): 4,
  (4, 'M'): 4,
  (4, 'N'): 4,
  (4, 'O'): 4,
  (4, 'P'): 4,
  (4, 'Q'): 4,
  (4, 'R'): 4,
  (4, 'S'): 4,
  (4, 'T'): 4,
  (4, 'U'): 4,
  (4, 'V'): 4,
  (4, 'W'): 4,
  (4, 'X'): 4,
  (4, 'Y'): 4,
  (4, 'Z'): 4,
  (4, '_'): 4,
  (4, 'a'): 4,
  (4, 'b'): 4,
  (4, 'c'): 4,
  (4, 'd'): 4,
  (4, 'e'): 4,
  (4, 'f'): 4,
  (4, 'g'): 4,
  (4, 'h'): 4,
  (4, 'i'): 4,
  (4, 'j'): 4,
  (4, 'k'): 4,
  (4, 'l'): 4,
  (4, 'm'): 4,
  (4, 'n'): 4,
  (4, 'o'): 4,
  (4, 'p'): 4,
  (4, 'q'): 4,
  (4, 'r'): 4,
  (4, 's'): 4,
  (4, 't'): 4,
  (4, 'u'): 4,
  (4, 'v'): 4,
  (4, 'w'): 4,
  (4, 'x'): 4,
  (4, 'y'): 4,
  (4, 'z'): 4,
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
 set([1, 3, 4, 5, 6, 7]),
 set([1, 3, 4, 5, 6, 7]),
 ['0, 0, 0, 0, 0, 0, 0, 0, start|, 0, start|, 0, 0',
  'H_WHITESPACE',
  '1, 0, start|, 0, start|, 0',
  'T_NUM_STRING',
  'T_STRING',
  '[',
  ']',
  'T_VARIABLE'])