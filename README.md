# HippyVM

HippyVM is an implementation of the PHP language using
[RPython/PyPy](http://pypy.org "pypy website") technology.

HippyVM right now works only on 64bit linux on x86 platform (this limitation
is temporary though, the RPython toolchain supports 32 and 64 bit x86,
ARMv6 and ARMv7 on windows, os x and linux).


## Building

The build process was tested for **Ubuntu 14.04**. Please create an issue/submit pull request if things are not working as expected.


#### 1. Clone this repo ;)

    git clone https://github.com/hippyvm/hippyvm

#### 2. Get a full source checkout of RPython: 

There are two alternative ways to achieve this, both equally functional:
   - [a snapshot](https://bitbucket.org/pypy/pypy/get/default.tar.gz) of PyPy is the easiest way to get a large repository.

        wget https://bitbucket.org/pypy/pypy/get/default.tar.gz 
        mkdir pypy 
        tar xfv default.tar.gz -C pypy --strip-components 1

   
   - [a full checkout](http://bitbucket.org/pypy/pypy) of the RPython repository translation toolchain (currently inside the PyPy repository). It will download the whole commit history of PyPy.

        hg clone http://bitbucket.org/pypy/pypy

 
#### 3. Get the build dependencies:

    pip install -r requirements.txt
    sudo apt-get install libmysqlclient-dev libpcre3-dev librhash-dev libbz2-dev php5-cli libffi-dev


#### 4. The building process goes like this:

    cd hippyvm
    <path to pypy>/rpython/bin/rpython -Ojit targethippy.py
    

This will create a hippy-c binary that works mostly like a php-cli without
readline support.



## Running it

You can run it with ./hippy-c <file.php>. Example of benchmarks are in bench/
sub-directory.



## Contribution

Like many open-source projects, HippyVM is looking for contributors.

In contrast with most language implementations that use C or C++, HippyVM has a low barrier of entry since it uses RPython, a subset of the Python language. It's really easy to write and read. Check out our implementation of [strstr](http://php.net/manual/pl/function.strstr.php)

```python
@wrap(['space', str, W_Root, Optional(bool)], aliases=['strchr'])
def strstr(space, haystack, w_needle, before_needle=False):
    """Find the first occurrence of a string."""
    try:
        needle = unwrap_needle(space, w_needle)
    except ValidationError as exc:
        space.ec.warn("strstr(): " + exc.msg)
        return space.w_False
    if len(needle) == 0:
        space.ec.warn("strstr(): Empty delimiter")
        return space.w_False
    pos = haystack.find(needle)
    if pos < 0:
        return space.w_False
    if before_needle:
        return space.newstr(haystack[:pos])
    else:
        return space.newstr(haystack[pos:])
```

Doesn't look that scary, right?

The reasons why HippyVM uses RPython go beyond this README. If you are interested, you can read more [here](http://pypy.readthedocs.org/en/latest/getting-started-dev.html)


### HippyVM's tests 

If the project is up and running, which means the building section from this README went well, you can try to run HippyVM's tests.

```bash
PYTHONPATH=$PYTHONPATH:/path-to-pypy py.test testing
```

This will execute all the tests that were explicitly written for HippyVM,
these tests are written in Python as well.
The example test for the `strstr` is [here](https://github.com/hippyvm/hippyvm/blob/master/testing/test_string_funcs.py#L696).

### PHP's tests 

After having HippyVM tests up and running you can
try running PHP's tests against the HippyVM implementation. 

```bash
PYTHONPATH=$PYTHONPATH:/path-to-pypy py.test test_phpt/
```

Those tests are exact copies from the [reference PHP implementation](https://github.com/php/php-src)


### What now?

If you find something missing, broken, or poorly implemented:
 - please create an issue, or better,
 - create a pull request and update the AUTHORS file.

Also please visit us on the irc channel #hippyvm@freenode.net 
