
from rpython.rlib.rstring import StringBuilder
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rtyper.lltypesystem.rstr import copy_string_to_raw
from rpython.rtyper.annlowlevel import llstr

from hippy.builtin import Optional, ExitFunctionWithError, wrap, W_Root
from hippy.module.regex import _pcre
from hippy.constants import CONSTS


PREG_PATTERN_ORDER  = CONSTS['pcre']['PREG_PATTERN_ORDER']
PREG_SET_ORDER      = CONSTS['pcre']['PREG_SET_ORDER']
PREG_OFFSET_CAPTURE = CONSTS['pcre']['PREG_OFFSET_CAPTURE']
PREG_REPLACE_EVAL   = CONSTS['pcre']['PREG_REPLACE_EVAL']
PREG_NO_ERROR       = CONSTS['pcre']['PREG_NO_ERROR']
PREG_INTERNAL_ERROR        = CONSTS['pcre']['PREG_INTERNAL_ERROR']
PREG_BACKTRACK_LIMIT_ERROR = CONSTS['pcre']['PREG_BACKTRACK_LIMIT_ERROR']
PREG_RECURSION_LIMIT_ERROR = CONSTS['pcre']['PREG_RECURSION_LIMIT_ERROR']
PREG_BAD_UTF8_ERROR        = CONSTS['pcre']['PREG_BAD_UTF8_ERROR']
PREG_BAD_UTF8_OFFSET_ERROR = CONSTS['pcre']['PREG_BAD_UTF8_OFFSET_ERROR']
PREG_SPLIT_NO_EMPTY       = CONSTS['pcre']['PREG_SPLIT_NO_EMPTY']
PREG_SPLIT_DELIM_CAPTURE  = CONSTS['pcre']['PREG_SPLIT_DELIM_CAPTURE']
PREG_SPLIT_OFFSET_CAPTURE = CONSTS['pcre']['PREG_SPLIT_OFFSET_CAPTURE']


class PCE(object):
    def __init__(self, re, extra, poptions, coptions, capturecount,
                 subpat_names):
        self.re = re
        self.extra = extra
        self.poptions = poptions
        self.coptions = coptions
        self.capturecount = capturecount
        self.subpat_names = subpat_names

    def utf8size(self, subject, position):
        # Return the number of bytes taken by the character starting
        # at subject[position].  It may be greater than one with utf8.
        if self.coptions & _pcre.PCRE_UTF8:
            case = ord(subject[position])
            if case < 0xc0:
                return 1
            elif case < 0xe0:
                return 2
            elif case < 0xf0:
                return 3
            else:
                return 4
        else:
            return 1

    def __del__(self):
        _pcre.hippy_pcre_free2(self.re, self.extra)


def getfullinfo_int(re, extra, flag):
    p_result = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
    rc = _pcre.pcre_fullinfo(re, extra, flag, p_result)
    result = p_result[0]
    lltype.free(p_result, flavor='raw')
    if rc < 0:
        raise ExitFunctionWithError("Internal pcre_fullinfo() error %d" % rc)
    return rffi.cast(lltype.Signed, result)

def getfullinfo_charp(re, extra, flag):
    p_result = lltype.malloc(rffi.CCHARPP.TO, 1, flavor='raw')
    rc = _pcre.pcre_fullinfo(re, extra, flag, p_result)
    result = p_result[0]
    lltype.free(p_result, flavor='raw')
    if rc < 0:
        raise ExitFunctionWithError("Internal pcre_fullinfo() error %d" % rc)
    return result

def make_subpats_table(capturecount, re, extra):
    num_subpats = capturecount + 1
    subpat_names = [None] * num_subpats

    name_cnt = getfullinfo_int(re, extra, _pcre.PCRE_INFO_NAMECOUNT)
    if name_cnt > 0:
        name_table = getfullinfo_charp(re, extra, _pcre.PCRE_INFO_NAMETABLE)
        name_size = getfullinfo_int(re, extra, _pcre.PCRE_INFO_NAMEENTRYSIZE)
        for i in range(name_cnt):
            name_idx = 0xff * ord(name_table[0]) + ord(name_table[1])
            name = rffi.charp2str(rffi.ptradd(name_table, 2))
            try:
                int(name)
            except ValueError:
                pass
            else:
                raise ExitFunctionWithError("Numeric named subpatterns "
                                            "are not allowed")
            subpat_names[name_idx] = name
            name_table = rffi.ptradd(name_table, name_size)
    return subpat_names

def get_compiled_regex_cache(interp, regex):
    pce = interp.space.regex_cache.get(regex)
    if pce is not None:
        return pce

    if '\x00' in regex:
        raise ExitFunctionWithError("Null byte in regex")

    # Parse through the leading whitespace, and display a warning if we
    # get to the end without encountering a delimiter.
    i = 0
    while i < len(regex) and regex[i].isspace():
        i += 1
    if i == len(regex):
        raise ExitFunctionWithError("Empty regular expression")

    # Get the delimiter and display a warning if it is alphanumeric
    # or a backslash.
    delimiter = regex[i]
    if delimiter.isalnum() or delimiter == '\\':
        raise ExitFunctionWithError("Delimiter must not be alphanumeric "
                                    "or backslash")
    i += 1
    pattern_start = i
    start_delimiter = delimiter
    if   delimiter == '(': delimiter = ')'
    elif delimiter == '[': delimiter = ']'
    elif delimiter == '{': delimiter = '}'
    elif delimiter == '<': delimiter = '>'
    end_delimiter = delimiter

    if start_delimiter == end_delimiter:
        # We need to iterate through the pattern, searching for the
        # ending delimiter, but skipping the backslashed delimiters.
        # If the ending delimiter is not found, display a warning.
        while i < len(regex):
            if regex[i] == '\\':
                i += 1
            elif regex[i] == end_delimiter:
                break
            i += 1
        else:
            raise ExitFunctionWithError("No ending delimiter '%s' found"
                                        % delimiter[:])
    else:
        # We iterate through the pattern, searching for the matching
        # ending delimiter. For each matching starting delimiter, we
        # increment nesting level, and decrement it for each matching
        # ending delimiter. If we reach the end of the pattern without
        # matching, display a warning.
        brackets = 1       # brackets nesting level
        while i < len(regex):
            if regex[i] == '\\':
                i += 1
            elif regex[i] == end_delimiter:
                brackets -= 1
                if brackets == 0:
                    break
            elif regex[i] == start_delimiter:
                brackets += 1
            i += 1
        else:
            raise ExitFunctionWithError("No ending matching delimiter '%s' "
                                        "found" % delimiter[:])
    # Move on to the options
    pattern_end = i
    i += 1

    # Parse through the options, setting appropriate flags.  Display
    # a warning if we encounter an unknown modifier.
    coptions = 0
    poptions = 0
    do_study = False
    while i < len(regex):
        option = regex[i]
        i += 1
        # Perl compatible options
        if   option == 'i': coptions |= _pcre.PCRE_CASELESS
        elif option == 'm': coptions |= _pcre.PCRE_MULTILINE
        elif option == 's': coptions |= _pcre.PCRE_DOTALL
        elif option == 'x': coptions |= _pcre.PCRE_EXTENDED
        # PCRE specific options
        elif option == 'A': coptions |= _pcre.PCRE_ANCHORED
        elif option == 'D': coptions |= _pcre.PCRE_DOLLAR_ENDONLY
        elif option == 'S': do_study = True
        elif option == 'U': coptions |= _pcre.PCRE_UNGREEDY
        elif option == 'X': coptions |= _pcre.PCRE_EXTRA
        elif option == 'u':
            coptions |= _pcre.PCRE_UTF8
            if _pcre.PCRE_UCP is not None:
                coptions |= _pcre.PCRE_UCP
        # Custom preg options
        elif option == 'e':
            poptions |= PREG_REPLACE_EVAL
            raise ExitFunctionWithError("The deprecated /e modifier is not "
                                        "supported by hippy")

        elif option == ' ': pass
        elif option == '\n': pass
        else:
            raise ExitFunctionWithError("Unknown modifier '%s'" % option[:])

    # XXX missing:
    #if HAVE_SETLOCALE
    #  if (strcmp(locale, "C"))
    #      tables = pcre_maketables();
    #endif

    # Make a copy of the actual pattern.
    length = pattern_end - pattern_start
    pattern = lltype.malloc(rffi.CCHARP.TO, length + 1, flavor='raw')
    copy_string_to_raw(llstr(regex), pattern, pattern_start, length)
    pattern[length] = '\x00'

    # Compile pattern and display a warning if compilation failed.
    p_error = lltype.malloc(rffi.CCHARPP.TO, 1, flavor='raw', zero=True)
    p_erroffset = lltype.malloc(rffi.INTP.TO, 1, flavor='raw', zero=True)
    tables = lltype.nullptr(rffi.CCHARP.TO)

    re = _pcre.pcre_compile(pattern, coptions, p_error, p_erroffset, tables)

    error = p_error[0]
    erroffset = rffi.cast(lltype.Signed, p_erroffset[0])
    lltype.free(p_erroffset, flavor='raw')
    lltype.free(p_error, flavor='raw')
    lltype.free(pattern, flavor='raw')
    # All three raw mallocs above are now freed

    if not re:
        raise ExitFunctionWithError("Compilation failed: %s at offset %d" %
                                    (rffi.charp2str(error), erroffset))

    # If study option was specified, study the pattern and
    # store the result in extra for passing to pcre_exec.
    extra = lltype.nullptr(_pcre.pcre_extra)
    if do_study:
        soptions = 0
        #if _pcre.PCRE_STUDY_JIT_COMPILE is not None:
        #    soptions |= _pcre.PCRE_STUDY_JIT_COMPILE
        p_error = lltype.malloc(rffi.CCHARPP.TO, 1, flavor='raw', zero=True)
        extra = _pcre.pcre_study(re, soptions, p_error)
        error = p_error[0]
        lltype.free(p_error, flavor='raw')
        if error:
            interp.warn("Error while studying pattern")
    if not extra:
        extra = _pcre.hippy_pcre_extra_malloc()
    rffi.setintfield(extra, 'c_flags',
                     rffi.getintfield(extra, 'c_flags') |
                     _pcre.PCRE_EXTRA_MATCH_LIMIT |
                     _pcre.PCRE_EXTRA_MATCH_LIMIT_RECURSION)

    capturecount = getfullinfo_int(re, extra, _pcre.PCRE_INFO_CAPTURECOUNT)
    assert capturecount >= 0

    subpat_names = make_subpats_table(capturecount, re, extra)

    pce = PCE(re, extra, poptions, coptions,    # XXX also locale and tables
              capturecount, subpat_names)

    interp.space.regex_cache.set(regex, pce)
    return pce


def handle_exec_error(interp, code):
    if code == _pcre.PCRE_ERROR_MATCHLIMIT:
        preg_code = PREG_BACKTRACK_LIMIT_ERROR
    elif code == _pcre.PCRE_ERROR_RECURSIONLIMIT:
        preg_code = PREG_RECURSION_LIMIT_ERROR
    elif code == _pcre.PCRE_ERROR_BADUTF8:
        preg_code = PREG_BAD_UTF8_ERROR
    elif code == _pcre.PCRE_ERROR_BADUTF8_OFFSET:
        preg_code = PREG_BAD_UTF8_OFFSET_ERROR
    else:
        preg_code = PREG_INTERNAL_ERROR
    interp.regexp_error_code = preg_code


def _add_result(space, subpats, subject, offsets, i, flags=0,
                subpat_name=None):
    start = rffi.cast(lltype.Signed, offsets[i<<1])
    stop = rffi.cast(lltype.Signed, offsets[(i<<1)+1])
    return _add_result_range(space, subpats, subject, start, stop,
                             flags, subpat_name)

def _add_result_range(space, subpats, subject, start, stop, flags=0,
                      subpat_name=None):
    original_start = start
    if start >= stop:
        start = stop = 0
    else:
        assert 0 <= start <= stop <= len(subject)
    s = subject[start:stop]
    w_s = space.newstr(s)
    if flags & PREG_SPLIT_OFFSET_CAPTURE:
        w_s = space.new_array_from_list([w_s, space.newint(original_start)])
    if subpat_name is not None:
        w_key = space.newstr(subpat_name)
        subpats = space.packitem_maybe_inplace(subpats, w_key, w_s)
    subpats = space.appenditem_maybe_inplace(subpats, w_s)
    return subpats


MODE_PATTERN_ORDER = PREG_PATTERN_ORDER
MODE_SET_ORDER     = PREG_SET_ORDER
MODE_MATCH         = max(MODE_PATTERN_ORDER, MODE_SET_ORDER) + 1
MODE_SPLIT         = MODE_MATCH + 1
MODE_NO_SUBPAT     = MODE_SPLIT + 1


def match_impl(interp, pce, subject, w_matches, start_offset,
               mode, limit, flags):
    space = interp.space

    # Negative offset counts from the end of the string.
    if start_offset < 0:
        start_offset = len(subject) + start_offset
        if start_offset < 0:
            start_offset = 0

    rffi.setintfield(pce.extra, 'c_match_limit', interp.regexp_backtrack_limit)
    rffi.setintfield(pce.extra, 'c_match_limit_recursion',
                     interp.regexp_recursion_limit)

    # Calculate the size of the offsets array
    num_subpats = pce.capturecount + 1
    size_offsets = num_subpats * 3

    # Allocate match sets array and initialize the values.
    if mode == MODE_PATTERN_ORDER:
        match_sets = [space.new_array_from_list([])
                      for i in range(num_subpats)]
    else:
        match_sets = None

    # Allocate some more raw stuff
    offsets = lltype.malloc(rffi.INTP.TO, size_offsets, flavor='raw')
    if w_matches:
        subpats = space.new_array_from_list([])
    else:
        mode = MODE_NO_SUBPAT
        subpats = None
    try:
        exoptions = 0
        g_notempty = 0
        matched = 0
        last_match = 0
        interp.regexp_error_code = PREG_NO_ERROR
        while matched != limit:
            # Execute the regular expression.
            rawsubject = _get_buffer_from_str(subject)
            count = _pcre.pcre_exec(pce.re, pce.extra, rawsubject,
                                    len(subject), start_offset,
                                    exoptions|g_notempty,
                                    offsets, size_offsets)

            # the string was already proved to be valid UTF-8
            exoptions |= _pcre.PCRE_NO_UTF8_CHECK

            # Check for too many substrings condition.
            if count == 0:
                interp.notice("Matched, but too many substrings")
                count = size_offsets // 3

            # If something has matched
            if count > 0:
                matched += 1

                # If subpatterns array has been passed, fill it in with values.
                if mode == MODE_MATCH:
                    # Single pattern matching
                    # For each subpattern, insert it into the
                    # subpatterns array.
                    for i in range(count):
                        subpats = _add_result(space, subpats, subject,
                                              offsets, i, flags,
                                              pce.subpat_names[i])
                elif mode == MODE_PATTERN_ORDER:
                    # Global pattern matching, pattern order
                    # For each subpattern, insert it into the
                    # appropriate array.
                    for i in range(count):
                        match_sets[i] = _add_result(
                            space, match_sets[i], subject,
                            offsets, i, flags)
                    # If the number of captured subpatterns on this
                    # run is less than the total possible number,
                    # pad the result arrays with empty strings.
                    for i in range(count, num_subpats):
                        match_sets[i] = _add_result_range(
                            space, match_sets[i], subject, 0, 0,
                            flags=0)   # xxx why????

                elif mode == MODE_SET_ORDER:
                    # Global pattern matching, set order
                    sub1 = space.new_array_from_list([])
                    for i in range(count):
                        sub1 = _add_result(space, sub1, subject,
                                           offsets, i, flags,
                                           pce.subpat_names[i])
                    subpats = space.appenditem_maybe_inplace(subpats, sub1)

                elif mode == MODE_SPLIT:
                    next_head = rffi.cast(lltype.Signed, offsets[0])
                    no_empty = (flags & PREG_SPLIT_NO_EMPTY) != 0
                    if no_empty and next_head == last_match:
                        matched -= 1
                    else:
                        subpats = _add_result_range(space, subpats,
                                                    subject, last_match,
                                                    next_head, flags)
                    last_match = rffi.cast(lltype.Signed, offsets[1])

                    if flags & PREG_SPLIT_DELIM_CAPTURE:
                        for i in range(1, count):
                            start = rffi.cast(lltype.Signed, offsets[i<<1])
                            stop = rffi.cast(lltype.Signed,
                                             offsets[(i<<1)+1])
                            if no_empty and start == stop:
                                continue
                            subpats = _add_result_range(space, subpats,
                                                        subject, start,
                                                        stop, flags)

            elif count == _pcre.PCRE_ERROR_NOMATCH:
                # If we previously set PCRE_NOTEMPTY after a null match,
                # this is not necessarily the end. We need to advance
                # the start offset, and continue. Fudge the offset
                # values to achieve this, unless we're already at the
                # end of the string.
                if g_notempty != 0 and start_offset < len(subject):
                    offsets[0] = rffi.cast(rffi.INT, start_offset)
                    start_offset += pce.utf8size(subject, start_offset)
                    offsets[1] = rffi.cast(rffi.INT, start_offset)
                else:
                    break

            else:
                handle_exec_error(interp, count)
                break

            # If we have matched an empty string, mimic what Perl's /g
            # options does.  This turns out to be rather cunning. First
            # we set PCRE_NOTEMPTY and try the match again at the same
            # point. If this fails (picked up above) we advance to the
            # next character.
            g_notempty = (_pcre.PCRE_NOTEMPTY | _pcre.PCRE_ANCHORED
                          if (rffi.cast(lltype.Signed, offsets[1]) ==
                              rffi.cast(lltype.Signed, offsets[0]))
                          else 0)

            # Advance to the position right after the last full match
            start_offset = rffi.cast(lltype.Signed, offsets[1])

    finally:
        lltype.free(offsets, flavor='raw')

    if subpats:
        if mode == MODE_PATTERN_ORDER:
            # Add the match sets to the output array
            for i in range(num_subpats):
                match_set = match_sets[i]
                subpat_name = pce.subpat_names[i]
                if subpat_name is not None:
                    w_key = space.newstr(subpat_name)
                    subpats = space.packitem_maybe_inplace(subpats, w_key,
                                                           match_set)
                subpats = space.appenditem_maybe_inplace(subpats, match_set)

        elif mode == MODE_SPLIT:
            # the offset might have been incremented,
            # but without further successful matches
            start_offset = last_match

            no_empty = (flags & PREG_SPLIT_NO_EMPTY) != 0
            if no_empty and start_offset >= len(subject):
                pass
            else:
                subpats = _add_result_range(space, subpats,
                                            subject, start_offset,
                                            len(subject), flags)

        w_matches.store(subpats, unique=True)

    # Did we encounter an error?
    if interp.regexp_error_code == PREG_NO_ERROR:
        return space.newint(matched)
    else:
        return space.w_False


@wrap(['interp', str, str, Optional('reference'), Optional(int),
       Optional(int)], error=False)
def preg_match(interp, pattern, subject, w_matches=None, flags=0, offset=0):
    pce = get_compiled_regex_cache(interp, pattern)
    offset_capture = (flags & PREG_OFFSET_CAPTURE) != 0
    if flags & 0xff:
        raise ExitFunctionWithError("Invalid flags specified")
    return match_impl(interp, pce, subject, w_matches,
                      offset, mode=MODE_MATCH, limit=1,
                      flags=PREG_SPLIT_OFFSET_CAPTURE if offset_capture else 0)


@wrap(['interp', str, str, Optional('reference'), Optional(int),
       Optional(int)], error=False)
def preg_match_all(interp, pattern, subject, w_matches=None, flags=-909,
                   offset=0):
    pce = get_compiled_regex_cache(interp, pattern)

    offset_capture = False
    subpats_order = PREG_PATTERN_ORDER
    if flags != -909:
        offset_capture = (flags & PREG_OFFSET_CAPTURE) != 0
        if flags & 0xff:
            subpats_order = flags & 0xff
        if (subpats_order < PREG_PATTERN_ORDER or
            subpats_order > PREG_SET_ORDER):
            interp.warn("preg_match_all(): Invalid flags specified")
            return interp.space.w_Null
    return match_impl(interp, pce, subject, w_matches,
                      offset, mode=subpats_order, limit=-1,
                      flags=PREG_SPLIT_OFFSET_CAPTURE if offset_capture else 0)


# ___________________________________________________________

def get_replace(s):
    strings = None
    numbers = None
    prev_i = 0
    ofs = 0
    i = 0
    while i < len(s):
        ofs = 0
        if s[i] == '$' or s[i] == '\\':
            if s[i] == '$' and i + 1 < len(s) and s[i + 1] == "{":
                end_bracket = s.find("}", i + 1)
                if end_bracket != -1 and end_bracket - i < 4:
                    num = -1
                    if s[i + 2].isdigit() and s[i + 3].isdigit():
                        num = ((ord(s[i + 2]) - ord('0')) * 10 +
                               (ord(s[i + 3]) - ord('0')))
                        ofs = 4
                    elif s[i + 2].isdigit():
                        num = ord(s[i + 2]) - ord('0')
                        ofs = 3
                    if num != -1:
                        if not strings:
                            strings = []
                            numbers = []
                        strings.append(s[prev_i:i])
                        numbers.append(num)
                else:
                    i += 1
                    continue
            elif i + 1 < len(s) and s[i + 1].isdigit():
                if i + 2 < len(s) and s[i + 2].isdigit():
                    num = (ord(s[i + 1]) - ord('0')) * 10 + ord(s[i + 2]) - ord('0')
                    ofs = 2
                else:
                    num = ord(s[i + 1]) - ord('0')
                    ofs = 1
                if not strings:
                    strings = []
                    numbers = []
                strings.append(s[prev_i:i])
                numbers.append(num)
            prev_i = i + ofs + 1
        i += 1
    if strings is not None:
        strings.append(s[prev_i:len(s)])
        return ReplaceWithPatterns(strings, numbers)
    return BaseReplace(s)

class BaseReplace(object):
    def __init__(self, rval):
        self.rval = rval

    def setup(self, interp, pce):
        self.interp = interp
        self.pce = pce

    def next_replace(self, builder, subject, count, offsets):
        builder.append(self.rval)

class ReplaceCallback(BaseReplace):
    def __init__(self, w_callback):
        self.w_callback = w_callback

    def next_replace(self, builder, subject, count, offsets):
        space = self.interp.space
        subpats = space.new_array_from_list([])
        for i in range(count):
            subpats = _add_result(space, subpats, subject, offsets, i,
                                  subpat_name=self.pce.subpat_names[i])
        w_res = self.w_callback.call_args(self.interp, [subpats])
        builder.append(space.str_w(w_res))

class ReplaceWithPatterns(BaseReplace):
    def __init__(self, strings, nums):
        self.strings = strings
        self.nums = nums

    def next_replace(self, builder, subject, count, offsets):
        for i in range(len(self.nums)):
            builder.append(self.strings[i])
            num = self.nums[i]
            if num < count:
                start = rffi.cast(lltype.Signed, offsets[num<<1])
                stop = rffi.cast(lltype.Signed, offsets[(num<<1)+1])
            else:
                start = 0
                stop = 0
            builder.append_slice(subject, start, stop)
        builder.append(self.strings[-1])


def replace_impl(interp, pce, replace_obj, subject, limit=-1):
    replace_obj.setup(interp, pce)
    space = interp.space
    rffi.setintfield(pce.extra, 'c_match_limit', interp.regexp_backtrack_limit)
    rffi.setintfield(pce.extra, 'c_match_limit_recursion',
                     interp.regexp_recursion_limit)

    # Calculate the size of the offsets array
    num_subpats = pce.capturecount + 1
    size_offsets = num_subpats * 3

    # Initialize some stuff
    builder = StringBuilder(len(subject))

    # Allocate some more raw stuff
    offsets = lltype.malloc(rffi.INTP.TO, size_offsets, flavor='raw')
    try:
        exoptions = 0
        g_notempty = 0
        start_offset = 0
        original_limit = limit
        interp.regexp_error_code = PREG_NO_ERROR

        while limit != 0:
            # Execute the regular expression.
            rawsubject = _get_buffer_from_str(subject)
            count = _pcre.pcre_exec(pce.re, pce.extra, rawsubject,
                                    len(subject), start_offset,
                                    exoptions|g_notempty,
                                    offsets, size_offsets)

            # the string was already proved to be valid UTF-8
            exoptions |= _pcre.PCRE_NO_UTF8_CHECK

            # Check for too many substrings condition.
            if count == 0:
                interp.notice("Matched, but too many substrings")
                count = size_offsets // 3

            # If something has matched
            if count > 0:

                # copy the part of the string before the match
                match_end = rffi.cast(lltype.Signed, offsets[0])
                builder.append_slice(subject, start_offset, match_end)

                # ask the replace_obj how to handle this match
                replace_obj.next_replace(builder, subject, count, offsets)

                limit -= 1

            elif count == _pcre.PCRE_ERROR_NOMATCH:
                # If we previously set PCRE_NOTEMPTY after a null match,
                # this is not necessarily the end. We need to advance
                # the start offset, and continue. Fudge the offset
                # values to achieve this, unless we're already at the
                # end of the string.
                if g_notempty != 0 and start_offset < len(subject):
                    next_offset = start_offset
                    next_offset += pce.utf8size(subject, start_offset)
                    builder.append_slice(subject, start_offset, next_offset)
                    offsets[0] = rffi.cast(rffi.INT, start_offset)
                    offsets[1] = rffi.cast(rffi.INT, next_offset)
                else:
                    builder.append_slice(subject, start_offset, len(subject))
                    break

            else:
                handle_exec_error(interp, count)
                return None, -1

            # If we have matched an empty string, mimic what Perl's /g
            # options does.  This turns out to be rather cunning. First
            # we set PCRE_NOTEMPTY and try the match again at the same
            # point. If this fails (picked up above) we advance to the
            # next character.
            g_notempty = (_pcre.PCRE_NOTEMPTY | _pcre.PCRE_ANCHORED
                          if (rffi.cast(lltype.Signed, offsets[1]) ==
                              rffi.cast(lltype.Signed, offsets[0]))
                          else 0)

            # Advance to the position right after the last full match
            start_offset = rffi.cast(lltype.Signed, offsets[1])

        else:
            # reached limit == 0: copy the end of the string
            builder.append_slice(subject, start_offset, len(subject))

    finally:
        lltype.free(offsets, flavor='raw')

    return space.newstr(builder.build()), original_limit - limit


def replace_in_subject(interp, w_regex, w_replace, is_callback_replace,
                       subject, limit):
    space = interp.space
    if is_callback_replace:
        replace_obj = ReplaceCallback(w_replace)

    elif not space.is_array(w_replace):
        replace_obj = get_replace(space.str_w(w_replace))

    else:
        # If w_replace is an array, so is w_regex (checked earlier)
        replace_count = 0
        with space.iter(w_replace) as repl_itr:
            with space.iter(w_regex) as regex_itr:
                while not regex_itr.done():
                    w_value = regex_itr.next(space)
                    if repl_itr.done():
                        replacement = ""
                    else:
                        replacement = space.str_w(repl_itr.next(space))
                    replace_obj = get_replace(replacement)
                    pce = get_compiled_regex_cache(interp,
                                                   space.str_w(w_value))
                    w_value1, replace_count_1 = replace_impl(
                        interp, pce, replace_obj, subject, limit)
                    if w_value1 is None:
                        return None, -1
                    replace_count += replace_count_1
                    subject = space.str_w(w_value1)
        return space.newstr(subject), replace_count

    # If regex is an array
    if space.is_array(w_regex):
        replace_count = 0
        with space.iter(w_regex) as regex_itr:
            while not regex_itr.done():
                w_value = regex_itr.next(space)
                pce = get_compiled_regex_cache(interp, space.str_w(w_value))
                w_value1, replace_count_1 = replace_impl(
                    interp, pce, replace_obj, subject, limit)
                if w_value1 is None:
                    return None, -1
                replace_count += replace_count_1
                subject = space.str_w(w_value1)
        return space.newstr(subject), replace_count

    else:
        pce = get_compiled_regex_cache(interp, space.str_w(w_regex))
        return replace_impl(interp, pce, replace_obj, subject, limit)


def preg_replace_impl(interp, funcname, w_regex, w_replace, w_subject, limit,
                      w_count, is_callback_replace, is_filter):
    space = interp.space
    if not is_callback_replace:
        if not space.is_array(w_replace):
            w_replace = space.newstr(space.str_w(w_replace))
        elif not space.is_array(w_regex):
            interp.warn("%s(): Parameter mismatch, pattern is "
                        "a string while replacement is an array" % funcname)
            return space.w_False

    if not space.is_array(w_regex):
        w_regex = space.newstr(space.str_w(w_regex))

    if space.is_array(w_subject):
        # if subject is an array
        w_result = space.new_array_from_list([])
        replace_count = 0
        with space.iter(w_subject) as subj_itr:
            while not subj_itr.done():
                w_key, w_value = subj_itr.next_item(space)
                w_value1, replace_count_1 = replace_in_subject(
                    interp, w_regex, w_replace, is_callback_replace,
                    space.str_w(w_value), limit)
                if w_value1 is None:
                    continue
                if is_filter and replace_count_1 == 0:
                    continue
                replace_count += replace_count_1
                w_result = space.setitem_maybe_inplace(
                    w_result, w_key, w_value1)

    else:
        # if subject is not an array
        w_result, replace_count = replace_in_subject(
            interp, w_regex, w_replace, is_callback_replace,
            space.str_w(w_subject), limit)
        if is_filter and replace_count == 0:
            w_result = space.w_Null

    if w_count is not None and replace_count >= 0:
        w_count.store(space.newint(replace_count))
    return w_result


def replace_fastcase(interp, w_regex, replace_obj, w_subject, limit, w_count):
    space = interp.space
    pce = get_compiled_regex_cache(interp, space.str_w(w_regex))
    subject = space.str_w(w_subject)
    w_result, replcount = replace_impl(interp, pce, replace_obj, subject,
                                       limit)
    if w_count is not None:
        w_count.store(space.newint(replcount))
    return w_result


@wrap(['interp', W_Root, W_Root, W_Root, Optional(int), Optional('reference')])
def preg_replace(interp, w_regex, w_replace, w_subject, limit=-1,
                 w_count=None):
    space = interp.space
    if (space.is_array(w_regex) or space.is_array(w_replace) or
        space.is_array(w_subject)):
        # complex case: we are passed arrays
        return preg_replace_impl(interp, "preg_replace", w_regex,
                                 w_replace, w_subject, limit, w_count,
                                 is_callback_replace=False, is_filter=False)

    else:
        # fast case: we are only passed strings
        replace_obj = get_replace(space.str_w(w_replace))
        return replace_fastcase(interp, w_regex, replace_obj, w_subject,
                                limit, w_count)


@wrap(['interp', W_Root, 'callback', W_Root, Optional(int),
       Optional('reference')], error=None)
def preg_replace_callback(interp, w_regex, w_callback, w_subject, limit=-1,
                          w_count=None):
    space = interp.space
    if space.is_array(w_regex) or space.is_array(w_subject):
        # complex case: we are passed arrays
        return preg_replace_impl(interp, "preg_replace_callback", w_regex,
                                 w_callback, w_subject, limit, w_count,
                                 is_callback_replace=True, is_filter=False)

    else:
        # fast case: we are only passed strings
        replace_obj = ReplaceCallback(w_callback)
        return replace_fastcase(interp, w_regex, replace_obj, w_subject,
                                limit, w_count)


@wrap(['interp', W_Root, W_Root, W_Root, Optional(int), Optional('reference')])
def preg_filter(interp, w_regex, w_replace, w_subject, limit=-1,
                 w_count=None):
    return preg_replace_impl(interp, "preg_filter", w_regex,
                             w_replace, w_subject, limit, w_count,
                             is_callback_replace=False, is_filter=True)


# ____________________________________________________________


SPECIAL_CHARS = ('\\', '+', '*', '?', '[', '^', ']', '$', '(', ')', '{', '}',
                 '=', '!', '<', '>', '|', ':', '-')

@wrap(['space', str, Optional(str)], error=None)
def preg_quote(space, arg, delimiter=None):
    res = StringBuilder(len(arg))
    extra_char = chr(0)
    if delimiter is not None and len(delimiter) >= 1:
        extra_char = delimiter[0]
    for c in arg:
        if c == "\x00":
            res.append("\\000")
        else:
            if c in SPECIAL_CHARS or c == extra_char:
                res.append('\\')
            res.append(c)
    return space.wrap(res.build())


# ____________________________________________________________

@wrap(['interp', str, str, Optional(int), Optional(int)], error=False)
def preg_split(interp, pattern, subject, limit=-1, flags=0):
    pce = get_compiled_regex_cache(interp, pattern)
    limit -= 1
    w_matches = interp.space.empty_ref()
    match_impl(interp, pce, subject, w_matches, 0,
               mode = MODE_SPLIT, limit = limit, flags = flags)
    if interp.regexp_error_code == PREG_NO_ERROR:
        return w_matches.deref()
    else:
        return interp.space.w_False


# ____________________________________________________________

@wrap(['interp'])
def preg_last_error(interp):
    return interp.space.wrap(interp.regexp_error_code)


# ____________________________________________________________

from rpython.rtyper.lltypesystem import rstr, llmemory

def _get_buffer_from_str(data):
    # Dangerous!  The resulting pointer is only valid as long as there
    # is no GC!
    lldata = llstr(data)
    data_start = llmemory.cast_ptr_to_adr(lldata) + \
      rffi.offsetof(rstr.STR, 'chars') + rffi.itemoffsetof(rstr.STR.chars, 0)
    return rffi.cast(rffi.CCHARP, data_start)
