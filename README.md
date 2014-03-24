HippyVM
=======

HippyVM is an implementation of the PHP language using
[RPython/PyPy](http://pypy.org "pypy website") technology.

HippyVM right now works only on 64bit linux on x86 platform (this limitation
is temporary though, the RPython toolchain supports 32 and 64 bit x86,
ARMv6 and ARMv7 on windows, os x and linux).

Building
========

1. You will need this repository, so please make yourself a "clone" :)
1. Install Python dependecies from `requirements.txt` file. The usual way is to create a [virtualenv](http://www.virtualenv.org/en/latest/) and then inside, but installing system wide (with sudo) is possible as well. Then: 

    ```
    pip install -r requirements.txt
    ```  
    
    If pip is not aviliable, please check [this](http://www.pip-installer.org/en/latest/installing.html).
    
1. Install system packages: 

   * `libpcre-dev` 
   * `php5`
   * `libffi5-dev`

1. Edit the PHP config (php.ini) 

   Find and edit line to `short_open_tag = On`

   Not sure where the php.ini file is? Check this thread [Dude, where's my php.ini?](http://stackoverflow.com/questions/8684609/dude-wheres-my-php-ini)

1. You'll need a [source](http://bitbucket.org/pypy/pypy) of the RPython translation toolchain. 
   You may try cloning the whole repo but having [a snapshot](https://bitbucket.org/pypy/pypy/get/default.tar.bz2) 
   of PyPy is the easiest way to get it fast.

1. Building goes like this (in **hippyvm** main directory):

   ```
   python <path to pypy>/rpython/bin/rpython -Ojit targethippy.py
   ```
   
   This will create a hippy-c binary that works mostly like a php cli without readling support.



Running it
==========

You can run it with ./hippy-c <file.php>. Example of benchmarks are in bench/
subdirectory.


Tests
=====

You'll need `py.test`:

    pip install pytest

To run tests fot **hippyvm**:
    
    py.test testing/
   
to run PHP's test on the top of the **hippyvm** interpreter: 
   
    py.test test_phpt/

