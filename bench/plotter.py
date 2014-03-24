#!/usr/bin/env python
""" ./plotter.py <out json>
"""

import json, sys

WARMUP = 3

def avg(lst):
    return sum(lst) / len(lst)

def count_dev(lst):
    a = avg(lst)
    s = 0
    for k in lst:
        s += (a - k) * (a - k)
    return s**0.5 / len(lst)

def sep(maxcounts):
    return '+'.join([''] + ['-' * (k + 2) for k in maxcounts] + [''])

def main(argv):
    data = json.load(open(argv[0]))
    data2 = json.load(open(argv[1]))
    lines = [['benchmark', 'zend', 'hiphop VM', 'hiphop interpreted', 'hippy VM', 'hippy / zend', 'hippy / hiphop', 'hippy / hiphop interpreted']]
    for bench, d in data['modified'].iteritems():
        hippy = avg(d[WARMUP:])
        zend = avg(data['base'][bench])
        hphp = avg(data2['base'][bench])
        hphp_dev = int((count_dev(data2['base'][bench]) / hphp) * 100)
        hphp_interp_raw = data2['modified'][bench]
        hphp_interp = avg(hphp_interp_raw)
        hphp_interp_dev = int((count_dev(hphp_interp_raw) / hphp_interp) * 100)
        dev = int((count_dev(d[WARMUP:]) / hippy) * 100)
        lines.append([bench, '%.3f' % zend, '%.3f+-%d%%' % (hphp, hphp_dev),
                      '%.3f+-%d%%' % (hphp_interp, hphp_interp_dev),
                      '%.3f+-%d%%' % (hippy, dev),
                      '%.1fx' % (zend / hippy),
                      '%.1fx' % (hphp / hippy),
                      '%.1fx' % (hphp_interp / hippy)])
    maxcounts = [0] * len(lines[0])
    for line in lines:
        for i, elem in enumerate(line):
            maxcounts[i] = max(len(elem), maxcounts[i])
    separator = sep(maxcounts)
    print separator
    for line in lines:
        print '|' + '|'.join([' ' + elem + ' ' * (1 + maxcounts[i] - len(elem))
                        for i, elem in enumerate(line)]) + '|'
        print separator

if __name__ == '__main__':
    main(sys.argv[1:])
