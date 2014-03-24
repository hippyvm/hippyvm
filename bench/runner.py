#!/usr/bin/env python
""" ./runner.py -b <base php> -m <modified php>
"""

import optparse, sys, envoy, py, json

ALL_BENCHMARKS = ['arr', 'fib', 'binary_trees', 'fannkuch',
                  'fasta', 'heapsort']
ALL_BENCHMARKS.sort()

def run_bench(php):
    bench_dir = py.path.local(__file__).dirpath()
    results = {}
    for bench in ALL_BENCHMARKS:
        fullname = str(bench_dir.join(bench + '.php'))
        print "Running %s %s" % (php, fullname)
        r = envoy.run(php + " " + fullname)
        if r.status_code != 0:
            print r.std_out
            print r.std_err
            raise Exception("Non zero status code")
        all_t = r.std_out.splitlines()[-10:]
        try:
            for i in range(len(all_t)):
                all_t[i] = float(all_t[i])
        except ValueError:
            print r.std_out
            print r.std_err
            raise Exception("Did not complete correctly")
        else:
            print "Measured %r" % all_t
            results[bench] = all_t
    return results

def main(argv):
    parser = optparse.OptionParser()
    parser.add_option('-b', '--base')
    parser.add_option('-m', '--modified')
    parser.add_option('-o', '--output')
    options, args = parser.parse_args(argv)
    assert not args
    if not options.base:
        raise Exception("Specify base interpreter")
    base = run_bench(options.base)
    if options.modified:
        modified = run_bench(options.modified)
    else:
        modified = None
    if options.output:
        json.dump({'base': base, 'modified': modified},
                  open(options.output, "w"))

if __name__ == '__main__':
    main(sys.argv[1:])
