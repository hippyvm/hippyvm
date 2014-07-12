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
            if char == '\x00':
                state = 1
            elif char == ' ':
                state = 2
            elif char == '$':
                state = 3
            elif char == '(':
                state = 4
            elif char == ',':
                state = 5
            elif char == '0':
                state = 6
            elif '1' <= char <= '9':
                state = 7
            elif char == '<':
                state = 8
            elif char == '@':
                state = 9
            elif 'A' <= char <= 'Z':
                state = 10
            elif 'c' <= char <= 'v':
                state = 10
            elif 'x' <= char <= 'z':
                state = 10
            elif char == '_':
                state = 10
            elif char == 'a':
                state = 10
            elif char == '\\':
                state = 11
            elif char == '`':
                state = 12
            elif char == '|':
                state = 13
            elif char == '#':
                state = 14
            elif char == "'":
                state = 15
            elif char == '+':
                state = 16
            elif char == '/':
                state = 17
            elif char == ';':
                state = 18
            elif char == '?':
                state = 19
            elif char == '[':
                state = 20
            elif char == 'w':
                state = 21
            elif char == '{':
                state = 22
            elif char == '\n':
                state = 23
            elif char == '"':
                state = 24
            elif char == '&':
                state = 25
            elif char == '*':
                state = 26
            elif char == '.':
                state = 27
            elif char == ':':
                state = 28
            elif char == '>':
                state = 29
            elif char == '^':
                state = 30
            elif char == 'b':
                state = 31
            elif char == '~':
                state = 32
            elif char == '\t':
                state = 33
            elif char == '\r':
                state = 34
            elif char == '!':
                state = 35
            elif char == '%':
                state = 36
            elif char == ')':
                state = 37
            elif char == '-':
                state = 38
            elif char == '=':
                state = 39
            elif char == ']':
                state = 40
            elif char == '}':
                state = 41
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
            if 'A' <= char <= 'Z':
                state = 162
            elif 'a' <= char <= 'z':
                state = 162
            elif char == '_':
                state = 162
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
            if char == 'a':
                state = 96
            elif char == 'b':
                state = 97
            elif char == 'd':
                state = 98
            elif char == 'f':
                state = 99
            elif char == 'i':
                state = 100
            elif char == 'o':
                state = 101
            elif char == 's':
                state = 102
            elif char == 'r':
                state = 103
            elif char == 'u':
                state = 104
            else:
                break
        if state == 6:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 6
                return i
            if char == 'E':
                state = 64
            elif char == 'e':
                state = 64
            elif char == '.':
                state = 65
            elif char == 'X':
                state = 95
            elif char == 'x':
                state = 95
            elif '0' <= char <= '9':
                state = 7
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
            if char == 'E':
                state = 64
            elif char == 'e':
                state = 64
            elif char == '.':
                state = 65
            elif '0' <= char <= '9':
                state = 7
                continue
            else:
                break
        if state == 8:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 8
                return i
            if char == '=':
                state = 91
            elif char == '<':
                state = 92
            elif char == '>':
                state = 93
            else:
                break
        if state == 10:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 10
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'a' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            else:
                break
        if state == 13:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 13
                return i
            if char == '=':
                state = 89
            elif char == '|':
                state = 90
            else:
                break
        if state == 14:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 14
                return i
            if '\x0b' <= char <= '\xff':
                state = 14
                continue
            elif '\x00' <= char <= '\t':
                state = 14
                continue
            else:
                break
        if state == 15:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 15
                return ~i
            if char == '\\':
                state = 88
            elif char == "'":
                state = 58
            elif ']' <= char <= '\xff':
                state = 15
                continue
            elif '(' <= char <= '[':
                state = 15
                continue
            elif '\x00' <= char <= '&':
                state = 15
                continue
            else:
                break
        if state == 16:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 16
                return i
            if char == '+':
                state = 86
            elif char == '=':
                state = 87
            else:
                break
        if state == 17:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 17
                return i
            if char == '*':
                state = 82
            elif char == '=':
                state = 83
            elif char == '/':
                state = 14
                continue
            else:
                break
        if state == 19:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 19
                return i
            if char == '>':
                state = 81
            else:
                break
        if state == 21:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 21
                return i
            if char == 'h':
                state = 72
            elif 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'i' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 'a' <= char <= 'g':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            else:
                break
        if state == 24:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 24
                return i
            if char == '\\':
                state = 57
            elif char == '"':
                state = 58
            elif ']' <= char <= '\xff':
                state = 52
            elif '#' <= char <= '[':
                state = 52
            elif '\x00' <= char <= '!':
                state = 52
            else:
                break
        if state == 25:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 25
                return i
            if char == '=':
                state = 70
            elif char == '&':
                state = 71
            else:
                break
        if state == 26:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 26
                return i
            if char == '=':
                state = 69
            else:
                break
        if state == 27:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 27
                return i
            if char == 'E':
                state = 64
            elif char == 'e':
                state = 64
            elif '0' <= char <= '9':
                state = 65
            elif char == '=':
                state = 66
            else:
                break
        if state == 28:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 28
                return i
            if char == ':':
                state = 63
            else:
                break
        if state == 29:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 29
                return i
            if char == '=':
                state = 60
            elif char == '>':
                state = 61
            else:
                break
        if state == 30:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 30
                return i
            if char == '=':
                state = 59
            else:
                break
        if state == 31:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 31
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'a' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == '"':
                state = 52
            elif char == '<':
                state = 53
            elif char == "'":
                state = 15
                continue
            else:
                break
        if state == 34:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 34
                return ~i
            if char == '\n':
                state = 51
            else:
                break
        if state == 35:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 35
                return i
            if char == '=':
                state = 49
            else:
                break
        if state == 36:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 36
                return i
            if char == '=':
                state = 48
            else:
                break
        if state == 38:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 38
                return i
            if char == '-':
                state = 45
            elif char == '=':
                state = 46
            elif char == '>':
                state = 47
            else:
                break
        if state == 39:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 39
                return i
            if char == '=':
                state = 42
            elif char == '>':
                state = 43
            else:
                break
        if state == 42:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 42
                return i
            if char == '=':
                state = 44
            else:
                break
        if state == 49:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 49
                return i
            if char == '=':
                state = 50
            else:
                break
        if state == 52:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 52
                return ~i
            if char == '\\':
                state = 57
            elif char == '"':
                state = 58
            elif ']' <= char <= '\xff':
                state = 52
                continue
            elif '#' <= char <= '[':
                state = 52
                continue
            elif '\x00' <= char <= '!':
                state = 52
                continue
            else:
                break
        if state == 53:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 53
                return ~i
            if char == '<':
                state = 54
            else:
                break
        if state == 54:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 54
                return ~i
            if char == '<':
                state = 55
            else:
                break
        if state == 55:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 55
                return ~i
            if char == '\n':
                state = 56
            elif '\x0b' <= char <= '\xff':
                state = 55
                continue
            elif '\x00' <= char <= '\t':
                state = 55
                continue
            else:
                break
        if state == 57:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 57
                return ~i
            if '\x00' <= char <= '\xff':
                state = 52
                continue
            else:
                break
        if state == 61:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 61
                return i
            if char == '=':
                state = 62
            else:
                break
        if state == 64:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 64
                return ~i
            if char == '+':
                state = 67
            elif char == '-':
                state = 67
            elif '0' <= char <= '9':
                state = 68
            else:
                break
        if state == 65:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 65
                return i
            if char == 'E':
                state = 64
                continue
            elif char == 'e':
                state = 64
                continue
            elif '0' <= char <= '9':
                state = 65
                continue
            else:
                break
        if state == 67:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 67
                return ~i
            if '0' <= char <= '9':
                state = 68
            else:
                break
        if state == 68:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 68
                return i
            if '0' <= char <= '9':
                state = 68
                continue
            else:
                break
        if state == 72:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 72
                return i
            if char == 'i':
                state = 73
            elif 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'j' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 'a' <= char <= 'h':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            else:
                break
        if state == 73:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 73
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'a' <= char <= 's':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 'u' <= char <= 'z':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == 't':
                state = 74
            else:
                break
        if state == 74:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 74
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'f' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 'a' <= char <= 'd':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == 'e':
                state = 75
            else:
                break
        if state == 75:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 75
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'a' <= char <= 'r':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 't' <= char <= 'z':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == 's':
                state = 76
            else:
                break
        if state == 76:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 76
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'a' <= char <= 'o':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 'q' <= char <= 'z':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == 'p':
                state = 77
            else:
                break
        if state == 77:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 77
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'b' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == 'a':
                state = 78
            else:
                break
        if state == 78:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 78
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'd' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif char == 'a':
                state = 10
                continue
            elif char == 'b':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            elif char == 'c':
                state = 79
            else:
                break
        if state == 79:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 79
                return i
            if char == 'e':
                state = 80
            elif 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'f' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif 'a' <= char <= 'd':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            else:
                break
        if state == 80:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 80
                return i
            if 'A' <= char <= 'Z':
                state = 10
                continue
            elif 'a' <= char <= 'z':
                state = 10
                continue
            elif '0' <= char <= '9':
                state = 10
                continue
            elif char == '_':
                state = 10
                continue
            else:
                break
        if state == 82:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 82
                return ~i
            if '+' <= char <= '\xff':
                state = 82
                continue
            elif '\x00' <= char <= ')':
                state = 82
                continue
            elif char == '*':
                state = 84
            else:
                break
        if state == 84:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 84
                return ~i
            if '0' <= char <= '\xff':
                state = 82
                continue
            elif '\x00' <= char <= ')':
                state = 82
                continue
            elif '+' <= char <= '.':
                state = 82
                continue
            elif char == '*':
                state = 84
                continue
            elif char == '/':
                state = 85
            else:
                break
        if state == 88:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 88
                return ~i
            if '\x00' <= char <= '\xff':
                state = 15
                continue
            else:
                break
        if state == 92:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 92
                return i
            if char == '=':
                state = 94
            elif char == '<':
                state = 55
                continue
            else:
                break
        if state == 95:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 95
                return i
            if '0' <= char <= '9':
                state = 95
                continue
            elif 'A' <= char <= 'F':
                state = 95
                continue
            elif 'a' <= char <= 'f':
                state = 95
                continue
            else:
                break
        if state == 96:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 96
                return ~i
            if char == 'r':
                state = 157
            else:
                break
        if state == 97:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 97
                return ~i
            if char == 'i':
                state = 146
            elif char == 'o':
                state = 147
            else:
                break
        if state == 98:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 98
                return ~i
            if char == 'o':
                state = 142
            else:
                break
        if state == 99:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 99
                return ~i
            if char == 'l':
                state = 139
            else:
                break
        if state == 100:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 100
                return ~i
            if char == 'n':
                state = 132
            else:
                break
        if state == 101:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 101
                return ~i
            if char == 'b':
                state = 126
            else:
                break
        if state == 102:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 102
                return ~i
            if char == 't':
                state = 120
            else:
                break
        if state == 103:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 103
                return ~i
            if char == 'e':
                state = 116
            else:
                break
        if state == 104:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 104
                return ~i
            if char == 'n':
                state = 105
            else:
                break
        if state == 105:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 105
                return ~i
            if char == 'i':
                state = 106
            elif char == 's':
                state = 107
            else:
                break
        if state == 106:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 106
                return ~i
            if char == 'c':
                state = 111
            else:
                break
        if state == 107:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 107
                return ~i
            if char == 'e':
                state = 108
            else:
                break
        if state == 108:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 108
                return ~i
            if char == 't':
                state = 109
            else:
                break
        if state == 109:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 109
                return ~i
            if char == ')':
                state = 110
            else:
                break
        if state == 111:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 111
                return ~i
            if char == 'o':
                state = 112
            else:
                break
        if state == 112:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 112
                return ~i
            if char == 'd':
                state = 113
            else:
                break
        if state == 113:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 113
                return ~i
            if char == 'e':
                state = 114
            else:
                break
        if state == 114:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 114
                return ~i
            if char == ')':
                state = 115
            else:
                break
        if state == 116:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 116
                return ~i
            if char == 'a':
                state = 117
            else:
                break
        if state == 117:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 117
                return ~i
            if char == 'l':
                state = 118
            else:
                break
        if state == 118:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 118
                return ~i
            if char == ')':
                state = 119
            else:
                break
        if state == 120:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 120
                return ~i
            if char == 'r':
                state = 121
            else:
                break
        if state == 121:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 121
                return ~i
            if char == 'i':
                state = 122
            else:
                break
        if state == 122:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 122
                return ~i
            if char == 'n':
                state = 123
            else:
                break
        if state == 123:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 123
                return ~i
            if char == 'g':
                state = 124
            else:
                break
        if state == 124:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 124
                return ~i
            if char == ')':
                state = 125
            else:
                break
        if state == 126:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 126
                return ~i
            if char == 'j':
                state = 127
            else:
                break
        if state == 127:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 127
                return ~i
            if char == 'e':
                state = 128
            else:
                break
        if state == 128:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 128
                return ~i
            if char == 'c':
                state = 129
            else:
                break
        if state == 129:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 129
                return ~i
            if char == 't':
                state = 130
            else:
                break
        if state == 130:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 130
                return ~i
            if char == ')':
                state = 131
            else:
                break
        if state == 132:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 132
                return ~i
            if char == 't':
                state = 133
            else:
                break
        if state == 133:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 133
                return ~i
            if char == ')':
                state = 134
            elif char == 'e':
                state = 135
            else:
                break
        if state == 135:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 135
                return ~i
            if char == 'g':
                state = 136
            else:
                break
        if state == 136:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 136
                return ~i
            if char == 'e':
                state = 137
            else:
                break
        if state == 137:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 137
                return ~i
            if char == 'r':
                state = 138
            else:
                break
        if state == 138:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 138
                return ~i
            if char == ')':
                state = 134
            else:
                break
        if state == 139:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 139
                return ~i
            if char == 'o':
                state = 140
            else:
                break
        if state == 140:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 140
                return ~i
            if char == 'a':
                state = 141
            else:
                break
        if state == 141:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 141
                return ~i
            if char == 't':
                state = 118
                continue
            else:
                break
        if state == 142:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 142
                return ~i
            if char == 'u':
                state = 143
            else:
                break
        if state == 143:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 143
                return ~i
            if char == 'b':
                state = 144
            else:
                break
        if state == 144:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 144
                return ~i
            if char == 'l':
                state = 145
            else:
                break
        if state == 145:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 145
                return ~i
            if char == 'e':
                state = 118
                continue
            else:
                break
        if state == 146:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 146
                return ~i
            if char == 'n':
                state = 154
            else:
                break
        if state == 147:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 147
                return ~i
            if char == 'o':
                state = 148
            else:
                break
        if state == 148:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 148
                return ~i
            if char == 'l':
                state = 149
            else:
                break
        if state == 149:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 149
                return ~i
            if char == ')':
                state = 150
            elif char == 'e':
                state = 151
            else:
                break
        if state == 151:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 151
                return ~i
            if char == 'a':
                state = 152
            else:
                break
        if state == 152:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 152
                return ~i
            if char == 'n':
                state = 153
            else:
                break
        if state == 153:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 153
                return ~i
            if char == ')':
                state = 150
            else:
                break
        if state == 154:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 154
                return ~i
            if char == 'a':
                state = 155
            else:
                break
        if state == 155:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 155
                return ~i
            if char == 'r':
                state = 156
            else:
                break
        if state == 156:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 156
                return ~i
            if char == 'y':
                state = 124
                continue
            else:
                break
        if state == 157:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 157
                return ~i
            if char == 'r':
                state = 158
            else:
                break
        if state == 158:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 158
                return ~i
            if char == 'a':
                state = 159
            else:
                break
        if state == 159:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 159
                return ~i
            if char == 'y':
                state = 160
            else:
                break
        if state == 160:
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 160
                return ~i
            if char == ')':
                state = 161
            else:
                break
        if state == 162:
            runner.last_matched_index = i - 1
            runner.last_matched_state = state
            try:
                char = input[i]
                i += 1
            except IndexError:
                runner.state = 162
                return i
            if 'A' <= char <= 'Z':
                state = 162
                continue
            elif 'a' <= char <= 'z':
                state = 162
                continue
            elif '0' <= char <= '9':
                state = 162
                continue
            elif char == '_':
                state = 162
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
automaton = DFA(163,
 {(0, '\x00'): 1,
  (0, '\t'): 33,
  (0, '\n'): 23,
  (0, '\r'): 34,
  (0, ' '): 2,
  (0, '!'): 35,
  (0, '"'): 24,
  (0, '#'): 14,
  (0, '$'): 3,
  (0, '%'): 36,
  (0, '&'): 25,
  (0, "'"): 15,
  (0, '('): 4,
  (0, ')'): 37,
  (0, '*'): 26,
  (0, '+'): 16,
  (0, ','): 5,
  (0, '-'): 38,
  (0, '.'): 27,
  (0, '/'): 17,
  (0, '0'): 6,
  (0, '1'): 7,
  (0, '2'): 7,
  (0, '3'): 7,
  (0, '4'): 7,
  (0, '5'): 7,
  (0, '6'): 7,
  (0, '7'): 7,
  (0, '8'): 7,
  (0, '9'): 7,
  (0, ':'): 28,
  (0, ';'): 18,
  (0, '<'): 8,
  (0, '='): 39,
  (0, '>'): 29,
  (0, '?'): 19,
  (0, '@'): 9,
  (0, 'A'): 10,
  (0, 'B'): 10,
  (0, 'C'): 10,
  (0, 'D'): 10,
  (0, 'E'): 10,
  (0, 'F'): 10,
  (0, 'G'): 10,
  (0, 'H'): 10,
  (0, 'I'): 10,
  (0, 'J'): 10,
  (0, 'K'): 10,
  (0, 'L'): 10,
  (0, 'M'): 10,
  (0, 'N'): 10,
  (0, 'O'): 10,
  (0, 'P'): 10,
  (0, 'Q'): 10,
  (0, 'R'): 10,
  (0, 'S'): 10,
  (0, 'T'): 10,
  (0, 'U'): 10,
  (0, 'V'): 10,
  (0, 'W'): 10,
  (0, 'X'): 10,
  (0, 'Y'): 10,
  (0, 'Z'): 10,
  (0, '['): 20,
  (0, '\\'): 11,
  (0, ']'): 40,
  (0, '^'): 30,
  (0, '_'): 10,
  (0, '`'): 12,
  (0, 'a'): 10,
  (0, 'b'): 31,
  (0, 'c'): 10,
  (0, 'd'): 10,
  (0, 'e'): 10,
  (0, 'f'): 10,
  (0, 'g'): 10,
  (0, 'h'): 10,
  (0, 'i'): 10,
  (0, 'j'): 10,
  (0, 'k'): 10,
  (0, 'l'): 10,
  (0, 'm'): 10,
  (0, 'n'): 10,
  (0, 'o'): 10,
  (0, 'p'): 10,
  (0, 'q'): 10,
  (0, 'r'): 10,
  (0, 's'): 10,
  (0, 't'): 10,
  (0, 'u'): 10,
  (0, 'v'): 10,
  (0, 'w'): 21,
  (0, 'x'): 10,
  (0, 'y'): 10,
  (0, 'z'): 10,
  (0, '{'): 22,
  (0, '|'): 13,
  (0, '}'): 41,
  (0, '~'): 32,
  (3, 'A'): 162,
  (3, 'B'): 162,
  (3, 'C'): 162,
  (3, 'D'): 162,
  (3, 'E'): 162,
  (3, 'F'): 162,
  (3, 'G'): 162,
  (3, 'H'): 162,
  (3, 'I'): 162,
  (3, 'J'): 162,
  (3, 'K'): 162,
  (3, 'L'): 162,
  (3, 'M'): 162,
  (3, 'N'): 162,
  (3, 'O'): 162,
  (3, 'P'): 162,
  (3, 'Q'): 162,
  (3, 'R'): 162,
  (3, 'S'): 162,
  (3, 'T'): 162,
  (3, 'U'): 162,
  (3, 'V'): 162,
  (3, 'W'): 162,
  (3, 'X'): 162,
  (3, 'Y'): 162,
  (3, 'Z'): 162,
  (3, '_'): 162,
  (3, 'a'): 162,
  (3, 'b'): 162,
  (3, 'c'): 162,
  (3, 'd'): 162,
  (3, 'e'): 162,
  (3, 'f'): 162,
  (3, 'g'): 162,
  (3, 'h'): 162,
  (3, 'i'): 162,
  (3, 'j'): 162,
  (3, 'k'): 162,
  (3, 'l'): 162,
  (3, 'm'): 162,
  (3, 'n'): 162,
  (3, 'o'): 162,
  (3, 'p'): 162,
  (3, 'q'): 162,
  (3, 'r'): 162,
  (3, 's'): 162,
  (3, 't'): 162,
  (3, 'u'): 162,
  (3, 'v'): 162,
  (3, 'w'): 162,
  (3, 'x'): 162,
  (3, 'y'): 162,
  (3, 'z'): 162,
  (4, 'a'): 96,
  (4, 'b'): 97,
  (4, 'd'): 98,
  (4, 'f'): 99,
  (4, 'i'): 100,
  (4, 'o'): 101,
  (4, 'r'): 103,
  (4, 's'): 102,
  (4, 'u'): 104,
  (6, '.'): 65,
  (6, '0'): 7,
  (6, '1'): 7,
  (6, '2'): 7,
  (6, '3'): 7,
  (6, '4'): 7,
  (6, '5'): 7,
  (6, '6'): 7,
  (6, '7'): 7,
  (6, '8'): 7,
  (6, '9'): 7,
  (6, 'E'): 64,
  (6, 'X'): 95,
  (6, 'e'): 64,
  (6, 'x'): 95,
  (7, '.'): 65,
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
  (7, 'E'): 64,
  (7, 'e'): 64,
  (8, '<'): 92,
  (8, '='): 91,
  (8, '>'): 93,
  (10, '0'): 10,
  (10, '1'): 10,
  (10, '2'): 10,
  (10, '3'): 10,
  (10, '4'): 10,
  (10, '5'): 10,
  (10, '6'): 10,
  (10, '7'): 10,
  (10, '8'): 10,
  (10, '9'): 10,
  (10, 'A'): 10,
  (10, 'B'): 10,
  (10, 'C'): 10,
  (10, 'D'): 10,
  (10, 'E'): 10,
  (10, 'F'): 10,
  (10, 'G'): 10,
  (10, 'H'): 10,
  (10, 'I'): 10,
  (10, 'J'): 10,
  (10, 'K'): 10,
  (10, 'L'): 10,
  (10, 'M'): 10,
  (10, 'N'): 10,
  (10, 'O'): 10,
  (10, 'P'): 10,
  (10, 'Q'): 10,
  (10, 'R'): 10,
  (10, 'S'): 10,
  (10, 'T'): 10,
  (10, 'U'): 10,
  (10, 'V'): 10,
  (10, 'W'): 10,
  (10, 'X'): 10,
  (10, 'Y'): 10,
  (10, 'Z'): 10,
  (10, '_'): 10,
  (10, 'a'): 10,
  (10, 'b'): 10,
  (10, 'c'): 10,
  (10, 'd'): 10,
  (10, 'e'): 10,
  (10, 'f'): 10,
  (10, 'g'): 10,
  (10, 'h'): 10,
  (10, 'i'): 10,
  (10, 'j'): 10,
  (10, 'k'): 10,
  (10, 'l'): 10,
  (10, 'm'): 10,
  (10, 'n'): 10,
  (10, 'o'): 10,
  (10, 'p'): 10,
  (10, 'q'): 10,
  (10, 'r'): 10,
  (10, 's'): 10,
  (10, 't'): 10,
  (10, 'u'): 10,
  (10, 'v'): 10,
  (10, 'w'): 10,
  (10, 'x'): 10,
  (10, 'y'): 10,
  (10, 'z'): 10,
  (13, '='): 89,
  (13, '|'): 90,
  (14, '\x00'): 14,
  (14, '\x01'): 14,
  (14, '\x02'): 14,
  (14, '\x03'): 14,
  (14, '\x04'): 14,
  (14, '\x05'): 14,
  (14, '\x06'): 14,
  (14, '\x07'): 14,
  (14, '\x08'): 14,
  (14, '\t'): 14,
  (14, '\x0b'): 14,
  (14, '\x0c'): 14,
  (14, '\r'): 14,
  (14, '\x0e'): 14,
  (14, '\x0f'): 14,
  (14, '\x10'): 14,
  (14, '\x11'): 14,
  (14, '\x12'): 14,
  (14, '\x13'): 14,
  (14, '\x14'): 14,
  (14, '\x15'): 14,
  (14, '\x16'): 14,
  (14, '\x17'): 14,
  (14, '\x18'): 14,
  (14, '\x19'): 14,
  (14, '\x1a'): 14,
  (14, '\x1b'): 14,
  (14, '\x1c'): 14,
  (14, '\x1d'): 14,
  (14, '\x1e'): 14,
  (14, '\x1f'): 14,
  (14, ' '): 14,
  (14, '!'): 14,
  (14, '"'): 14,
  (14, '#'): 14,
  (14, '$'): 14,
  (14, '%'): 14,
  (14, '&'): 14,
  (14, "'"): 14,
  (14, '('): 14,
  (14, ')'): 14,
  (14, '*'): 14,
  (14, '+'): 14,
  (14, ','): 14,
  (14, '-'): 14,
  (14, '.'): 14,
  (14, '/'): 14,
  (14, '0'): 14,
  (14, '1'): 14,
  (14, '2'): 14,
  (14, '3'): 14,
  (14, '4'): 14,
  (14, '5'): 14,
  (14, '6'): 14,
  (14, '7'): 14,
  (14, '8'): 14,
  (14, '9'): 14,
  (14, ':'): 14,
  (14, ';'): 14,
  (14, '<'): 14,
  (14, '='): 14,
  (14, '>'): 14,
  (14, '?'): 14,
  (14, '@'): 14,
  (14, 'A'): 14,
  (14, 'B'): 14,
  (14, 'C'): 14,
  (14, 'D'): 14,
  (14, 'E'): 14,
  (14, 'F'): 14,
  (14, 'G'): 14,
  (14, 'H'): 14,
  (14, 'I'): 14,
  (14, 'J'): 14,
  (14, 'K'): 14,
  (14, 'L'): 14,
  (14, 'M'): 14,
  (14, 'N'): 14,
  (14, 'O'): 14,
  (14, 'P'): 14,
  (14, 'Q'): 14,
  (14, 'R'): 14,
  (14, 'S'): 14,
  (14, 'T'): 14,
  (14, 'U'): 14,
  (14, 'V'): 14,
  (14, 'W'): 14,
  (14, 'X'): 14,
  (14, 'Y'): 14,
  (14, 'Z'): 14,
  (14, '['): 14,
  (14, '\\'): 14,
  (14, ']'): 14,
  (14, '^'): 14,
  (14, '_'): 14,
  (14, '`'): 14,
  (14, 'a'): 14,
  (14, 'b'): 14,
  (14, 'c'): 14,
  (14, 'd'): 14,
  (14, 'e'): 14,
  (14, 'f'): 14,
  (14, 'g'): 14,
  (14, 'h'): 14,
  (14, 'i'): 14,
  (14, 'j'): 14,
  (14, 'k'): 14,
  (14, 'l'): 14,
  (14, 'm'): 14,
  (14, 'n'): 14,
  (14, 'o'): 14,
  (14, 'p'): 14,
  (14, 'q'): 14,
  (14, 'r'): 14,
  (14, 's'): 14,
  (14, 't'): 14,
  (14, 'u'): 14,
  (14, 'v'): 14,
  (14, 'w'): 14,
  (14, 'x'): 14,
  (14, 'y'): 14,
  (14, 'z'): 14,
  (14, '{'): 14,
  (14, '|'): 14,
  (14, '}'): 14,
  (14, '~'): 14,
  (14, '\x7f'): 14,
  (14, '\x80'): 14,
  (14, '\x81'): 14,
  (14, '\x82'): 14,
  (14, '\x83'): 14,
  (14, '\x84'): 14,
  (14, '\x85'): 14,
  (14, '\x86'): 14,
  (14, '\x87'): 14,
  (14, '\x88'): 14,
  (14, '\x89'): 14,
  (14, '\x8a'): 14,
  (14, '\x8b'): 14,
  (14, '\x8c'): 14,
  (14, '\x8d'): 14,
  (14, '\x8e'): 14,
  (14, '\x8f'): 14,
  (14, '\x90'): 14,
  (14, '\x91'): 14,
  (14, '\x92'): 14,
  (14, '\x93'): 14,
  (14, '\x94'): 14,
  (14, '\x95'): 14,
  (14, '\x96'): 14,
  (14, '\x97'): 14,
  (14, '\x98'): 14,
  (14, '\x99'): 14,
  (14, '\x9a'): 14,
  (14, '\x9b'): 14,
  (14, '\x9c'): 14,
  (14, '\x9d'): 14,
  (14, '\x9e'): 14,
  (14, '\x9f'): 14,
  (14, '\xa0'): 14,
  (14, '\xa1'): 14,
  (14, '\xa2'): 14,
  (14, '\xa3'): 14,
  (14, '\xa4'): 14,
  (14, '\xa5'): 14,
  (14, '\xa6'): 14,
  (14, '\xa7'): 14,
  (14, '\xa8'): 14,
  (14, '\xa9'): 14,
  (14, '\xaa'): 14,
  (14, '\xab'): 14,
  (14, '\xac'): 14,
  (14, '\xad'): 14,
  (14, '\xae'): 14,
  (14, '\xaf'): 14,
  (14, '\xb0'): 14,
  (14, '\xb1'): 14,
  (14, '\xb2'): 14,
  (14, '\xb3'): 14,
  (14, '\xb4'): 14,
  (14, '\xb5'): 14,
  (14, '\xb6'): 14,
  (14, '\xb7'): 14,
  (14, '\xb8'): 14,
  (14, '\xb9'): 14,
  (14, '\xba'): 14,
  (14, '\xbb'): 14,
  (14, '\xbc'): 14,
  (14, '\xbd'): 14,
  (14, '\xbe'): 14,
  (14, '\xbf'): 14,
  (14, '\xc0'): 14,
  (14, '\xc1'): 14,
  (14, '\xc2'): 14,
  (14, '\xc3'): 14,
  (14, '\xc4'): 14,
  (14, '\xc5'): 14,
  (14, '\xc6'): 14,
  (14, '\xc7'): 14,
  (14, '\xc8'): 14,
  (14, '\xc9'): 14,
  (14, '\xca'): 14,
  (14, '\xcb'): 14,
  (14, '\xcc'): 14,
  (14, '\xcd'): 14,
  (14, '\xce'): 14,
  (14, '\xcf'): 14,
  (14, '\xd0'): 14,
  (14, '\xd1'): 14,
  (14, '\xd2'): 14,
  (14, '\xd3'): 14,
  (14, '\xd4'): 14,
  (14, '\xd5'): 14,
  (14, '\xd6'): 14,
  (14, '\xd7'): 14,
  (14, '\xd8'): 14,
  (14, '\xd9'): 14,
  (14, '\xda'): 14,
  (14, '\xdb'): 14,
  (14, '\xdc'): 14,
  (14, '\xdd'): 14,
  (14, '\xde'): 14,
  (14, '\xdf'): 14,
  (14, '\xe0'): 14,
  (14, '\xe1'): 14,
  (14, '\xe2'): 14,
  (14, '\xe3'): 14,
  (14, '\xe4'): 14,
  (14, '\xe5'): 14,
  (14, '\xe6'): 14,
  (14, '\xe7'): 14,
  (14, '\xe8'): 14,
  (14, '\xe9'): 14,
  (14, '\xea'): 14,
  (14, '\xeb'): 14,
  (14, '\xec'): 14,
  (14, '\xed'): 14,
  (14, '\xee'): 14,
  (14, '\xef'): 14,
  (14, '\xf0'): 14,
  (14, '\xf1'): 14,
  (14, '\xf2'): 14,
  (14, '\xf3'): 14,
  (14, '\xf4'): 14,
  (14, '\xf5'): 14,
  (14, '\xf6'): 14,
  (14, '\xf7'): 14,
  (14, '\xf8'): 14,
  (14, '\xf9'): 14,
  (14, '\xfa'): 14,
  (14, '\xfb'): 14,
  (14, '\xfc'): 14,
  (14, '\xfd'): 14,
  (14, '\xfe'): 14,
  (14, '\xff'): 14,
  (15, '\x00'): 15,
  (15, '\x01'): 15,
  (15, '\x02'): 15,
  (15, '\x03'): 15,
  (15, '\x04'): 15,
  (15, '\x05'): 15,
  (15, '\x06'): 15,
  (15, '\x07'): 15,
  (15, '\x08'): 15,
  (15, '\t'): 15,
  (15, '\n'): 15,
  (15, '\x0b'): 15,
  (15, '\x0c'): 15,
  (15, '\r'): 15,
  (15, '\x0e'): 15,
  (15, '\x0f'): 15,
  (15, '\x10'): 15,
  (15, '\x11'): 15,
  (15, '\x12'): 15,
  (15, '\x13'): 15,
  (15, '\x14'): 15,
  (15, '\x15'): 15,
  (15, '\x16'): 15,
  (15, '\x17'): 15,
  (15, '\x18'): 15,
  (15, '\x19'): 15,
  (15, '\x1a'): 15,
  (15, '\x1b'): 15,
  (15, '\x1c'): 15,
  (15, '\x1d'): 15,
  (15, '\x1e'): 15,
  (15, '\x1f'): 15,
  (15, ' '): 15,
  (15, '!'): 15,
  (15, '"'): 15,
  (15, '#'): 15,
  (15, '$'): 15,
  (15, '%'): 15,
  (15, '&'): 15,
  (15, "'"): 58,
  (15, '('): 15,
  (15, ')'): 15,
  (15, '*'): 15,
  (15, '+'): 15,
  (15, ','): 15,
  (15, '-'): 15,
  (15, '.'): 15,
  (15, '/'): 15,
  (15, '0'): 15,
  (15, '1'): 15,
  (15, '2'): 15,
  (15, '3'): 15,
  (15, '4'): 15,
  (15, '5'): 15,
  (15, '6'): 15,
  (15, '7'): 15,
  (15, '8'): 15,
  (15, '9'): 15,
  (15, ':'): 15,
  (15, ';'): 15,
  (15, '<'): 15,
  (15, '='): 15,
  (15, '>'): 15,
  (15, '?'): 15,
  (15, '@'): 15,
  (15, 'A'): 15,
  (15, 'B'): 15,
  (15, 'C'): 15,
  (15, 'D'): 15,
  (15, 'E'): 15,
  (15, 'F'): 15,
  (15, 'G'): 15,
  (15, 'H'): 15,
  (15, 'I'): 15,
  (15, 'J'): 15,
  (15, 'K'): 15,
  (15, 'L'): 15,
  (15, 'M'): 15,
  (15, 'N'): 15,
  (15, 'O'): 15,
  (15, 'P'): 15,
  (15, 'Q'): 15,
  (15, 'R'): 15,
  (15, 'S'): 15,
  (15, 'T'): 15,
  (15, 'U'): 15,
  (15, 'V'): 15,
  (15, 'W'): 15,
  (15, 'X'): 15,
  (15, 'Y'): 15,
  (15, 'Z'): 15,
  (15, '['): 15,
  (15, '\\'): 88,
  (15, ']'): 15,
  (15, '^'): 15,
  (15, '_'): 15,
  (15, '`'): 15,
  (15, 'a'): 15,
  (15, 'b'): 15,
  (15, 'c'): 15,
  (15, 'd'): 15,
  (15, 'e'): 15,
  (15, 'f'): 15,
  (15, 'g'): 15,
  (15, 'h'): 15,
  (15, 'i'): 15,
  (15, 'j'): 15,
  (15, 'k'): 15,
  (15, 'l'): 15,
  (15, 'm'): 15,
  (15, 'n'): 15,
  (15, 'o'): 15,
  (15, 'p'): 15,
  (15, 'q'): 15,
  (15, 'r'): 15,
  (15, 's'): 15,
  (15, 't'): 15,
  (15, 'u'): 15,
  (15, 'v'): 15,
  (15, 'w'): 15,
  (15, 'x'): 15,
  (15, 'y'): 15,
  (15, 'z'): 15,
  (15, '{'): 15,
  (15, '|'): 15,
  (15, '}'): 15,
  (15, '~'): 15,
  (15, '\x7f'): 15,
  (15, '\x80'): 15,
  (15, '\x81'): 15,
  (15, '\x82'): 15,
  (15, '\x83'): 15,
  (15, '\x84'): 15,
  (15, '\x85'): 15,
  (15, '\x86'): 15,
  (15, '\x87'): 15,
  (15, '\x88'): 15,
  (15, '\x89'): 15,
  (15, '\x8a'): 15,
  (15, '\x8b'): 15,
  (15, '\x8c'): 15,
  (15, '\x8d'): 15,
  (15, '\x8e'): 15,
  (15, '\x8f'): 15,
  (15, '\x90'): 15,
  (15, '\x91'): 15,
  (15, '\x92'): 15,
  (15, '\x93'): 15,
  (15, '\x94'): 15,
  (15, '\x95'): 15,
  (15, '\x96'): 15,
  (15, '\x97'): 15,
  (15, '\x98'): 15,
  (15, '\x99'): 15,
  (15, '\x9a'): 15,
  (15, '\x9b'): 15,
  (15, '\x9c'): 15,
  (15, '\x9d'): 15,
  (15, '\x9e'): 15,
  (15, '\x9f'): 15,
  (15, '\xa0'): 15,
  (15, '\xa1'): 15,
  (15, '\xa2'): 15,
  (15, '\xa3'): 15,
  (15, '\xa4'): 15,
  (15, '\xa5'): 15,
  (15, '\xa6'): 15,
  (15, '\xa7'): 15,
  (15, '\xa8'): 15,
  (15, '\xa9'): 15,
  (15, '\xaa'): 15,
  (15, '\xab'): 15,
  (15, '\xac'): 15,
  (15, '\xad'): 15,
  (15, '\xae'): 15,
  (15, '\xaf'): 15,
  (15, '\xb0'): 15,
  (15, '\xb1'): 15,
  (15, '\xb2'): 15,
  (15, '\xb3'): 15,
  (15, '\xb4'): 15,
  (15, '\xb5'): 15,
  (15, '\xb6'): 15,
  (15, '\xb7'): 15,
  (15, '\xb8'): 15,
  (15, '\xb9'): 15,
  (15, '\xba'): 15,
  (15, '\xbb'): 15,
  (15, '\xbc'): 15,
  (15, '\xbd'): 15,
  (15, '\xbe'): 15,
  (15, '\xbf'): 15,
  (15, '\xc0'): 15,
  (15, '\xc1'): 15,
  (15, '\xc2'): 15,
  (15, '\xc3'): 15,
  (15, '\xc4'): 15,
  (15, '\xc5'): 15,
  (15, '\xc6'): 15,
  (15, '\xc7'): 15,
  (15, '\xc8'): 15,
  (15, '\xc9'): 15,
  (15, '\xca'): 15,
  (15, '\xcb'): 15,
  (15, '\xcc'): 15,
  (15, '\xcd'): 15,
  (15, '\xce'): 15,
  (15, '\xcf'): 15,
  (15, '\xd0'): 15,
  (15, '\xd1'): 15,
  (15, '\xd2'): 15,
  (15, '\xd3'): 15,
  (15, '\xd4'): 15,
  (15, '\xd5'): 15,
  (15, '\xd6'): 15,
  (15, '\xd7'): 15,
  (15, '\xd8'): 15,
  (15, '\xd9'): 15,
  (15, '\xda'): 15,
  (15, '\xdb'): 15,
  (15, '\xdc'): 15,
  (15, '\xdd'): 15,
  (15, '\xde'): 15,
  (15, '\xdf'): 15,
  (15, '\xe0'): 15,
  (15, '\xe1'): 15,
  (15, '\xe2'): 15,
  (15, '\xe3'): 15,
  (15, '\xe4'): 15,
  (15, '\xe5'): 15,
  (15, '\xe6'): 15,
  (15, '\xe7'): 15,
  (15, '\xe8'): 15,
  (15, '\xe9'): 15,
  (15, '\xea'): 15,
  (15, '\xeb'): 15,
  (15, '\xec'): 15,
  (15, '\xed'): 15,
  (15, '\xee'): 15,
  (15, '\xef'): 15,
  (15, '\xf0'): 15,
  (15, '\xf1'): 15,
  (15, '\xf2'): 15,
  (15, '\xf3'): 15,
  (15, '\xf4'): 15,
  (15, '\xf5'): 15,
  (15, '\xf6'): 15,
  (15, '\xf7'): 15,
  (15, '\xf8'): 15,
  (15, '\xf9'): 15,
  (15, '\xfa'): 15,
  (15, '\xfb'): 15,
  (15, '\xfc'): 15,
  (15, '\xfd'): 15,
  (15, '\xfe'): 15,
  (15, '\xff'): 15,
  (16, '+'): 86,
  (16, '='): 87,
  (17, '*'): 82,
  (17, '/'): 14,
  (17, '='): 83,
  (19, '>'): 81,
  (21, '0'): 10,
  (21, '1'): 10,
  (21, '2'): 10,
  (21, '3'): 10,
  (21, '4'): 10,
  (21, '5'): 10,
  (21, '6'): 10,
  (21, '7'): 10,
  (21, '8'): 10,
  (21, '9'): 10,
  (21, 'A'): 10,
  (21, 'B'): 10,
  (21, 'C'): 10,
  (21, 'D'): 10,
  (21, 'E'): 10,
  (21, 'F'): 10,
  (21, 'G'): 10,
  (21, 'H'): 10,
  (21, 'I'): 10,
  (21, 'J'): 10,
  (21, 'K'): 10,
  (21, 'L'): 10,
  (21, 'M'): 10,
  (21, 'N'): 10,
  (21, 'O'): 10,
  (21, 'P'): 10,
  (21, 'Q'): 10,
  (21, 'R'): 10,
  (21, 'S'): 10,
  (21, 'T'): 10,
  (21, 'U'): 10,
  (21, 'V'): 10,
  (21, 'W'): 10,
  (21, 'X'): 10,
  (21, 'Y'): 10,
  (21, 'Z'): 10,
  (21, '_'): 10,
  (21, 'a'): 10,
  (21, 'b'): 10,
  (21, 'c'): 10,
  (21, 'd'): 10,
  (21, 'e'): 10,
  (21, 'f'): 10,
  (21, 'g'): 10,
  (21, 'h'): 72,
  (21, 'i'): 10,
  (21, 'j'): 10,
  (21, 'k'): 10,
  (21, 'l'): 10,
  (21, 'm'): 10,
  (21, 'n'): 10,
  (21, 'o'): 10,
  (21, 'p'): 10,
  (21, 'q'): 10,
  (21, 'r'): 10,
  (21, 's'): 10,
  (21, 't'): 10,
  (21, 'u'): 10,
  (21, 'v'): 10,
  (21, 'w'): 10,
  (21, 'x'): 10,
  (21, 'y'): 10,
  (21, 'z'): 10,
  (24, '\x00'): 52,
  (24, '\x01'): 52,
  (24, '\x02'): 52,
  (24, '\x03'): 52,
  (24, '\x04'): 52,
  (24, '\x05'): 52,
  (24, '\x06'): 52,
  (24, '\x07'): 52,
  (24, '\x08'): 52,
  (24, '\t'): 52,
  (24, '\n'): 52,
  (24, '\x0b'): 52,
  (24, '\x0c'): 52,
  (24, '\r'): 52,
  (24, '\x0e'): 52,
  (24, '\x0f'): 52,
  (24, '\x10'): 52,
  (24, '\x11'): 52,
  (24, '\x12'): 52,
  (24, '\x13'): 52,
  (24, '\x14'): 52,
  (24, '\x15'): 52,
  (24, '\x16'): 52,
  (24, '\x17'): 52,
  (24, '\x18'): 52,
  (24, '\x19'): 52,
  (24, '\x1a'): 52,
  (24, '\x1b'): 52,
  (24, '\x1c'): 52,
  (24, '\x1d'): 52,
  (24, '\x1e'): 52,
  (24, '\x1f'): 52,
  (24, ' '): 52,
  (24, '!'): 52,
  (24, '"'): 58,
  (24, '#'): 52,
  (24, '$'): 52,
  (24, '%'): 52,
  (24, '&'): 52,
  (24, "'"): 52,
  (24, '('): 52,
  (24, ')'): 52,
  (24, '*'): 52,
  (24, '+'): 52,
  (24, ','): 52,
  (24, '-'): 52,
  (24, '.'): 52,
  (24, '/'): 52,
  (24, '0'): 52,
  (24, '1'): 52,
  (24, '2'): 52,
  (24, '3'): 52,
  (24, '4'): 52,
  (24, '5'): 52,
  (24, '6'): 52,
  (24, '7'): 52,
  (24, '8'): 52,
  (24, '9'): 52,
  (24, ':'): 52,
  (24, ';'): 52,
  (24, '<'): 52,
  (24, '='): 52,
  (24, '>'): 52,
  (24, '?'): 52,
  (24, '@'): 52,
  (24, 'A'): 52,
  (24, 'B'): 52,
  (24, 'C'): 52,
  (24, 'D'): 52,
  (24, 'E'): 52,
  (24, 'F'): 52,
  (24, 'G'): 52,
  (24, 'H'): 52,
  (24, 'I'): 52,
  (24, 'J'): 52,
  (24, 'K'): 52,
  (24, 'L'): 52,
  (24, 'M'): 52,
  (24, 'N'): 52,
  (24, 'O'): 52,
  (24, 'P'): 52,
  (24, 'Q'): 52,
  (24, 'R'): 52,
  (24, 'S'): 52,
  (24, 'T'): 52,
  (24, 'U'): 52,
  (24, 'V'): 52,
  (24, 'W'): 52,
  (24, 'X'): 52,
  (24, 'Y'): 52,
  (24, 'Z'): 52,
  (24, '['): 52,
  (24, '\\'): 57,
  (24, ']'): 52,
  (24, '^'): 52,
  (24, '_'): 52,
  (24, '`'): 52,
  (24, 'a'): 52,
  (24, 'b'): 52,
  (24, 'c'): 52,
  (24, 'd'): 52,
  (24, 'e'): 52,
  (24, 'f'): 52,
  (24, 'g'): 52,
  (24, 'h'): 52,
  (24, 'i'): 52,
  (24, 'j'): 52,
  (24, 'k'): 52,
  (24, 'l'): 52,
  (24, 'm'): 52,
  (24, 'n'): 52,
  (24, 'o'): 52,
  (24, 'p'): 52,
  (24, 'q'): 52,
  (24, 'r'): 52,
  (24, 's'): 52,
  (24, 't'): 52,
  (24, 'u'): 52,
  (24, 'v'): 52,
  (24, 'w'): 52,
  (24, 'x'): 52,
  (24, 'y'): 52,
  (24, 'z'): 52,
  (24, '{'): 52,
  (24, '|'): 52,
  (24, '}'): 52,
  (24, '~'): 52,
  (24, '\x7f'): 52,
  (24, '\x80'): 52,
  (24, '\x81'): 52,
  (24, '\x82'): 52,
  (24, '\x83'): 52,
  (24, '\x84'): 52,
  (24, '\x85'): 52,
  (24, '\x86'): 52,
  (24, '\x87'): 52,
  (24, '\x88'): 52,
  (24, '\x89'): 52,
  (24, '\x8a'): 52,
  (24, '\x8b'): 52,
  (24, '\x8c'): 52,
  (24, '\x8d'): 52,
  (24, '\x8e'): 52,
  (24, '\x8f'): 52,
  (24, '\x90'): 52,
  (24, '\x91'): 52,
  (24, '\x92'): 52,
  (24, '\x93'): 52,
  (24, '\x94'): 52,
  (24, '\x95'): 52,
  (24, '\x96'): 52,
  (24, '\x97'): 52,
  (24, '\x98'): 52,
  (24, '\x99'): 52,
  (24, '\x9a'): 52,
  (24, '\x9b'): 52,
  (24, '\x9c'): 52,
  (24, '\x9d'): 52,
  (24, '\x9e'): 52,
  (24, '\x9f'): 52,
  (24, '\xa0'): 52,
  (24, '\xa1'): 52,
  (24, '\xa2'): 52,
  (24, '\xa3'): 52,
  (24, '\xa4'): 52,
  (24, '\xa5'): 52,
  (24, '\xa6'): 52,
  (24, '\xa7'): 52,
  (24, '\xa8'): 52,
  (24, '\xa9'): 52,
  (24, '\xaa'): 52,
  (24, '\xab'): 52,
  (24, '\xac'): 52,
  (24, '\xad'): 52,
  (24, '\xae'): 52,
  (24, '\xaf'): 52,
  (24, '\xb0'): 52,
  (24, '\xb1'): 52,
  (24, '\xb2'): 52,
  (24, '\xb3'): 52,
  (24, '\xb4'): 52,
  (24, '\xb5'): 52,
  (24, '\xb6'): 52,
  (24, '\xb7'): 52,
  (24, '\xb8'): 52,
  (24, '\xb9'): 52,
  (24, '\xba'): 52,
  (24, '\xbb'): 52,
  (24, '\xbc'): 52,
  (24, '\xbd'): 52,
  (24, '\xbe'): 52,
  (24, '\xbf'): 52,
  (24, '\xc0'): 52,
  (24, '\xc1'): 52,
  (24, '\xc2'): 52,
  (24, '\xc3'): 52,
  (24, '\xc4'): 52,
  (24, '\xc5'): 52,
  (24, '\xc6'): 52,
  (24, '\xc7'): 52,
  (24, '\xc8'): 52,
  (24, '\xc9'): 52,
  (24, '\xca'): 52,
  (24, '\xcb'): 52,
  (24, '\xcc'): 52,
  (24, '\xcd'): 52,
  (24, '\xce'): 52,
  (24, '\xcf'): 52,
  (24, '\xd0'): 52,
  (24, '\xd1'): 52,
  (24, '\xd2'): 52,
  (24, '\xd3'): 52,
  (24, '\xd4'): 52,
  (24, '\xd5'): 52,
  (24, '\xd6'): 52,
  (24, '\xd7'): 52,
  (24, '\xd8'): 52,
  (24, '\xd9'): 52,
  (24, '\xda'): 52,
  (24, '\xdb'): 52,
  (24, '\xdc'): 52,
  (24, '\xdd'): 52,
  (24, '\xde'): 52,
  (24, '\xdf'): 52,
  (24, '\xe0'): 52,
  (24, '\xe1'): 52,
  (24, '\xe2'): 52,
  (24, '\xe3'): 52,
  (24, '\xe4'): 52,
  (24, '\xe5'): 52,
  (24, '\xe6'): 52,
  (24, '\xe7'): 52,
  (24, '\xe8'): 52,
  (24, '\xe9'): 52,
  (24, '\xea'): 52,
  (24, '\xeb'): 52,
  (24, '\xec'): 52,
  (24, '\xed'): 52,
  (24, '\xee'): 52,
  (24, '\xef'): 52,
  (24, '\xf0'): 52,
  (24, '\xf1'): 52,
  (24, '\xf2'): 52,
  (24, '\xf3'): 52,
  (24, '\xf4'): 52,
  (24, '\xf5'): 52,
  (24, '\xf6'): 52,
  (24, '\xf7'): 52,
  (24, '\xf8'): 52,
  (24, '\xf9'): 52,
  (24, '\xfa'): 52,
  (24, '\xfb'): 52,
  (24, '\xfc'): 52,
  (24, '\xfd'): 52,
  (24, '\xfe'): 52,
  (24, '\xff'): 52,
  (25, '&'): 71,
  (25, '='): 70,
  (26, '='): 69,
  (27, '0'): 65,
  (27, '1'): 65,
  (27, '2'): 65,
  (27, '3'): 65,
  (27, '4'): 65,
  (27, '5'): 65,
  (27, '6'): 65,
  (27, '7'): 65,
  (27, '8'): 65,
  (27, '9'): 65,
  (27, '='): 66,
  (27, 'E'): 64,
  (27, 'e'): 64,
  (28, ':'): 63,
  (29, '='): 60,
  (29, '>'): 61,
  (30, '='): 59,
  (31, '"'): 52,
  (31, "'"): 15,
  (31, '0'): 10,
  (31, '1'): 10,
  (31, '2'): 10,
  (31, '3'): 10,
  (31, '4'): 10,
  (31, '5'): 10,
  (31, '6'): 10,
  (31, '7'): 10,
  (31, '8'): 10,
  (31, '9'): 10,
  (31, '<'): 53,
  (31, 'A'): 10,
  (31, 'B'): 10,
  (31, 'C'): 10,
  (31, 'D'): 10,
  (31, 'E'): 10,
  (31, 'F'): 10,
  (31, 'G'): 10,
  (31, 'H'): 10,
  (31, 'I'): 10,
  (31, 'J'): 10,
  (31, 'K'): 10,
  (31, 'L'): 10,
  (31, 'M'): 10,
  (31, 'N'): 10,
  (31, 'O'): 10,
  (31, 'P'): 10,
  (31, 'Q'): 10,
  (31, 'R'): 10,
  (31, 'S'): 10,
  (31, 'T'): 10,
  (31, 'U'): 10,
  (31, 'V'): 10,
  (31, 'W'): 10,
  (31, 'X'): 10,
  (31, 'Y'): 10,
  (31, 'Z'): 10,
  (31, '_'): 10,
  (31, 'a'): 10,
  (31, 'b'): 10,
  (31, 'c'): 10,
  (31, 'd'): 10,
  (31, 'e'): 10,
  (31, 'f'): 10,
  (31, 'g'): 10,
  (31, 'h'): 10,
  (31, 'i'): 10,
  (31, 'j'): 10,
  (31, 'k'): 10,
  (31, 'l'): 10,
  (31, 'm'): 10,
  (31, 'n'): 10,
  (31, 'o'): 10,
  (31, 'p'): 10,
  (31, 'q'): 10,
  (31, 'r'): 10,
  (31, 's'): 10,
  (31, 't'): 10,
  (31, 'u'): 10,
  (31, 'v'): 10,
  (31, 'w'): 10,
  (31, 'x'): 10,
  (31, 'y'): 10,
  (31, 'z'): 10,
  (34, '\n'): 51,
  (35, '='): 49,
  (36, '='): 48,
  (38, '-'): 45,
  (38, '='): 46,
  (38, '>'): 47,
  (39, '='): 42,
  (39, '>'): 43,
  (42, '='): 44,
  (49, '='): 50,
  (52, '\x00'): 52,
  (52, '\x01'): 52,
  (52, '\x02'): 52,
  (52, '\x03'): 52,
  (52, '\x04'): 52,
  (52, '\x05'): 52,
  (52, '\x06'): 52,
  (52, '\x07'): 52,
  (52, '\x08'): 52,
  (52, '\t'): 52,
  (52, '\n'): 52,
  (52, '\x0b'): 52,
  (52, '\x0c'): 52,
  (52, '\r'): 52,
  (52, '\x0e'): 52,
  (52, '\x0f'): 52,
  (52, '\x10'): 52,
  (52, '\x11'): 52,
  (52, '\x12'): 52,
  (52, '\x13'): 52,
  (52, '\x14'): 52,
  (52, '\x15'): 52,
  (52, '\x16'): 52,
  (52, '\x17'): 52,
  (52, '\x18'): 52,
  (52, '\x19'): 52,
  (52, '\x1a'): 52,
  (52, '\x1b'): 52,
  (52, '\x1c'): 52,
  (52, '\x1d'): 52,
  (52, '\x1e'): 52,
  (52, '\x1f'): 52,
  (52, ' '): 52,
  (52, '!'): 52,
  (52, '"'): 58,
  (52, '#'): 52,
  (52, '$'): 52,
  (52, '%'): 52,
  (52, '&'): 52,
  (52, "'"): 52,
  (52, '('): 52,
  (52, ')'): 52,
  (52, '*'): 52,
  (52, '+'): 52,
  (52, ','): 52,
  (52, '-'): 52,
  (52, '.'): 52,
  (52, '/'): 52,
  (52, '0'): 52,
  (52, '1'): 52,
  (52, '2'): 52,
  (52, '3'): 52,
  (52, '4'): 52,
  (52, '5'): 52,
  (52, '6'): 52,
  (52, '7'): 52,
  (52, '8'): 52,
  (52, '9'): 52,
  (52, ':'): 52,
  (52, ';'): 52,
  (52, '<'): 52,
  (52, '='): 52,
  (52, '>'): 52,
  (52, '?'): 52,
  (52, '@'): 52,
  (52, 'A'): 52,
  (52, 'B'): 52,
  (52, 'C'): 52,
  (52, 'D'): 52,
  (52, 'E'): 52,
  (52, 'F'): 52,
  (52, 'G'): 52,
  (52, 'H'): 52,
  (52, 'I'): 52,
  (52, 'J'): 52,
  (52, 'K'): 52,
  (52, 'L'): 52,
  (52, 'M'): 52,
  (52, 'N'): 52,
  (52, 'O'): 52,
  (52, 'P'): 52,
  (52, 'Q'): 52,
  (52, 'R'): 52,
  (52, 'S'): 52,
  (52, 'T'): 52,
  (52, 'U'): 52,
  (52, 'V'): 52,
  (52, 'W'): 52,
  (52, 'X'): 52,
  (52, 'Y'): 52,
  (52, 'Z'): 52,
  (52, '['): 52,
  (52, '\\'): 57,
  (52, ']'): 52,
  (52, '^'): 52,
  (52, '_'): 52,
  (52, '`'): 52,
  (52, 'a'): 52,
  (52, 'b'): 52,
  (52, 'c'): 52,
  (52, 'd'): 52,
  (52, 'e'): 52,
  (52, 'f'): 52,
  (52, 'g'): 52,
  (52, 'h'): 52,
  (52, 'i'): 52,
  (52, 'j'): 52,
  (52, 'k'): 52,
  (52, 'l'): 52,
  (52, 'm'): 52,
  (52, 'n'): 52,
  (52, 'o'): 52,
  (52, 'p'): 52,
  (52, 'q'): 52,
  (52, 'r'): 52,
  (52, 's'): 52,
  (52, 't'): 52,
  (52, 'u'): 52,
  (52, 'v'): 52,
  (52, 'w'): 52,
  (52, 'x'): 52,
  (52, 'y'): 52,
  (52, 'z'): 52,
  (52, '{'): 52,
  (52, '|'): 52,
  (52, '}'): 52,
  (52, '~'): 52,
  (52, '\x7f'): 52,
  (52, '\x80'): 52,
  (52, '\x81'): 52,
  (52, '\x82'): 52,
  (52, '\x83'): 52,
  (52, '\x84'): 52,
  (52, '\x85'): 52,
  (52, '\x86'): 52,
  (52, '\x87'): 52,
  (52, '\x88'): 52,
  (52, '\x89'): 52,
  (52, '\x8a'): 52,
  (52, '\x8b'): 52,
  (52, '\x8c'): 52,
  (52, '\x8d'): 52,
  (52, '\x8e'): 52,
  (52, '\x8f'): 52,
  (52, '\x90'): 52,
  (52, '\x91'): 52,
  (52, '\x92'): 52,
  (52, '\x93'): 52,
  (52, '\x94'): 52,
  (52, '\x95'): 52,
  (52, '\x96'): 52,
  (52, '\x97'): 52,
  (52, '\x98'): 52,
  (52, '\x99'): 52,
  (52, '\x9a'): 52,
  (52, '\x9b'): 52,
  (52, '\x9c'): 52,
  (52, '\x9d'): 52,
  (52, '\x9e'): 52,
  (52, '\x9f'): 52,
  (52, '\xa0'): 52,
  (52, '\xa1'): 52,
  (52, '\xa2'): 52,
  (52, '\xa3'): 52,
  (52, '\xa4'): 52,
  (52, '\xa5'): 52,
  (52, '\xa6'): 52,
  (52, '\xa7'): 52,
  (52, '\xa8'): 52,
  (52, '\xa9'): 52,
  (52, '\xaa'): 52,
  (52, '\xab'): 52,
  (52, '\xac'): 52,
  (52, '\xad'): 52,
  (52, '\xae'): 52,
  (52, '\xaf'): 52,
  (52, '\xb0'): 52,
  (52, '\xb1'): 52,
  (52, '\xb2'): 52,
  (52, '\xb3'): 52,
  (52, '\xb4'): 52,
  (52, '\xb5'): 52,
  (52, '\xb6'): 52,
  (52, '\xb7'): 52,
  (52, '\xb8'): 52,
  (52, '\xb9'): 52,
  (52, '\xba'): 52,
  (52, '\xbb'): 52,
  (52, '\xbc'): 52,
  (52, '\xbd'): 52,
  (52, '\xbe'): 52,
  (52, '\xbf'): 52,
  (52, '\xc0'): 52,
  (52, '\xc1'): 52,
  (52, '\xc2'): 52,
  (52, '\xc3'): 52,
  (52, '\xc4'): 52,
  (52, '\xc5'): 52,
  (52, '\xc6'): 52,
  (52, '\xc7'): 52,
  (52, '\xc8'): 52,
  (52, '\xc9'): 52,
  (52, '\xca'): 52,
  (52, '\xcb'): 52,
  (52, '\xcc'): 52,
  (52, '\xcd'): 52,
  (52, '\xce'): 52,
  (52, '\xcf'): 52,
  (52, '\xd0'): 52,
  (52, '\xd1'): 52,
  (52, '\xd2'): 52,
  (52, '\xd3'): 52,
  (52, '\xd4'): 52,
  (52, '\xd5'): 52,
  (52, '\xd6'): 52,
  (52, '\xd7'): 52,
  (52, '\xd8'): 52,
  (52, '\xd9'): 52,
  (52, '\xda'): 52,
  (52, '\xdb'): 52,
  (52, '\xdc'): 52,
  (52, '\xdd'): 52,
  (52, '\xde'): 52,
  (52, '\xdf'): 52,
  (52, '\xe0'): 52,
  (52, '\xe1'): 52,
  (52, '\xe2'): 52,
  (52, '\xe3'): 52,
  (52, '\xe4'): 52,
  (52, '\xe5'): 52,
  (52, '\xe6'): 52,
  (52, '\xe7'): 52,
  (52, '\xe8'): 52,
  (52, '\xe9'): 52,
  (52, '\xea'): 52,
  (52, '\xeb'): 52,
  (52, '\xec'): 52,
  (52, '\xed'): 52,
  (52, '\xee'): 52,
  (52, '\xef'): 52,
  (52, '\xf0'): 52,
  (52, '\xf1'): 52,
  (52, '\xf2'): 52,
  (52, '\xf3'): 52,
  (52, '\xf4'): 52,
  (52, '\xf5'): 52,
  (52, '\xf6'): 52,
  (52, '\xf7'): 52,
  (52, '\xf8'): 52,
  (52, '\xf9'): 52,
  (52, '\xfa'): 52,
  (52, '\xfb'): 52,
  (52, '\xfc'): 52,
  (52, '\xfd'): 52,
  (52, '\xfe'): 52,
  (52, '\xff'): 52,
  (53, '<'): 54,
  (54, '<'): 55,
  (55, '\x00'): 55,
  (55, '\x01'): 55,
  (55, '\x02'): 55,
  (55, '\x03'): 55,
  (55, '\x04'): 55,
  (55, '\x05'): 55,
  (55, '\x06'): 55,
  (55, '\x07'): 55,
  (55, '\x08'): 55,
  (55, '\t'): 55,
  (55, '\n'): 56,
  (55, '\x0b'): 55,
  (55, '\x0c'): 55,
  (55, '\r'): 55,
  (55, '\x0e'): 55,
  (55, '\x0f'): 55,
  (55, '\x10'): 55,
  (55, '\x11'): 55,
  (55, '\x12'): 55,
  (55, '\x13'): 55,
  (55, '\x14'): 55,
  (55, '\x15'): 55,
  (55, '\x16'): 55,
  (55, '\x17'): 55,
  (55, '\x18'): 55,
  (55, '\x19'): 55,
  (55, '\x1a'): 55,
  (55, '\x1b'): 55,
  (55, '\x1c'): 55,
  (55, '\x1d'): 55,
  (55, '\x1e'): 55,
  (55, '\x1f'): 55,
  (55, ' '): 55,
  (55, '!'): 55,
  (55, '"'): 55,
  (55, '#'): 55,
  (55, '$'): 55,
  (55, '%'): 55,
  (55, '&'): 55,
  (55, "'"): 55,
  (55, '('): 55,
  (55, ')'): 55,
  (55, '*'): 55,
  (55, '+'): 55,
  (55, ','): 55,
  (55, '-'): 55,
  (55, '.'): 55,
  (55, '/'): 55,
  (55, '0'): 55,
  (55, '1'): 55,
  (55, '2'): 55,
  (55, '3'): 55,
  (55, '4'): 55,
  (55, '5'): 55,
  (55, '6'): 55,
  (55, '7'): 55,
  (55, '8'): 55,
  (55, '9'): 55,
  (55, ':'): 55,
  (55, ';'): 55,
  (55, '<'): 55,
  (55, '='): 55,
  (55, '>'): 55,
  (55, '?'): 55,
  (55, '@'): 55,
  (55, 'A'): 55,
  (55, 'B'): 55,
  (55, 'C'): 55,
  (55, 'D'): 55,
  (55, 'E'): 55,
  (55, 'F'): 55,
  (55, 'G'): 55,
  (55, 'H'): 55,
  (55, 'I'): 55,
  (55, 'J'): 55,
  (55, 'K'): 55,
  (55, 'L'): 55,
  (55, 'M'): 55,
  (55, 'N'): 55,
  (55, 'O'): 55,
  (55, 'P'): 55,
  (55, 'Q'): 55,
  (55, 'R'): 55,
  (55, 'S'): 55,
  (55, 'T'): 55,
  (55, 'U'): 55,
  (55, 'V'): 55,
  (55, 'W'): 55,
  (55, 'X'): 55,
  (55, 'Y'): 55,
  (55, 'Z'): 55,
  (55, '['): 55,
  (55, '\\'): 55,
  (55, ']'): 55,
  (55, '^'): 55,
  (55, '_'): 55,
  (55, '`'): 55,
  (55, 'a'): 55,
  (55, 'b'): 55,
  (55, 'c'): 55,
  (55, 'd'): 55,
  (55, 'e'): 55,
  (55, 'f'): 55,
  (55, 'g'): 55,
  (55, 'h'): 55,
  (55, 'i'): 55,
  (55, 'j'): 55,
  (55, 'k'): 55,
  (55, 'l'): 55,
  (55, 'm'): 55,
  (55, 'n'): 55,
  (55, 'o'): 55,
  (55, 'p'): 55,
  (55, 'q'): 55,
  (55, 'r'): 55,
  (55, 's'): 55,
  (55, 't'): 55,
  (55, 'u'): 55,
  (55, 'v'): 55,
  (55, 'w'): 55,
  (55, 'x'): 55,
  (55, 'y'): 55,
  (55, 'z'): 55,
  (55, '{'): 55,
  (55, '|'): 55,
  (55, '}'): 55,
  (55, '~'): 55,
  (55, '\x7f'): 55,
  (55, '\x80'): 55,
  (55, '\x81'): 55,
  (55, '\x82'): 55,
  (55, '\x83'): 55,
  (55, '\x84'): 55,
  (55, '\x85'): 55,
  (55, '\x86'): 55,
  (55, '\x87'): 55,
  (55, '\x88'): 55,
  (55, '\x89'): 55,
  (55, '\x8a'): 55,
  (55, '\x8b'): 55,
  (55, '\x8c'): 55,
  (55, '\x8d'): 55,
  (55, '\x8e'): 55,
  (55, '\x8f'): 55,
  (55, '\x90'): 55,
  (55, '\x91'): 55,
  (55, '\x92'): 55,
  (55, '\x93'): 55,
  (55, '\x94'): 55,
  (55, '\x95'): 55,
  (55, '\x96'): 55,
  (55, '\x97'): 55,
  (55, '\x98'): 55,
  (55, '\x99'): 55,
  (55, '\x9a'): 55,
  (55, '\x9b'): 55,
  (55, '\x9c'): 55,
  (55, '\x9d'): 55,
  (55, '\x9e'): 55,
  (55, '\x9f'): 55,
  (55, '\xa0'): 55,
  (55, '\xa1'): 55,
  (55, '\xa2'): 55,
  (55, '\xa3'): 55,
  (55, '\xa4'): 55,
  (55, '\xa5'): 55,
  (55, '\xa6'): 55,
  (55, '\xa7'): 55,
  (55, '\xa8'): 55,
  (55, '\xa9'): 55,
  (55, '\xaa'): 55,
  (55, '\xab'): 55,
  (55, '\xac'): 55,
  (55, '\xad'): 55,
  (55, '\xae'): 55,
  (55, '\xaf'): 55,
  (55, '\xb0'): 55,
  (55, '\xb1'): 55,
  (55, '\xb2'): 55,
  (55, '\xb3'): 55,
  (55, '\xb4'): 55,
  (55, '\xb5'): 55,
  (55, '\xb6'): 55,
  (55, '\xb7'): 55,
  (55, '\xb8'): 55,
  (55, '\xb9'): 55,
  (55, '\xba'): 55,
  (55, '\xbb'): 55,
  (55, '\xbc'): 55,
  (55, '\xbd'): 55,
  (55, '\xbe'): 55,
  (55, '\xbf'): 55,
  (55, '\xc0'): 55,
  (55, '\xc1'): 55,
  (55, '\xc2'): 55,
  (55, '\xc3'): 55,
  (55, '\xc4'): 55,
  (55, '\xc5'): 55,
  (55, '\xc6'): 55,
  (55, '\xc7'): 55,
  (55, '\xc8'): 55,
  (55, '\xc9'): 55,
  (55, '\xca'): 55,
  (55, '\xcb'): 55,
  (55, '\xcc'): 55,
  (55, '\xcd'): 55,
  (55, '\xce'): 55,
  (55, '\xcf'): 55,
  (55, '\xd0'): 55,
  (55, '\xd1'): 55,
  (55, '\xd2'): 55,
  (55, '\xd3'): 55,
  (55, '\xd4'): 55,
  (55, '\xd5'): 55,
  (55, '\xd6'): 55,
  (55, '\xd7'): 55,
  (55, '\xd8'): 55,
  (55, '\xd9'): 55,
  (55, '\xda'): 55,
  (55, '\xdb'): 55,
  (55, '\xdc'): 55,
  (55, '\xdd'): 55,
  (55, '\xde'): 55,
  (55, '\xdf'): 55,
  (55, '\xe0'): 55,
  (55, '\xe1'): 55,
  (55, '\xe2'): 55,
  (55, '\xe3'): 55,
  (55, '\xe4'): 55,
  (55, '\xe5'): 55,
  (55, '\xe6'): 55,
  (55, '\xe7'): 55,
  (55, '\xe8'): 55,
  (55, '\xe9'): 55,
  (55, '\xea'): 55,
  (55, '\xeb'): 55,
  (55, '\xec'): 55,
  (55, '\xed'): 55,
  (55, '\xee'): 55,
  (55, '\xef'): 55,
  (55, '\xf0'): 55,
  (55, '\xf1'): 55,
  (55, '\xf2'): 55,
  (55, '\xf3'): 55,
  (55, '\xf4'): 55,
  (55, '\xf5'): 55,
  (55, '\xf6'): 55,
  (55, '\xf7'): 55,
  (55, '\xf8'): 55,
  (55, '\xf9'): 55,
  (55, '\xfa'): 55,
  (55, '\xfb'): 55,
  (55, '\xfc'): 55,
  (55, '\xfd'): 55,
  (55, '\xfe'): 55,
  (55, '\xff'): 55,
  (57, '\x00'): 52,
  (57, '\x01'): 52,
  (57, '\x02'): 52,
  (57, '\x03'): 52,
  (57, '\x04'): 52,
  (57, '\x05'): 52,
  (57, '\x06'): 52,
  (57, '\x07'): 52,
  (57, '\x08'): 52,
  (57, '\t'): 52,
  (57, '\n'): 52,
  (57, '\x0b'): 52,
  (57, '\x0c'): 52,
  (57, '\r'): 52,
  (57, '\x0e'): 52,
  (57, '\x0f'): 52,
  (57, '\x10'): 52,
  (57, '\x11'): 52,
  (57, '\x12'): 52,
  (57, '\x13'): 52,
  (57, '\x14'): 52,
  (57, '\x15'): 52,
  (57, '\x16'): 52,
  (57, '\x17'): 52,
  (57, '\x18'): 52,
  (57, '\x19'): 52,
  (57, '\x1a'): 52,
  (57, '\x1b'): 52,
  (57, '\x1c'): 52,
  (57, '\x1d'): 52,
  (57, '\x1e'): 52,
  (57, '\x1f'): 52,
  (57, ' '): 52,
  (57, '!'): 52,
  (57, '"'): 52,
  (57, '#'): 52,
  (57, '$'): 52,
  (57, '%'): 52,
  (57, '&'): 52,
  (57, "'"): 52,
  (57, '('): 52,
  (57, ')'): 52,
  (57, '*'): 52,
  (57, '+'): 52,
  (57, ','): 52,
  (57, '-'): 52,
  (57, '.'): 52,
  (57, '/'): 52,
  (57, '0'): 52,
  (57, '1'): 52,
  (57, '2'): 52,
  (57, '3'): 52,
  (57, '4'): 52,
  (57, '5'): 52,
  (57, '6'): 52,
  (57, '7'): 52,
  (57, '8'): 52,
  (57, '9'): 52,
  (57, ':'): 52,
  (57, ';'): 52,
  (57, '<'): 52,
  (57, '='): 52,
  (57, '>'): 52,
  (57, '?'): 52,
  (57, '@'): 52,
  (57, 'A'): 52,
  (57, 'B'): 52,
  (57, 'C'): 52,
  (57, 'D'): 52,
  (57, 'E'): 52,
  (57, 'F'): 52,
  (57, 'G'): 52,
  (57, 'H'): 52,
  (57, 'I'): 52,
  (57, 'J'): 52,
  (57, 'K'): 52,
  (57, 'L'): 52,
  (57, 'M'): 52,
  (57, 'N'): 52,
  (57, 'O'): 52,
  (57, 'P'): 52,
  (57, 'Q'): 52,
  (57, 'R'): 52,
  (57, 'S'): 52,
  (57, 'T'): 52,
  (57, 'U'): 52,
  (57, 'V'): 52,
  (57, 'W'): 52,
  (57, 'X'): 52,
  (57, 'Y'): 52,
  (57, 'Z'): 52,
  (57, '['): 52,
  (57, '\\'): 52,
  (57, ']'): 52,
  (57, '^'): 52,
  (57, '_'): 52,
  (57, '`'): 52,
  (57, 'a'): 52,
  (57, 'b'): 52,
  (57, 'c'): 52,
  (57, 'd'): 52,
  (57, 'e'): 52,
  (57, 'f'): 52,
  (57, 'g'): 52,
  (57, 'h'): 52,
  (57, 'i'): 52,
  (57, 'j'): 52,
  (57, 'k'): 52,
  (57, 'l'): 52,
  (57, 'm'): 52,
  (57, 'n'): 52,
  (57, 'o'): 52,
  (57, 'p'): 52,
  (57, 'q'): 52,
  (57, 'r'): 52,
  (57, 's'): 52,
  (57, 't'): 52,
  (57, 'u'): 52,
  (57, 'v'): 52,
  (57, 'w'): 52,
  (57, 'x'): 52,
  (57, 'y'): 52,
  (57, 'z'): 52,
  (57, '{'): 52,
  (57, '|'): 52,
  (57, '}'): 52,
  (57, '~'): 52,
  (57, '\x7f'): 52,
  (57, '\x80'): 52,
  (57, '\x81'): 52,
  (57, '\x82'): 52,
  (57, '\x83'): 52,
  (57, '\x84'): 52,
  (57, '\x85'): 52,
  (57, '\x86'): 52,
  (57, '\x87'): 52,
  (57, '\x88'): 52,
  (57, '\x89'): 52,
  (57, '\x8a'): 52,
  (57, '\x8b'): 52,
  (57, '\x8c'): 52,
  (57, '\x8d'): 52,
  (57, '\x8e'): 52,
  (57, '\x8f'): 52,
  (57, '\x90'): 52,
  (57, '\x91'): 52,
  (57, '\x92'): 52,
  (57, '\x93'): 52,
  (57, '\x94'): 52,
  (57, '\x95'): 52,
  (57, '\x96'): 52,
  (57, '\x97'): 52,
  (57, '\x98'): 52,
  (57, '\x99'): 52,
  (57, '\x9a'): 52,
  (57, '\x9b'): 52,
  (57, '\x9c'): 52,
  (57, '\x9d'): 52,
  (57, '\x9e'): 52,
  (57, '\x9f'): 52,
  (57, '\xa0'): 52,
  (57, '\xa1'): 52,
  (57, '\xa2'): 52,
  (57, '\xa3'): 52,
  (57, '\xa4'): 52,
  (57, '\xa5'): 52,
  (57, '\xa6'): 52,
  (57, '\xa7'): 52,
  (57, '\xa8'): 52,
  (57, '\xa9'): 52,
  (57, '\xaa'): 52,
  (57, '\xab'): 52,
  (57, '\xac'): 52,
  (57, '\xad'): 52,
  (57, '\xae'): 52,
  (57, '\xaf'): 52,
  (57, '\xb0'): 52,
  (57, '\xb1'): 52,
  (57, '\xb2'): 52,
  (57, '\xb3'): 52,
  (57, '\xb4'): 52,
  (57, '\xb5'): 52,
  (57, '\xb6'): 52,
  (57, '\xb7'): 52,
  (57, '\xb8'): 52,
  (57, '\xb9'): 52,
  (57, '\xba'): 52,
  (57, '\xbb'): 52,
  (57, '\xbc'): 52,
  (57, '\xbd'): 52,
  (57, '\xbe'): 52,
  (57, '\xbf'): 52,
  (57, '\xc0'): 52,
  (57, '\xc1'): 52,
  (57, '\xc2'): 52,
  (57, '\xc3'): 52,
  (57, '\xc4'): 52,
  (57, '\xc5'): 52,
  (57, '\xc6'): 52,
  (57, '\xc7'): 52,
  (57, '\xc8'): 52,
  (57, '\xc9'): 52,
  (57, '\xca'): 52,
  (57, '\xcb'): 52,
  (57, '\xcc'): 52,
  (57, '\xcd'): 52,
  (57, '\xce'): 52,
  (57, '\xcf'): 52,
  (57, '\xd0'): 52,
  (57, '\xd1'): 52,
  (57, '\xd2'): 52,
  (57, '\xd3'): 52,
  (57, '\xd4'): 52,
  (57, '\xd5'): 52,
  (57, '\xd6'): 52,
  (57, '\xd7'): 52,
  (57, '\xd8'): 52,
  (57, '\xd9'): 52,
  (57, '\xda'): 52,
  (57, '\xdb'): 52,
  (57, '\xdc'): 52,
  (57, '\xdd'): 52,
  (57, '\xde'): 52,
  (57, '\xdf'): 52,
  (57, '\xe0'): 52,
  (57, '\xe1'): 52,
  (57, '\xe2'): 52,
  (57, '\xe3'): 52,
  (57, '\xe4'): 52,
  (57, '\xe5'): 52,
  (57, '\xe6'): 52,
  (57, '\xe7'): 52,
  (57, '\xe8'): 52,
  (57, '\xe9'): 52,
  (57, '\xea'): 52,
  (57, '\xeb'): 52,
  (57, '\xec'): 52,
  (57, '\xed'): 52,
  (57, '\xee'): 52,
  (57, '\xef'): 52,
  (57, '\xf0'): 52,
  (57, '\xf1'): 52,
  (57, '\xf2'): 52,
  (57, '\xf3'): 52,
  (57, '\xf4'): 52,
  (57, '\xf5'): 52,
  (57, '\xf6'): 52,
  (57, '\xf7'): 52,
  (57, '\xf8'): 52,
  (57, '\xf9'): 52,
  (57, '\xfa'): 52,
  (57, '\xfb'): 52,
  (57, '\xfc'): 52,
  (57, '\xfd'): 52,
  (57, '\xfe'): 52,
  (57, '\xff'): 52,
  (61, '='): 62,
  (64, '+'): 67,
  (64, '-'): 67,
  (64, '0'): 68,
  (64, '1'): 68,
  (64, '2'): 68,
  (64, '3'): 68,
  (64, '4'): 68,
  (64, '5'): 68,
  (64, '6'): 68,
  (64, '7'): 68,
  (64, '8'): 68,
  (64, '9'): 68,
  (65, '0'): 65,
  (65, '1'): 65,
  (65, '2'): 65,
  (65, '3'): 65,
  (65, '4'): 65,
  (65, '5'): 65,
  (65, '6'): 65,
  (65, '7'): 65,
  (65, '8'): 65,
  (65, '9'): 65,
  (65, 'E'): 64,
  (65, 'e'): 64,
  (67, '0'): 68,
  (67, '1'): 68,
  (67, '2'): 68,
  (67, '3'): 68,
  (67, '4'): 68,
  (67, '5'): 68,
  (67, '6'): 68,
  (67, '7'): 68,
  (67, '8'): 68,
  (67, '9'): 68,
  (68, '0'): 68,
  (68, '1'): 68,
  (68, '2'): 68,
  (68, '3'): 68,
  (68, '4'): 68,
  (68, '5'): 68,
  (68, '6'): 68,
  (68, '7'): 68,
  (68, '8'): 68,
  (68, '9'): 68,
  (72, '0'): 10,
  (72, '1'): 10,
  (72, '2'): 10,
  (72, '3'): 10,
  (72, '4'): 10,
  (72, '5'): 10,
  (72, '6'): 10,
  (72, '7'): 10,
  (72, '8'): 10,
  (72, '9'): 10,
  (72, 'A'): 10,
  (72, 'B'): 10,
  (72, 'C'): 10,
  (72, 'D'): 10,
  (72, 'E'): 10,
  (72, 'F'): 10,
  (72, 'G'): 10,
  (72, 'H'): 10,
  (72, 'I'): 10,
  (72, 'J'): 10,
  (72, 'K'): 10,
  (72, 'L'): 10,
  (72, 'M'): 10,
  (72, 'N'): 10,
  (72, 'O'): 10,
  (72, 'P'): 10,
  (72, 'Q'): 10,
  (72, 'R'): 10,
  (72, 'S'): 10,
  (72, 'T'): 10,
  (72, 'U'): 10,
  (72, 'V'): 10,
  (72, 'W'): 10,
  (72, 'X'): 10,
  (72, 'Y'): 10,
  (72, 'Z'): 10,
  (72, '_'): 10,
  (72, 'a'): 10,
  (72, 'b'): 10,
  (72, 'c'): 10,
  (72, 'd'): 10,
  (72, 'e'): 10,
  (72, 'f'): 10,
  (72, 'g'): 10,
  (72, 'h'): 10,
  (72, 'i'): 73,
  (72, 'j'): 10,
  (72, 'k'): 10,
  (72, 'l'): 10,
  (72, 'm'): 10,
  (72, 'n'): 10,
  (72, 'o'): 10,
  (72, 'p'): 10,
  (72, 'q'): 10,
  (72, 'r'): 10,
  (72, 's'): 10,
  (72, 't'): 10,
  (72, 'u'): 10,
  (72, 'v'): 10,
  (72, 'w'): 10,
  (72, 'x'): 10,
  (72, 'y'): 10,
  (72, 'z'): 10,
  (73, '0'): 10,
  (73, '1'): 10,
  (73, '2'): 10,
  (73, '3'): 10,
  (73, '4'): 10,
  (73, '5'): 10,
  (73, '6'): 10,
  (73, '7'): 10,
  (73, '8'): 10,
  (73, '9'): 10,
  (73, 'A'): 10,
  (73, 'B'): 10,
  (73, 'C'): 10,
  (73, 'D'): 10,
  (73, 'E'): 10,
  (73, 'F'): 10,
  (73, 'G'): 10,
  (73, 'H'): 10,
  (73, 'I'): 10,
  (73, 'J'): 10,
  (73, 'K'): 10,
  (73, 'L'): 10,
  (73, 'M'): 10,
  (73, 'N'): 10,
  (73, 'O'): 10,
  (73, 'P'): 10,
  (73, 'Q'): 10,
  (73, 'R'): 10,
  (73, 'S'): 10,
  (73, 'T'): 10,
  (73, 'U'): 10,
  (73, 'V'): 10,
  (73, 'W'): 10,
  (73, 'X'): 10,
  (73, 'Y'): 10,
  (73, 'Z'): 10,
  (73, '_'): 10,
  (73, 'a'): 10,
  (73, 'b'): 10,
  (73, 'c'): 10,
  (73, 'd'): 10,
  (73, 'e'): 10,
  (73, 'f'): 10,
  (73, 'g'): 10,
  (73, 'h'): 10,
  (73, 'i'): 10,
  (73, 'j'): 10,
  (73, 'k'): 10,
  (73, 'l'): 10,
  (73, 'm'): 10,
  (73, 'n'): 10,
  (73, 'o'): 10,
  (73, 'p'): 10,
  (73, 'q'): 10,
  (73, 'r'): 10,
  (73, 's'): 10,
  (73, 't'): 74,
  (73, 'u'): 10,
  (73, 'v'): 10,
  (73, 'w'): 10,
  (73, 'x'): 10,
  (73, 'y'): 10,
  (73, 'z'): 10,
  (74, '0'): 10,
  (74, '1'): 10,
  (74, '2'): 10,
  (74, '3'): 10,
  (74, '4'): 10,
  (74, '5'): 10,
  (74, '6'): 10,
  (74, '7'): 10,
  (74, '8'): 10,
  (74, '9'): 10,
  (74, 'A'): 10,
  (74, 'B'): 10,
  (74, 'C'): 10,
  (74, 'D'): 10,
  (74, 'E'): 10,
  (74, 'F'): 10,
  (74, 'G'): 10,
  (74, 'H'): 10,
  (74, 'I'): 10,
  (74, 'J'): 10,
  (74, 'K'): 10,
  (74, 'L'): 10,
  (74, 'M'): 10,
  (74, 'N'): 10,
  (74, 'O'): 10,
  (74, 'P'): 10,
  (74, 'Q'): 10,
  (74, 'R'): 10,
  (74, 'S'): 10,
  (74, 'T'): 10,
  (74, 'U'): 10,
  (74, 'V'): 10,
  (74, 'W'): 10,
  (74, 'X'): 10,
  (74, 'Y'): 10,
  (74, 'Z'): 10,
  (74, '_'): 10,
  (74, 'a'): 10,
  (74, 'b'): 10,
  (74, 'c'): 10,
  (74, 'd'): 10,
  (74, 'e'): 75,
  (74, 'f'): 10,
  (74, 'g'): 10,
  (74, 'h'): 10,
  (74, 'i'): 10,
  (74, 'j'): 10,
  (74, 'k'): 10,
  (74, 'l'): 10,
  (74, 'm'): 10,
  (74, 'n'): 10,
  (74, 'o'): 10,
  (74, 'p'): 10,
  (74, 'q'): 10,
  (74, 'r'): 10,
  (74, 's'): 10,
  (74, 't'): 10,
  (74, 'u'): 10,
  (74, 'v'): 10,
  (74, 'w'): 10,
  (74, 'x'): 10,
  (74, 'y'): 10,
  (74, 'z'): 10,
  (75, '0'): 10,
  (75, '1'): 10,
  (75, '2'): 10,
  (75, '3'): 10,
  (75, '4'): 10,
  (75, '5'): 10,
  (75, '6'): 10,
  (75, '7'): 10,
  (75, '8'): 10,
  (75, '9'): 10,
  (75, 'A'): 10,
  (75, 'B'): 10,
  (75, 'C'): 10,
  (75, 'D'): 10,
  (75, 'E'): 10,
  (75, 'F'): 10,
  (75, 'G'): 10,
  (75, 'H'): 10,
  (75, 'I'): 10,
  (75, 'J'): 10,
  (75, 'K'): 10,
  (75, 'L'): 10,
  (75, 'M'): 10,
  (75, 'N'): 10,
  (75, 'O'): 10,
  (75, 'P'): 10,
  (75, 'Q'): 10,
  (75, 'R'): 10,
  (75, 'S'): 10,
  (75, 'T'): 10,
  (75, 'U'): 10,
  (75, 'V'): 10,
  (75, 'W'): 10,
  (75, 'X'): 10,
  (75, 'Y'): 10,
  (75, 'Z'): 10,
  (75, '_'): 10,
  (75, 'a'): 10,
  (75, 'b'): 10,
  (75, 'c'): 10,
  (75, 'd'): 10,
  (75, 'e'): 10,
  (75, 'f'): 10,
  (75, 'g'): 10,
  (75, 'h'): 10,
  (75, 'i'): 10,
  (75, 'j'): 10,
  (75, 'k'): 10,
  (75, 'l'): 10,
  (75, 'm'): 10,
  (75, 'n'): 10,
  (75, 'o'): 10,
  (75, 'p'): 10,
  (75, 'q'): 10,
  (75, 'r'): 10,
  (75, 's'): 76,
  (75, 't'): 10,
  (75, 'u'): 10,
  (75, 'v'): 10,
  (75, 'w'): 10,
  (75, 'x'): 10,
  (75, 'y'): 10,
  (75, 'z'): 10,
  (76, '0'): 10,
  (76, '1'): 10,
  (76, '2'): 10,
  (76, '3'): 10,
  (76, '4'): 10,
  (76, '5'): 10,
  (76, '6'): 10,
  (76, '7'): 10,
  (76, '8'): 10,
  (76, '9'): 10,
  (76, 'A'): 10,
  (76, 'B'): 10,
  (76, 'C'): 10,
  (76, 'D'): 10,
  (76, 'E'): 10,
  (76, 'F'): 10,
  (76, 'G'): 10,
  (76, 'H'): 10,
  (76, 'I'): 10,
  (76, 'J'): 10,
  (76, 'K'): 10,
  (76, 'L'): 10,
  (76, 'M'): 10,
  (76, 'N'): 10,
  (76, 'O'): 10,
  (76, 'P'): 10,
  (76, 'Q'): 10,
  (76, 'R'): 10,
  (76, 'S'): 10,
  (76, 'T'): 10,
  (76, 'U'): 10,
  (76, 'V'): 10,
  (76, 'W'): 10,
  (76, 'X'): 10,
  (76, 'Y'): 10,
  (76, 'Z'): 10,
  (76, '_'): 10,
  (76, 'a'): 10,
  (76, 'b'): 10,
  (76, 'c'): 10,
  (76, 'd'): 10,
  (76, 'e'): 10,
  (76, 'f'): 10,
  (76, 'g'): 10,
  (76, 'h'): 10,
  (76, 'i'): 10,
  (76, 'j'): 10,
  (76, 'k'): 10,
  (76, 'l'): 10,
  (76, 'm'): 10,
  (76, 'n'): 10,
  (76, 'o'): 10,
  (76, 'p'): 77,
  (76, 'q'): 10,
  (76, 'r'): 10,
  (76, 's'): 10,
  (76, 't'): 10,
  (76, 'u'): 10,
  (76, 'v'): 10,
  (76, 'w'): 10,
  (76, 'x'): 10,
  (76, 'y'): 10,
  (76, 'z'): 10,
  (77, '0'): 10,
  (77, '1'): 10,
  (77, '2'): 10,
  (77, '3'): 10,
  (77, '4'): 10,
  (77, '5'): 10,
  (77, '6'): 10,
  (77, '7'): 10,
  (77, '8'): 10,
  (77, '9'): 10,
  (77, 'A'): 10,
  (77, 'B'): 10,
  (77, 'C'): 10,
  (77, 'D'): 10,
  (77, 'E'): 10,
  (77, 'F'): 10,
  (77, 'G'): 10,
  (77, 'H'): 10,
  (77, 'I'): 10,
  (77, 'J'): 10,
  (77, 'K'): 10,
  (77, 'L'): 10,
  (77, 'M'): 10,
  (77, 'N'): 10,
  (77, 'O'): 10,
  (77, 'P'): 10,
  (77, 'Q'): 10,
  (77, 'R'): 10,
  (77, 'S'): 10,
  (77, 'T'): 10,
  (77, 'U'): 10,
  (77, 'V'): 10,
  (77, 'W'): 10,
  (77, 'X'): 10,
  (77, 'Y'): 10,
  (77, 'Z'): 10,
  (77, '_'): 10,
  (77, 'a'): 78,
  (77, 'b'): 10,
  (77, 'c'): 10,
  (77, 'd'): 10,
  (77, 'e'): 10,
  (77, 'f'): 10,
  (77, 'g'): 10,
  (77, 'h'): 10,
  (77, 'i'): 10,
  (77, 'j'): 10,
  (77, 'k'): 10,
  (77, 'l'): 10,
  (77, 'm'): 10,
  (77, 'n'): 10,
  (77, 'o'): 10,
  (77, 'p'): 10,
  (77, 'q'): 10,
  (77, 'r'): 10,
  (77, 's'): 10,
  (77, 't'): 10,
  (77, 'u'): 10,
  (77, 'v'): 10,
  (77, 'w'): 10,
  (77, 'x'): 10,
  (77, 'y'): 10,
  (77, 'z'): 10,
  (78, '0'): 10,
  (78, '1'): 10,
  (78, '2'): 10,
  (78, '3'): 10,
  (78, '4'): 10,
  (78, '5'): 10,
  (78, '6'): 10,
  (78, '7'): 10,
  (78, '8'): 10,
  (78, '9'): 10,
  (78, 'A'): 10,
  (78, 'B'): 10,
  (78, 'C'): 10,
  (78, 'D'): 10,
  (78, 'E'): 10,
  (78, 'F'): 10,
  (78, 'G'): 10,
  (78, 'H'): 10,
  (78, 'I'): 10,
  (78, 'J'): 10,
  (78, 'K'): 10,
  (78, 'L'): 10,
  (78, 'M'): 10,
  (78, 'N'): 10,
  (78, 'O'): 10,
  (78, 'P'): 10,
  (78, 'Q'): 10,
  (78, 'R'): 10,
  (78, 'S'): 10,
  (78, 'T'): 10,
  (78, 'U'): 10,
  (78, 'V'): 10,
  (78, 'W'): 10,
  (78, 'X'): 10,
  (78, 'Y'): 10,
  (78, 'Z'): 10,
  (78, '_'): 10,
  (78, 'a'): 10,
  (78, 'b'): 10,
  (78, 'c'): 79,
  (78, 'd'): 10,
  (78, 'e'): 10,
  (78, 'f'): 10,
  (78, 'g'): 10,
  (78, 'h'): 10,
  (78, 'i'): 10,
  (78, 'j'): 10,
  (78, 'k'): 10,
  (78, 'l'): 10,
  (78, 'm'): 10,
  (78, 'n'): 10,
  (78, 'o'): 10,
  (78, 'p'): 10,
  (78, 'q'): 10,
  (78, 'r'): 10,
  (78, 's'): 10,
  (78, 't'): 10,
  (78, 'u'): 10,
  (78, 'v'): 10,
  (78, 'w'): 10,
  (78, 'x'): 10,
  (78, 'y'): 10,
  (78, 'z'): 10,
  (79, '0'): 10,
  (79, '1'): 10,
  (79, '2'): 10,
  (79, '3'): 10,
  (79, '4'): 10,
  (79, '5'): 10,
  (79, '6'): 10,
  (79, '7'): 10,
  (79, '8'): 10,
  (79, '9'): 10,
  (79, 'A'): 10,
  (79, 'B'): 10,
  (79, 'C'): 10,
  (79, 'D'): 10,
  (79, 'E'): 10,
  (79, 'F'): 10,
  (79, 'G'): 10,
  (79, 'H'): 10,
  (79, 'I'): 10,
  (79, 'J'): 10,
  (79, 'K'): 10,
  (79, 'L'): 10,
  (79, 'M'): 10,
  (79, 'N'): 10,
  (79, 'O'): 10,
  (79, 'P'): 10,
  (79, 'Q'): 10,
  (79, 'R'): 10,
  (79, 'S'): 10,
  (79, 'T'): 10,
  (79, 'U'): 10,
  (79, 'V'): 10,
  (79, 'W'): 10,
  (79, 'X'): 10,
  (79, 'Y'): 10,
  (79, 'Z'): 10,
  (79, '_'): 10,
  (79, 'a'): 10,
  (79, 'b'): 10,
  (79, 'c'): 10,
  (79, 'd'): 10,
  (79, 'e'): 80,
  (79, 'f'): 10,
  (79, 'g'): 10,
  (79, 'h'): 10,
  (79, 'i'): 10,
  (79, 'j'): 10,
  (79, 'k'): 10,
  (79, 'l'): 10,
  (79, 'm'): 10,
  (79, 'n'): 10,
  (79, 'o'): 10,
  (79, 'p'): 10,
  (79, 'q'): 10,
  (79, 'r'): 10,
  (79, 's'): 10,
  (79, 't'): 10,
  (79, 'u'): 10,
  (79, 'v'): 10,
  (79, 'w'): 10,
  (79, 'x'): 10,
  (79, 'y'): 10,
  (79, 'z'): 10,
  (80, '0'): 10,
  (80, '1'): 10,
  (80, '2'): 10,
  (80, '3'): 10,
  (80, '4'): 10,
  (80, '5'): 10,
  (80, '6'): 10,
  (80, '7'): 10,
  (80, '8'): 10,
  (80, '9'): 10,
  (80, 'A'): 10,
  (80, 'B'): 10,
  (80, 'C'): 10,
  (80, 'D'): 10,
  (80, 'E'): 10,
  (80, 'F'): 10,
  (80, 'G'): 10,
  (80, 'H'): 10,
  (80, 'I'): 10,
  (80, 'J'): 10,
  (80, 'K'): 10,
  (80, 'L'): 10,
  (80, 'M'): 10,
  (80, 'N'): 10,
  (80, 'O'): 10,
  (80, 'P'): 10,
  (80, 'Q'): 10,
  (80, 'R'): 10,
  (80, 'S'): 10,
  (80, 'T'): 10,
  (80, 'U'): 10,
  (80, 'V'): 10,
  (80, 'W'): 10,
  (80, 'X'): 10,
  (80, 'Y'): 10,
  (80, 'Z'): 10,
  (80, '_'): 10,
  (80, 'a'): 10,
  (80, 'b'): 10,
  (80, 'c'): 10,
  (80, 'd'): 10,
  (80, 'e'): 10,
  (80, 'f'): 10,
  (80, 'g'): 10,
  (80, 'h'): 10,
  (80, 'i'): 10,
  (80, 'j'): 10,
  (80, 'k'): 10,
  (80, 'l'): 10,
  (80, 'm'): 10,
  (80, 'n'): 10,
  (80, 'o'): 10,
  (80, 'p'): 10,
  (80, 'q'): 10,
  (80, 'r'): 10,
  (80, 's'): 10,
  (80, 't'): 10,
  (80, 'u'): 10,
  (80, 'v'): 10,
  (80, 'w'): 10,
  (80, 'x'): 10,
  (80, 'y'): 10,
  (80, 'z'): 10,
  (82, '\x00'): 82,
  (82, '\x01'): 82,
  (82, '\x02'): 82,
  (82, '\x03'): 82,
  (82, '\x04'): 82,
  (82, '\x05'): 82,
  (82, '\x06'): 82,
  (82, '\x07'): 82,
  (82, '\x08'): 82,
  (82, '\t'): 82,
  (82, '\n'): 82,
  (82, '\x0b'): 82,
  (82, '\x0c'): 82,
  (82, '\r'): 82,
  (82, '\x0e'): 82,
  (82, '\x0f'): 82,
  (82, '\x10'): 82,
  (82, '\x11'): 82,
  (82, '\x12'): 82,
  (82, '\x13'): 82,
  (82, '\x14'): 82,
  (82, '\x15'): 82,
  (82, '\x16'): 82,
  (82, '\x17'): 82,
  (82, '\x18'): 82,
  (82, '\x19'): 82,
  (82, '\x1a'): 82,
  (82, '\x1b'): 82,
  (82, '\x1c'): 82,
  (82, '\x1d'): 82,
  (82, '\x1e'): 82,
  (82, '\x1f'): 82,
  (82, ' '): 82,
  (82, '!'): 82,
  (82, '"'): 82,
  (82, '#'): 82,
  (82, '$'): 82,
  (82, '%'): 82,
  (82, '&'): 82,
  (82, "'"): 82,
  (82, '('): 82,
  (82, ')'): 82,
  (82, '*'): 84,
  (82, '+'): 82,
  (82, ','): 82,
  (82, '-'): 82,
  (82, '.'): 82,
  (82, '/'): 82,
  (82, '0'): 82,
  (82, '1'): 82,
  (82, '2'): 82,
  (82, '3'): 82,
  (82, '4'): 82,
  (82, '5'): 82,
  (82, '6'): 82,
  (82, '7'): 82,
  (82, '8'): 82,
  (82, '9'): 82,
  (82, ':'): 82,
  (82, ';'): 82,
  (82, '<'): 82,
  (82, '='): 82,
  (82, '>'): 82,
  (82, '?'): 82,
  (82, '@'): 82,
  (82, 'A'): 82,
  (82, 'B'): 82,
  (82, 'C'): 82,
  (82, 'D'): 82,
  (82, 'E'): 82,
  (82, 'F'): 82,
  (82, 'G'): 82,
  (82, 'H'): 82,
  (82, 'I'): 82,
  (82, 'J'): 82,
  (82, 'K'): 82,
  (82, 'L'): 82,
  (82, 'M'): 82,
  (82, 'N'): 82,
  (82, 'O'): 82,
  (82, 'P'): 82,
  (82, 'Q'): 82,
  (82, 'R'): 82,
  (82, 'S'): 82,
  (82, 'T'): 82,
  (82, 'U'): 82,
  (82, 'V'): 82,
  (82, 'W'): 82,
  (82, 'X'): 82,
  (82, 'Y'): 82,
  (82, 'Z'): 82,
  (82, '['): 82,
  (82, '\\'): 82,
  (82, ']'): 82,
  (82, '^'): 82,
  (82, '_'): 82,
  (82, '`'): 82,
  (82, 'a'): 82,
  (82, 'b'): 82,
  (82, 'c'): 82,
  (82, 'd'): 82,
  (82, 'e'): 82,
  (82, 'f'): 82,
  (82, 'g'): 82,
  (82, 'h'): 82,
  (82, 'i'): 82,
  (82, 'j'): 82,
  (82, 'k'): 82,
  (82, 'l'): 82,
  (82, 'm'): 82,
  (82, 'n'): 82,
  (82, 'o'): 82,
  (82, 'p'): 82,
  (82, 'q'): 82,
  (82, 'r'): 82,
  (82, 's'): 82,
  (82, 't'): 82,
  (82, 'u'): 82,
  (82, 'v'): 82,
  (82, 'w'): 82,
  (82, 'x'): 82,
  (82, 'y'): 82,
  (82, 'z'): 82,
  (82, '{'): 82,
  (82, '|'): 82,
  (82, '}'): 82,
  (82, '~'): 82,
  (82, '\x7f'): 82,
  (82, '\x80'): 82,
  (82, '\x81'): 82,
  (82, '\x82'): 82,
  (82, '\x83'): 82,
  (82, '\x84'): 82,
  (82, '\x85'): 82,
  (82, '\x86'): 82,
  (82, '\x87'): 82,
  (82, '\x88'): 82,
  (82, '\x89'): 82,
  (82, '\x8a'): 82,
  (82, '\x8b'): 82,
  (82, '\x8c'): 82,
  (82, '\x8d'): 82,
  (82, '\x8e'): 82,
  (82, '\x8f'): 82,
  (82, '\x90'): 82,
  (82, '\x91'): 82,
  (82, '\x92'): 82,
  (82, '\x93'): 82,
  (82, '\x94'): 82,
  (82, '\x95'): 82,
  (82, '\x96'): 82,
  (82, '\x97'): 82,
  (82, '\x98'): 82,
  (82, '\x99'): 82,
  (82, '\x9a'): 82,
  (82, '\x9b'): 82,
  (82, '\x9c'): 82,
  (82, '\x9d'): 82,
  (82, '\x9e'): 82,
  (82, '\x9f'): 82,
  (82, '\xa0'): 82,
  (82, '\xa1'): 82,
  (82, '\xa2'): 82,
  (82, '\xa3'): 82,
  (82, '\xa4'): 82,
  (82, '\xa5'): 82,
  (82, '\xa6'): 82,
  (82, '\xa7'): 82,
  (82, '\xa8'): 82,
  (82, '\xa9'): 82,
  (82, '\xaa'): 82,
  (82, '\xab'): 82,
  (82, '\xac'): 82,
  (82, '\xad'): 82,
  (82, '\xae'): 82,
  (82, '\xaf'): 82,
  (82, '\xb0'): 82,
  (82, '\xb1'): 82,
  (82, '\xb2'): 82,
  (82, '\xb3'): 82,
  (82, '\xb4'): 82,
  (82, '\xb5'): 82,
  (82, '\xb6'): 82,
  (82, '\xb7'): 82,
  (82, '\xb8'): 82,
  (82, '\xb9'): 82,
  (82, '\xba'): 82,
  (82, '\xbb'): 82,
  (82, '\xbc'): 82,
  (82, '\xbd'): 82,
  (82, '\xbe'): 82,
  (82, '\xbf'): 82,
  (82, '\xc0'): 82,
  (82, '\xc1'): 82,
  (82, '\xc2'): 82,
  (82, '\xc3'): 82,
  (82, '\xc4'): 82,
  (82, '\xc5'): 82,
  (82, '\xc6'): 82,
  (82, '\xc7'): 82,
  (82, '\xc8'): 82,
  (82, '\xc9'): 82,
  (82, '\xca'): 82,
  (82, '\xcb'): 82,
  (82, '\xcc'): 82,
  (82, '\xcd'): 82,
  (82, '\xce'): 82,
  (82, '\xcf'): 82,
  (82, '\xd0'): 82,
  (82, '\xd1'): 82,
  (82, '\xd2'): 82,
  (82, '\xd3'): 82,
  (82, '\xd4'): 82,
  (82, '\xd5'): 82,
  (82, '\xd6'): 82,
  (82, '\xd7'): 82,
  (82, '\xd8'): 82,
  (82, '\xd9'): 82,
  (82, '\xda'): 82,
  (82, '\xdb'): 82,
  (82, '\xdc'): 82,
  (82, '\xdd'): 82,
  (82, '\xde'): 82,
  (82, '\xdf'): 82,
  (82, '\xe0'): 82,
  (82, '\xe1'): 82,
  (82, '\xe2'): 82,
  (82, '\xe3'): 82,
  (82, '\xe4'): 82,
  (82, '\xe5'): 82,
  (82, '\xe6'): 82,
  (82, '\xe7'): 82,
  (82, '\xe8'): 82,
  (82, '\xe9'): 82,
  (82, '\xea'): 82,
  (82, '\xeb'): 82,
  (82, '\xec'): 82,
  (82, '\xed'): 82,
  (82, '\xee'): 82,
  (82, '\xef'): 82,
  (82, '\xf0'): 82,
  (82, '\xf1'): 82,
  (82, '\xf2'): 82,
  (82, '\xf3'): 82,
  (82, '\xf4'): 82,
  (82, '\xf5'): 82,
  (82, '\xf6'): 82,
  (82, '\xf7'): 82,
  (82, '\xf8'): 82,
  (82, '\xf9'): 82,
  (82, '\xfa'): 82,
  (82, '\xfb'): 82,
  (82, '\xfc'): 82,
  (82, '\xfd'): 82,
  (82, '\xfe'): 82,
  (82, '\xff'): 82,
  (84, '\x00'): 82,
  (84, '\x01'): 82,
  (84, '\x02'): 82,
  (84, '\x03'): 82,
  (84, '\x04'): 82,
  (84, '\x05'): 82,
  (84, '\x06'): 82,
  (84, '\x07'): 82,
  (84, '\x08'): 82,
  (84, '\t'): 82,
  (84, '\n'): 82,
  (84, '\x0b'): 82,
  (84, '\x0c'): 82,
  (84, '\r'): 82,
  (84, '\x0e'): 82,
  (84, '\x0f'): 82,
  (84, '\x10'): 82,
  (84, '\x11'): 82,
  (84, '\x12'): 82,
  (84, '\x13'): 82,
  (84, '\x14'): 82,
  (84, '\x15'): 82,
  (84, '\x16'): 82,
  (84, '\x17'): 82,
  (84, '\x18'): 82,
  (84, '\x19'): 82,
  (84, '\x1a'): 82,
  (84, '\x1b'): 82,
  (84, '\x1c'): 82,
  (84, '\x1d'): 82,
  (84, '\x1e'): 82,
  (84, '\x1f'): 82,
  (84, ' '): 82,
  (84, '!'): 82,
  (84, '"'): 82,
  (84, '#'): 82,
  (84, '$'): 82,
  (84, '%'): 82,
  (84, '&'): 82,
  (84, "'"): 82,
  (84, '('): 82,
  (84, ')'): 82,
  (84, '*'): 84,
  (84, '+'): 82,
  (84, ','): 82,
  (84, '-'): 82,
  (84, '.'): 82,
  (84, '/'): 85,
  (84, '0'): 82,
  (84, '1'): 82,
  (84, '2'): 82,
  (84, '3'): 82,
  (84, '4'): 82,
  (84, '5'): 82,
  (84, '6'): 82,
  (84, '7'): 82,
  (84, '8'): 82,
  (84, '9'): 82,
  (84, ':'): 82,
  (84, ';'): 82,
  (84, '<'): 82,
  (84, '='): 82,
  (84, '>'): 82,
  (84, '?'): 82,
  (84, '@'): 82,
  (84, 'A'): 82,
  (84, 'B'): 82,
  (84, 'C'): 82,
  (84, 'D'): 82,
  (84, 'E'): 82,
  (84, 'F'): 82,
  (84, 'G'): 82,
  (84, 'H'): 82,
  (84, 'I'): 82,
  (84, 'J'): 82,
  (84, 'K'): 82,
  (84, 'L'): 82,
  (84, 'M'): 82,
  (84, 'N'): 82,
  (84, 'O'): 82,
  (84, 'P'): 82,
  (84, 'Q'): 82,
  (84, 'R'): 82,
  (84, 'S'): 82,
  (84, 'T'): 82,
  (84, 'U'): 82,
  (84, 'V'): 82,
  (84, 'W'): 82,
  (84, 'X'): 82,
  (84, 'Y'): 82,
  (84, 'Z'): 82,
  (84, '['): 82,
  (84, '\\'): 82,
  (84, ']'): 82,
  (84, '^'): 82,
  (84, '_'): 82,
  (84, '`'): 82,
  (84, 'a'): 82,
  (84, 'b'): 82,
  (84, 'c'): 82,
  (84, 'd'): 82,
  (84, 'e'): 82,
  (84, 'f'): 82,
  (84, 'g'): 82,
  (84, 'h'): 82,
  (84, 'i'): 82,
  (84, 'j'): 82,
  (84, 'k'): 82,
  (84, 'l'): 82,
  (84, 'm'): 82,
  (84, 'n'): 82,
  (84, 'o'): 82,
  (84, 'p'): 82,
  (84, 'q'): 82,
  (84, 'r'): 82,
  (84, 's'): 82,
  (84, 't'): 82,
  (84, 'u'): 82,
  (84, 'v'): 82,
  (84, 'w'): 82,
  (84, 'x'): 82,
  (84, 'y'): 82,
  (84, 'z'): 82,
  (84, '{'): 82,
  (84, '|'): 82,
  (84, '}'): 82,
  (84, '~'): 82,
  (84, '\x7f'): 82,
  (84, '\x80'): 82,
  (84, '\x81'): 82,
  (84, '\x82'): 82,
  (84, '\x83'): 82,
  (84, '\x84'): 82,
  (84, '\x85'): 82,
  (84, '\x86'): 82,
  (84, '\x87'): 82,
  (84, '\x88'): 82,
  (84, '\x89'): 82,
  (84, '\x8a'): 82,
  (84, '\x8b'): 82,
  (84, '\x8c'): 82,
  (84, '\x8d'): 82,
  (84, '\x8e'): 82,
  (84, '\x8f'): 82,
  (84, '\x90'): 82,
  (84, '\x91'): 82,
  (84, '\x92'): 82,
  (84, '\x93'): 82,
  (84, '\x94'): 82,
  (84, '\x95'): 82,
  (84, '\x96'): 82,
  (84, '\x97'): 82,
  (84, '\x98'): 82,
  (84, '\x99'): 82,
  (84, '\x9a'): 82,
  (84, '\x9b'): 82,
  (84, '\x9c'): 82,
  (84, '\x9d'): 82,
  (84, '\x9e'): 82,
  (84, '\x9f'): 82,
  (84, '\xa0'): 82,
  (84, '\xa1'): 82,
  (84, '\xa2'): 82,
  (84, '\xa3'): 82,
  (84, '\xa4'): 82,
  (84, '\xa5'): 82,
  (84, '\xa6'): 82,
  (84, '\xa7'): 82,
  (84, '\xa8'): 82,
  (84, '\xa9'): 82,
  (84, '\xaa'): 82,
  (84, '\xab'): 82,
  (84, '\xac'): 82,
  (84, '\xad'): 82,
  (84, '\xae'): 82,
  (84, '\xaf'): 82,
  (84, '\xb0'): 82,
  (84, '\xb1'): 82,
  (84, '\xb2'): 82,
  (84, '\xb3'): 82,
  (84, '\xb4'): 82,
  (84, '\xb5'): 82,
  (84, '\xb6'): 82,
  (84, '\xb7'): 82,
  (84, '\xb8'): 82,
  (84, '\xb9'): 82,
  (84, '\xba'): 82,
  (84, '\xbb'): 82,
  (84, '\xbc'): 82,
  (84, '\xbd'): 82,
  (84, '\xbe'): 82,
  (84, '\xbf'): 82,
  (84, '\xc0'): 82,
  (84, '\xc1'): 82,
  (84, '\xc2'): 82,
  (84, '\xc3'): 82,
  (84, '\xc4'): 82,
  (84, '\xc5'): 82,
  (84, '\xc6'): 82,
  (84, '\xc7'): 82,
  (84, '\xc8'): 82,
  (84, '\xc9'): 82,
  (84, '\xca'): 82,
  (84, '\xcb'): 82,
  (84, '\xcc'): 82,
  (84, '\xcd'): 82,
  (84, '\xce'): 82,
  (84, '\xcf'): 82,
  (84, '\xd0'): 82,
  (84, '\xd1'): 82,
  (84, '\xd2'): 82,
  (84, '\xd3'): 82,
  (84, '\xd4'): 82,
  (84, '\xd5'): 82,
  (84, '\xd6'): 82,
  (84, '\xd7'): 82,
  (84, '\xd8'): 82,
  (84, '\xd9'): 82,
  (84, '\xda'): 82,
  (84, '\xdb'): 82,
  (84, '\xdc'): 82,
  (84, '\xdd'): 82,
  (84, '\xde'): 82,
  (84, '\xdf'): 82,
  (84, '\xe0'): 82,
  (84, '\xe1'): 82,
  (84, '\xe2'): 82,
  (84, '\xe3'): 82,
  (84, '\xe4'): 82,
  (84, '\xe5'): 82,
  (84, '\xe6'): 82,
  (84, '\xe7'): 82,
  (84, '\xe8'): 82,
  (84, '\xe9'): 82,
  (84, '\xea'): 82,
  (84, '\xeb'): 82,
  (84, '\xec'): 82,
  (84, '\xed'): 82,
  (84, '\xee'): 82,
  (84, '\xef'): 82,
  (84, '\xf0'): 82,
  (84, '\xf1'): 82,
  (84, '\xf2'): 82,
  (84, '\xf3'): 82,
  (84, '\xf4'): 82,
  (84, '\xf5'): 82,
  (84, '\xf6'): 82,
  (84, '\xf7'): 82,
  (84, '\xf8'): 82,
  (84, '\xf9'): 82,
  (84, '\xfa'): 82,
  (84, '\xfb'): 82,
  (84, '\xfc'): 82,
  (84, '\xfd'): 82,
  (84, '\xfe'): 82,
  (84, '\xff'): 82,
  (88, '\x00'): 15,
  (88, '\x01'): 15,
  (88, '\x02'): 15,
  (88, '\x03'): 15,
  (88, '\x04'): 15,
  (88, '\x05'): 15,
  (88, '\x06'): 15,
  (88, '\x07'): 15,
  (88, '\x08'): 15,
  (88, '\t'): 15,
  (88, '\n'): 15,
  (88, '\x0b'): 15,
  (88, '\x0c'): 15,
  (88, '\r'): 15,
  (88, '\x0e'): 15,
  (88, '\x0f'): 15,
  (88, '\x10'): 15,
  (88, '\x11'): 15,
  (88, '\x12'): 15,
  (88, '\x13'): 15,
  (88, '\x14'): 15,
  (88, '\x15'): 15,
  (88, '\x16'): 15,
  (88, '\x17'): 15,
  (88, '\x18'): 15,
  (88, '\x19'): 15,
  (88, '\x1a'): 15,
  (88, '\x1b'): 15,
  (88, '\x1c'): 15,
  (88, '\x1d'): 15,
  (88, '\x1e'): 15,
  (88, '\x1f'): 15,
  (88, ' '): 15,
  (88, '!'): 15,
  (88, '"'): 15,
  (88, '#'): 15,
  (88, '$'): 15,
  (88, '%'): 15,
  (88, '&'): 15,
  (88, "'"): 15,
  (88, '('): 15,
  (88, ')'): 15,
  (88, '*'): 15,
  (88, '+'): 15,
  (88, ','): 15,
  (88, '-'): 15,
  (88, '.'): 15,
  (88, '/'): 15,
  (88, '0'): 15,
  (88, '1'): 15,
  (88, '2'): 15,
  (88, '3'): 15,
  (88, '4'): 15,
  (88, '5'): 15,
  (88, '6'): 15,
  (88, '7'): 15,
  (88, '8'): 15,
  (88, '9'): 15,
  (88, ':'): 15,
  (88, ';'): 15,
  (88, '<'): 15,
  (88, '='): 15,
  (88, '>'): 15,
  (88, '?'): 15,
  (88, '@'): 15,
  (88, 'A'): 15,
  (88, 'B'): 15,
  (88, 'C'): 15,
  (88, 'D'): 15,
  (88, 'E'): 15,
  (88, 'F'): 15,
  (88, 'G'): 15,
  (88, 'H'): 15,
  (88, 'I'): 15,
  (88, 'J'): 15,
  (88, 'K'): 15,
  (88, 'L'): 15,
  (88, 'M'): 15,
  (88, 'N'): 15,
  (88, 'O'): 15,
  (88, 'P'): 15,
  (88, 'Q'): 15,
  (88, 'R'): 15,
  (88, 'S'): 15,
  (88, 'T'): 15,
  (88, 'U'): 15,
  (88, 'V'): 15,
  (88, 'W'): 15,
  (88, 'X'): 15,
  (88, 'Y'): 15,
  (88, 'Z'): 15,
  (88, '['): 15,
  (88, '\\'): 15,
  (88, ']'): 15,
  (88, '^'): 15,
  (88, '_'): 15,
  (88, '`'): 15,
  (88, 'a'): 15,
  (88, 'b'): 15,
  (88, 'c'): 15,
  (88, 'd'): 15,
  (88, 'e'): 15,
  (88, 'f'): 15,
  (88, 'g'): 15,
  (88, 'h'): 15,
  (88, 'i'): 15,
  (88, 'j'): 15,
  (88, 'k'): 15,
  (88, 'l'): 15,
  (88, 'm'): 15,
  (88, 'n'): 15,
  (88, 'o'): 15,
  (88, 'p'): 15,
  (88, 'q'): 15,
  (88, 'r'): 15,
  (88, 's'): 15,
  (88, 't'): 15,
  (88, 'u'): 15,
  (88, 'v'): 15,
  (88, 'w'): 15,
  (88, 'x'): 15,
  (88, 'y'): 15,
  (88, 'z'): 15,
  (88, '{'): 15,
  (88, '|'): 15,
  (88, '}'): 15,
  (88, '~'): 15,
  (88, '\x7f'): 15,
  (88, '\x80'): 15,
  (88, '\x81'): 15,
  (88, '\x82'): 15,
  (88, '\x83'): 15,
  (88, '\x84'): 15,
  (88, '\x85'): 15,
  (88, '\x86'): 15,
  (88, '\x87'): 15,
  (88, '\x88'): 15,
  (88, '\x89'): 15,
  (88, '\x8a'): 15,
  (88, '\x8b'): 15,
  (88, '\x8c'): 15,
  (88, '\x8d'): 15,
  (88, '\x8e'): 15,
  (88, '\x8f'): 15,
  (88, '\x90'): 15,
  (88, '\x91'): 15,
  (88, '\x92'): 15,
  (88, '\x93'): 15,
  (88, '\x94'): 15,
  (88, '\x95'): 15,
  (88, '\x96'): 15,
  (88, '\x97'): 15,
  (88, '\x98'): 15,
  (88, '\x99'): 15,
  (88, '\x9a'): 15,
  (88, '\x9b'): 15,
  (88, '\x9c'): 15,
  (88, '\x9d'): 15,
  (88, '\x9e'): 15,
  (88, '\x9f'): 15,
  (88, '\xa0'): 15,
  (88, '\xa1'): 15,
  (88, '\xa2'): 15,
  (88, '\xa3'): 15,
  (88, '\xa4'): 15,
  (88, '\xa5'): 15,
  (88, '\xa6'): 15,
  (88, '\xa7'): 15,
  (88, '\xa8'): 15,
  (88, '\xa9'): 15,
  (88, '\xaa'): 15,
  (88, '\xab'): 15,
  (88, '\xac'): 15,
  (88, '\xad'): 15,
  (88, '\xae'): 15,
  (88, '\xaf'): 15,
  (88, '\xb0'): 15,
  (88, '\xb1'): 15,
  (88, '\xb2'): 15,
  (88, '\xb3'): 15,
  (88, '\xb4'): 15,
  (88, '\xb5'): 15,
  (88, '\xb6'): 15,
  (88, '\xb7'): 15,
  (88, '\xb8'): 15,
  (88, '\xb9'): 15,
  (88, '\xba'): 15,
  (88, '\xbb'): 15,
  (88, '\xbc'): 15,
  (88, '\xbd'): 15,
  (88, '\xbe'): 15,
  (88, '\xbf'): 15,
  (88, '\xc0'): 15,
  (88, '\xc1'): 15,
  (88, '\xc2'): 15,
  (88, '\xc3'): 15,
  (88, '\xc4'): 15,
  (88, '\xc5'): 15,
  (88, '\xc6'): 15,
  (88, '\xc7'): 15,
  (88, '\xc8'): 15,
  (88, '\xc9'): 15,
  (88, '\xca'): 15,
  (88, '\xcb'): 15,
  (88, '\xcc'): 15,
  (88, '\xcd'): 15,
  (88, '\xce'): 15,
  (88, '\xcf'): 15,
  (88, '\xd0'): 15,
  (88, '\xd1'): 15,
  (88, '\xd2'): 15,
  (88, '\xd3'): 15,
  (88, '\xd4'): 15,
  (88, '\xd5'): 15,
  (88, '\xd6'): 15,
  (88, '\xd7'): 15,
  (88, '\xd8'): 15,
  (88, '\xd9'): 15,
  (88, '\xda'): 15,
  (88, '\xdb'): 15,
  (88, '\xdc'): 15,
  (88, '\xdd'): 15,
  (88, '\xde'): 15,
  (88, '\xdf'): 15,
  (88, '\xe0'): 15,
  (88, '\xe1'): 15,
  (88, '\xe2'): 15,
  (88, '\xe3'): 15,
  (88, '\xe4'): 15,
  (88, '\xe5'): 15,
  (88, '\xe6'): 15,
  (88, '\xe7'): 15,
  (88, '\xe8'): 15,
  (88, '\xe9'): 15,
  (88, '\xea'): 15,
  (88, '\xeb'): 15,
  (88, '\xec'): 15,
  (88, '\xed'): 15,
  (88, '\xee'): 15,
  (88, '\xef'): 15,
  (88, '\xf0'): 15,
  (88, '\xf1'): 15,
  (88, '\xf2'): 15,
  (88, '\xf3'): 15,
  (88, '\xf4'): 15,
  (88, '\xf5'): 15,
  (88, '\xf6'): 15,
  (88, '\xf7'): 15,
  (88, '\xf8'): 15,
  (88, '\xf9'): 15,
  (88, '\xfa'): 15,
  (88, '\xfb'): 15,
  (88, '\xfc'): 15,
  (88, '\xfd'): 15,
  (88, '\xfe'): 15,
  (88, '\xff'): 15,
  (92, '<'): 55,
  (92, '='): 94,
  (95, '0'): 95,
  (95, '1'): 95,
  (95, '2'): 95,
  (95, '3'): 95,
  (95, '4'): 95,
  (95, '5'): 95,
  (95, '6'): 95,
  (95, '7'): 95,
  (95, '8'): 95,
  (95, '9'): 95,
  (95, 'A'): 95,
  (95, 'B'): 95,
  (95, 'C'): 95,
  (95, 'D'): 95,
  (95, 'E'): 95,
  (95, 'F'): 95,
  (95, 'a'): 95,
  (95, 'b'): 95,
  (95, 'c'): 95,
  (95, 'd'): 95,
  (95, 'e'): 95,
  (95, 'f'): 95,
  (96, 'r'): 157,
  (97, 'i'): 146,
  (97, 'o'): 147,
  (98, 'o'): 142,
  (99, 'l'): 139,
  (100, 'n'): 132,
  (101, 'b'): 126,
  (102, 't'): 120,
  (103, 'e'): 116,
  (104, 'n'): 105,
  (105, 'i'): 106,
  (105, 's'): 107,
  (106, 'c'): 111,
  (107, 'e'): 108,
  (108, 't'): 109,
  (109, ')'): 110,
  (111, 'o'): 112,
  (112, 'd'): 113,
  (113, 'e'): 114,
  (114, ')'): 115,
  (116, 'a'): 117,
  (117, 'l'): 118,
  (118, ')'): 119,
  (120, 'r'): 121,
  (121, 'i'): 122,
  (122, 'n'): 123,
  (123, 'g'): 124,
  (124, ')'): 125,
  (126, 'j'): 127,
  (127, 'e'): 128,
  (128, 'c'): 129,
  (129, 't'): 130,
  (130, ')'): 131,
  (132, 't'): 133,
  (133, ')'): 134,
  (133, 'e'): 135,
  (135, 'g'): 136,
  (136, 'e'): 137,
  (137, 'r'): 138,
  (138, ')'): 134,
  (139, 'o'): 140,
  (140, 'a'): 141,
  (141, 't'): 118,
  (142, 'u'): 143,
  (143, 'b'): 144,
  (144, 'l'): 145,
  (145, 'e'): 118,
  (146, 'n'): 154,
  (147, 'o'): 148,
  (148, 'l'): 149,
  (149, ')'): 150,
  (149, 'e'): 151,
  (151, 'a'): 152,
  (152, 'n'): 153,
  (153, ')'): 150,
  (154, 'a'): 155,
  (155, 'r'): 156,
  (156, 'y'): 124,
  (157, 'r'): 158,
  (158, 'a'): 159,
  (159, 'y'): 160,
  (160, ')'): 161,
  (162, '0'): 162,
  (162, '1'): 162,
  (162, '2'): 162,
  (162, '3'): 162,
  (162, '4'): 162,
  (162, '5'): 162,
  (162, '6'): 162,
  (162, '7'): 162,
  (162, '8'): 162,
  (162, '9'): 162,
  (162, 'A'): 162,
  (162, 'B'): 162,
  (162, 'C'): 162,
  (162, 'D'): 162,
  (162, 'E'): 162,
  (162, 'F'): 162,
  (162, 'G'): 162,
  (162, 'H'): 162,
  (162, 'I'): 162,
  (162, 'J'): 162,
  (162, 'K'): 162,
  (162, 'L'): 162,
  (162, 'M'): 162,
  (162, 'N'): 162,
  (162, 'O'): 162,
  (162, 'P'): 162,
  (162, 'Q'): 162,
  (162, 'R'): 162,
  (162, 'S'): 162,
  (162, 'T'): 162,
  (162, 'U'): 162,
  (162, 'V'): 162,
  (162, 'W'): 162,
  (162, 'X'): 162,
  (162, 'Y'): 162,
  (162, 'Z'): 162,
  (162, '_'): 162,
  (162, 'a'): 162,
  (162, 'b'): 162,
  (162, 'c'): 162,
  (162, 'd'): 162,
  (162, 'e'): 162,
  (162, 'f'): 162,
  (162, 'g'): 162,
  (162, 'h'): 162,
  (162, 'i'): 162,
  (162, 'j'): 162,
  (162, 'k'): 162,
  (162, 'l'): 162,
  (162, 'm'): 162,
  (162, 'n'): 162,
  (162, 'o'): 162,
  (162, 'p'): 162,
  (162, 'q'): 162,
  (162, 'r'): 162,
  (162, 's'): 162,
  (162, 't'): 162,
  (162, 'u'): 162,
  (162, 'v'): 162,
  (162, 'w'): 162,
  (162, 'x'): 162,
  (162, 'y'): 162,
  (162, 'z'): 162},
 set([1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      35,
      36,
      37,
      38,
      39,
      40,
      41,
      42,
      43,
      44,
      45,
      46,
      47,
      48,
      49,
      50,
      51,
      56,
      58,
      59,
      60,
      61,
      62,
      63,
      65,
      66,
      68,
      69,
      70,
      71,
      72,
      73,
      74,
      75,
      76,
      77,
      78,
      79,
      80,
      81,
      83,
      85,
      86,
      87,
      89,
      90,
      91,
      92,
      93,
      94,
      95,
      110,
      115,
      119,
      125,
      131,
      134,
      150,
      161,
      162]),
 set([1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      35,
      36,
      37,
      38,
      39,
      40,
      41,
      42,
      43,
      44,
      45,
      46,
      47,
      48,
      49,
      50,
      51,
      56,
      58,
      59,
      60,
      61,
      62,
      63,
      65,
      66,
      68,
      69,
      70,
      71,
      72,
      73,
      74,
      75,
      76,
      77,
      78,
      79,
      80,
      81,
      83,
      85,
      86,
      87,
      89,
      90,
      91,
      92,
      93,
      94,
      95,
      110,
      115,
      119,
      125,
      131,
      134,
      150,
      161,
      162]),
 ['0, 0, 0, final*, 0, final|, start|, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, final*, 0, final|, start|, 0, final*, 0, final|, start|, 0, 0, 0, start|, 0, 0, 0, 0, 0, 0, 0, start|, 0, start|, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, start|, 0, 0, start|, 0, 0, 0, 0, 0, final*, 0, final*, start*, 0, start|, 0, start|, 0, 0, start|, 0, start|, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, start|, 0, 0, 0, start|, 0, 0',
  'T_END_HEREDOC',
  'H_WHITESPACE',
  '$',
  '(',
  ',',
  'T_LNUMBER',
  'T_LNUMBER',
  '<',
  '@',
  'T_STRING',
  'T_NS_SEPARATOR',
  '`',
  '|',
  'T_COMMENT',
  'final*, 1, final*, start*, 0, final*, 0, 0, start|, 0, start|, 0, final|, start|, 0, final*, start*, 0, final*, 1, final*, 0, 0, start|, 0, start|, 0, start|, 0, final*, start*, 0, final*, 0, final*, 0, start|, 0, final|, start|, 0, 1, final|, start|, 0, final*, start*, 0, final*, 0, final*, 0, 1, final|, start|, 0, final|, start|, 0, final|, start|, 0, final*, start*, 0, final*, 0, final*, 0, final|, start|, 0, 1, final|, start|, 0, final|, start|, 0',
  '+',
  '/',
  ';',
  '?',
  '[',
  'T_STRING',
  '{',
  'H_NEW_LINE',
  '"',
  '&',
  '*',
  '.',
  ':',
  '>',
  '^',
  'T_STRING',
  '~',
  'H_TABULATURE',
  '1',
  '!',
  '%',
  ')',
  '-',
  '=',
  ']',
  '}',
  'T_IS_EQUAL',
  'T_DOUBLE_ARROW',
  'T_IS_IDENTICAL',
  'T_DEC',
  'T_MINUS_EQUAL',
  'T_OBJECT_OPERATOR',
  'T_MOD_EQUAL',
  'T_IS_NOT_EQUAL',
  'T_IS_NOT_IDENTICAL',
  'H_NEW_LINE',
  '0, final*, 1, final*, 0, 0, start|, 0, start|, 0, start|, 0, final*, start*, 0, final*, 0, final*, 0, start|, 0, final|, start|, 0, 1, final|, start|, 0, final*, start*, 0, final*, 0, final*, 0, 1, final|, start|, 0, final|, start|, 0, final|, start|, 0, final*, start*, 0, final*, 0, final*, 0, final|, start|, 0, 1, final|, start|, 0, final|, start|, 0, final*, start*, 0, final*, 0, 0, start|, 0, start|, 0, final|, start|, 0, final*, 1, final*, start*',
  '1, 0, final*',
  'final*, 1, 0',
  'final*, 1, final*, 0, start|, 0, final*, start*, 0, final*, 0, final|, start|, 0, 1, final*, start*, 0, final*, 0, 1, final|, start|, 0, final*, start*, 0',
  'T_START_HEREDOC',
  '1, 0',
  'T_CONSTANT_ENCAPSED_STRING',
  'T_XOR_EQUAL',
  'T_IS_GREATER_OR_EQUAL',
  'T_SR',
  'T_SR_EQUAL',
  'T_PAAMAYIM_NEKUDOTAYIM',
  'final|, final*, 0, final|, start|, 0, start|, 0, 0, final*, 1, final|, 1, final*, 0, final|, start|, 0, start|, 0, 0, final*',
  'T_DNUMBER',
  'T_CONCAT_EQUAL',
  'final|, final*, 1, final|, 0, 1, final|, final*, final|, 0',
  'T_DNUMBER',
  'T_MUL_EQUAL',
  'T_AND_EQUAL',
  'T_BOOLEAN_AND',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'T_STRING',
  'B_END_OF_CODE_BLOCK',
  '2, final*, 0, 0, start|, 0, start|, 0, 0, final*, start|, 0, 0, 0, 0, start*, final*, 0, final*, 0, final|, start|, 0, 1, final|, start|, 0, 0, final*, start*, 0, 0, 0, 0, start|, final*, 0, final*, 0, 1, final|, start|, 0, final|, start|, 0, 0, final*, start*, 0, 0, 0, 0, start|, final*, 0, final*, 0, final|, start|, 0, 1, final|, start|, 0, final*, 0, 1, final|, start|, 0, 0, 0, final*, start*, 0, final*, 0, 0, start|, 0, final|, start|, 0, 0, final|, start|, 0, final*, 0, 0, final*, final*, final|, 1, final|, final|, final*, start*, 0, final*, 0, 0, start|, 0, final|, start|, 0, 0, final|, start|, 0, final*, 0, 0, final*, final*, 1, final|, final|, final|, final*, start*, 0, final*, 0, 0, start|, 0, final|, start|, 0, 0, final|, start|, 0, final*, 0, 0, final*, final*, final|, 1, final|, final*, start*, 0, final*, 0, 0, start|, 0, final|, start|, 0, 0, final|, start|, 0, final*, 0, 0, final*, final*, final|, 1, final|, final|, final*, 1, final*, start*, 0',
  'T_DIV_EQUAL',
  'final*, final*, 0, 1, final*, start*, 0, 0, start|, 0, start|, 0, start|, 0, 0, final*, final*, 0, 1, final*, start*, 0, final*, 1, final*, 0, final*, start*, 0, 0, start|, 0, start|, 0, start|, 0, 0, final*, 1, final*, 0, final*, start*, 0',
  'T_COMMENT',
  'T_INC',
  'T_PLUS_EQUAL',
  '0, 1',
  'T_OR_EQUAL',
  'T_BOOLEAN_OR',
  'T_IS_SMALLER_OR_EQUAL',
  'T_SL',
  'T_IS_NOT_EQUAL',
  'T_SL_EQUAL',
  'T_LNUMBER',
  '2',
  '1, 1, 1',
  '1',
  '1',
  '1, 1',
  '2',
  '1',
  '1',
  '2, 2',
  '3, 3',
  '4',
  '4',
  '5',
  '6',
  'T_UNSET_CAST',
  '5',
  '6',
  '7',
  '8',
  'T_UNICODE_CAST',
  '2',
  '3',
  '5, final|, final*, 0, final|, final|, final*, 0, 4, 6, final|, final*, 0, final|',
  'T_DOUBLE_CAST',
  '2',
  '3',
  '4',
  '5',
  '6, final*, 0, final|, 6, final|, 0, final*',
  'T_STRING_CAST',
  '3',
  '4',
  '5',
  '6',
  '7',
  'T_OBJECT_CAST',
  '2, 2',
  'final*, 3, 0, 3, final|',
  'T_INT_CAST',
  '4',
  '5',
  '6',
  '7, final*, 0, final|',
  '2',
  '3',
  '4',
  '2',
  '3',
  '4',
  '5',
  '2',
  '2, 2',
  '3, 3',
  'final|, final*, 0, 4, 4',
  'T_BOOL_CAST',
  '5',
  '6',
  'final|, 7, final*, 0',
  '3',
  '4',
  '5',
  '3',
  '4',
  '5',
  '6',
  'T_ARRAY_CAST',
  'T_VARIABLE'])