#!/usr/bin/env python
""" ./runner.py -b <base php> -m <modified php>
"""
import os
import subprocess
import collections
import json


INTERPRETERS  = (
    ("PHP", "/usr/bin/php"), # Base interpreter
    ("HHVM", "/home/seba/things/hhvm/dev/hhvm/hphp/hhvm/hhvm -v Eval.Jit=true"),
    ("HippyVM", "../hippy-c"),
)

BENCHMARKS = (
    ('GcBench', "gcbench.php"),
    ('Fannkuch', 'fannkuch.php'),
    ('Fasta', 'fasta.php'),
    ('Heapsort', 'heapsort.php'),
    ('Richards', 'richards.php'),
    ('Spectral Norm', 'spectral_norm.php'),
    ('Nbody', 'nbody.php'),
    ('Nbody Modifed', 'nbody_modified.php'),
)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def bench(interpreter, name, source):

    target = os.path.join(BASE_DIR, source)

    stdout, stderr = subprocess.Popen(
        "%s %s" % (interpreter, target),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()

    if stderr:
        print "Interpreter %s Benchmark '%s' in %s returned\n%s" %\
            (interpreter, name, target, stderr)

    results = []
    for v in stdout.split():
        try:
            results.append(float(v))
        except ValueError as e:
            print "Interpreter %s Benchmark '%s' in %s returned something else than time, %s" % \
                (interpreter, name, target, e.message)

    return sum(results) / len(results)


def chart_data(results):
    colors = ["#000080", "#9EC0BB", "#101050"]
    data = []
    for interpreter, _ in INTERPRETERS:
        group_data = {
            "key": interpreter,
            "color": colors.pop(),
            "values": []
        }
        for benchmark_name, benchmark_results in results.items():
            group_data['values'].append({
                "label": benchmark_name,
                "value": [r for r in benchmark_results if r['name'] == interpreter][0]['ratio'],
                "time": [r for r in benchmark_results if r['name'] == interpreter][0]['time']
            })

        data.append(group_data)

    open(os.path.join(BASE_DIR, "data.json"), "w").write(json.dumps(data, indent=4))


def main():
    results = collections.OrderedDict()

    for name, source in BENCHMARKS:

        base_interpreter_name, base_interpreter = INTERPRETERS[0]
        base_time = bench(base_interpreter, name, source)

        results[name] = [
            {"name": base_interpreter_name, "time": base_time, "ratio": 1}
        ]

        for interpreter_name, interpreter_binary in INTERPRETERS[1:]:
            time = bench(interpreter_binary, name, source)

            results[name].append({
                "name": interpreter_name,
                "time": time,
                "ratio": time / base_time
            })

    chart_data(results)

    php_total = sum([e[0]['time'] for e in results.values()])
    hhvm_total = sum([e[1]['time'] for e in results.values()])
    hippvym_total = sum([e[2]['time'] for e in results.values()])

    print "PHP vs HippyVM: %s" % (php_total / hippvym_total)
    print "HHVM vs HippyVM: %s" % (hhvm_total / hippvym_total)

if __name__ == "__main__":
    main()
