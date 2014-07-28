# HippyVM

HippyVM is an implementation of the PHP language using
[RPython/PyPy](http://pypy.org "pypy website") technology.

HippyVM right now works only on 64bit linux on x86 platform (this limitation
is temporary though, the RPython toolchain supports 32 and 64 bit x86,
ARMv6 and ARMv7 on windows, os x and linux).


## Building

The build process was tested for **Ubutnu 14.04**. Please create an issue/submit pull request if things are not working as expected.


1. Clone this repo ;)

        git clone https://github.com/hippyvm/hippyvm

2. Get the full checkout of RPython repository. The two alternatives ways to achieve this, both equally functionall:
   - [a snapshot](https://bitbucket.org/pypy/pypy/get/default.tar.gz) of PyPy is the easiest way to get a large repository.

        ```bash
        wget https://bitbucket.org/pypy/pypy/get/default.tar.gz 
        mkdir pypy
        tar xfv default.tar.gz -C pypy --strip-components 1
        ```
   
   - [a full checkout](http://bitbucket.org/pypy/pypy) of the RPython repository translation toolchain (currently inside the PyPy repository). It will download whole PyPy commit history 

        ```bash
        hg clone http://bitbucket.org/pypy/pypy
        ```
 
3. The build dependencies:

    ```bash
    pip install -r requirements.txt
    sudo apt-get install libmysqlclient-dev libpcre3-dev librhash-dev libbz2-dev php5-cli
    ```

3. The building process goes like this (in HippyVm main directory):

    ```bash
    cd hippyvm
    <path to pypy>/rpython/bin/rpython -Ojit targethippy.py
    ```

This will create a hippy-c binary that works mostly like a php-cli without
readling support.



## Running it

You can run it with ./hippy-c <file.php>. Example of benchmarks are in bench/
sub-directory.



## Contribution

As many opensource projects, HippyVM is looking for contributors.

HippyVM has a really low barrier of entry, differently than other VM's is not using nigher C nor C++, it uses RPython, which syntax is subset of Python language. It's really easy to write and read. Check out our implementation of [strstr](http://php.net/manual/pl/function.strstr.php)

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

The idea why HippyVM is using RPython goes beyond this README, though if you being interested, please have read more [here](http://pypy.readthedocs.org/en/latest/getting-started-dev.html)


### HippyVM's tests 

If the project is up and running, which means the building section from this README went well, you can try to run HippyVM's tests.

```bash
PYTHONPATH=$PYTHONPATH:/path-to-pypy py.test testing
```

This will execute all tests that were written for HippyVM explicitly,
those test are written in Python as well.
The example test for the `strstr` [here](https://github.com/hippyvm/hippyvm/blob/master/testing/test_string_funcs.py#L696).

### PHP's tests 

After having HippyVM tests up and running you can
try running PHP's tests against the HippyVM implementation. 

```bash
 PYTHONPATH=$PYTHONPATH:../pypy py.test test_phpt/
```

Those tests are moved over the [PHP implementation](https://github.com/php/php-src)


### What now?

If you find something missing, being broken, poorly implemented:
 - please create an issue, or better,
 - create a pull request and update the AUTHORS file.

Also please visit us on the irc channel #hippyvm@freenode.net 
