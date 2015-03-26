# PyHyp

PyHyp is a composition of PyPy and HippyVM.

## Building

First make sure you have enough RAM. 10GB should be enough.

Clone our PyPy fork and switch to the right branch:

```
$ hg clone https://bitbucket.org/softdevteam/pypy-hippy-bridge
$ cd pypy-hippy-bridge && hg up hippy_bridge
```

Then clone this repo somewhere and switch into the PyHyp branch:

```
$ git clone https://github.com/hippyvm/hippyvm
$ cd hippyvm
$ git checkout pypy_bridge
```

Install HippyVM dependencies:

```
$ pip install -r requirements.txt
$ sudo apt-get install libmysqlclient-dev libpcre3-dev librhash-dev libbz2-dev php5-cli libffi-dev
```

If you don't want to install pip packages as root, use `--user` or
alternatively use a virtualenv.

Finally, translate PyHyp:

```
$ python /path/to/pypy-hippy-bridge/rpython/bin/rpython -Ojit targethippy.py
```

When finished, the PyHyp binary is called `hippy-c`.

You can translate faster by using PyPy.

OpenBSD users should install a newer GCC (than base) and set `CC=egcc` prior to
translation.

Please report problems to [Edd Barrett](http://theunixzoo.co.uk)
