===============================================================================
 Demonstrate issue with list ordering in docker-compose 1.5.0 (`issue 2342`__)
===============================================================================

This is a s{a/i}ample project that demonstrate an issue with the way docker-compose
configuration is loaded and interpolated.

It seems the new functionality is perturbed by the `hash randomization`__ feature introduced in
Python 3.3 (backported to Python 2.7, off by default).

__ https://github.com/docker/compose/issues/2342
__ https://docs.python.org/3/using/cmdline.html#envvar-PYTHONHASHSEED

Why it matters
==============

I'm using doit__ to automate some tasks. In particular I use its ability__ to keep an hash of
some configuration settings to *optimize* the build step, that is, to perform the build only
when needed because some setting has been changed.

__ http://pydoit.org/
__ http://pydoit.org/uptodate.html?highlight=config_changed#config-changed

As soon I switched one of my projects to Python 3, I quickly found that something wasn't
working as expected: the build task was invoking needless recompilation, but even
``docker-compose up`` kept recreating some of the services, even if their configuration didn't
change at all.

At first I thought that tweaking the `config_changed()`__ function to use ``pprint.pformat()``
instead of a plain ``repr()`` would be enough\ [*]_, but after some further investigation I found
that not only the ordering of *keys* in a dictionary was changing from one run to the next, but
also the ordering of *items* in various lists (``volumes``, to mention one).

__ https://github.com/pydoit/doit/blob/fc97427bb5e912b6544e91a4049e14aa2b5570a3/doit/tools.py#L62
.. [*] See https://github.com/pydoit/doit/issues/113

Demonstration
=============

This tiny example, adapted from the `getting started`__ chapter of the documentation, exhibits
the problem: the configuration of the ``web`` service defines two ``volumes``, in alphabetical
order, but when ``docker-compose`` reads it, that order is not (always) respected::

    $ tox
    py27 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py27 runtests: PYTHONHASHSEED='948517400'
    py27 runtests: commands[0] | ….tox/py27/bin/python …test.py
    {'ports': ['5000:5000'], 'volumes': ['…app:/srv/app', '…www:/srv/www'], 'build': '/tmp/testdc'}
    py34 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py34 runtests: PYTHONHASHSEED='948517400'
    py34 runtests: commands[0] | ….tox/py34/bin/python …test.py
    {'build': '/tmp/testdc', 'volumes': ['…app:/srv/app', '…www:/srv/www'], 'ports': ['5000:5000']}
    _______________ summary _______________
      py27: commands succeeded
      py34: commands succeeded
      congratulations :)

    $ tox
    py27 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py27 runtests: PYTHONHASHSEED='420369442'
    py27 runtests: commands[0] | ….tox/py27/bin/python …test.py
    {'ports': ['5000:5000'], 'volumes': ['…app:/srv/app', '…www:/srv/www'], 'build': '/tmp/testdc'}
    py34 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py34 runtests: PYTHONHASHSEED='420369442'
    py34 runtests: commands[0] | ….tox/py34/bin/python …test.py
    {'ports': ['5000:5000'], 'volumes': ['…app:/srv/app', '…www:/srv/www'], 'build': '/tmp/testdc'}
    _______________ summary _______________
      py27: commands succeeded
      py34: commands succeeded
      congratulations :)

    $ tox
    py27 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py27 runtests: PYTHONHASHSEED='774086394'
    py27 runtests: commands[0] | ….tox/py27/bin/python …test.py
    {'build': '/tmp/testdc', 'volumes': ['…www:/srv/www', '…app:/srv/app'], 'ports': ['5000:5000']}
    Traceback (most recent call last):
      File "…test.py", line 34, in <module>
        main()
      File "…test.py", line 31, in main
        assert volumes == sorted(volumes)
    AssertionError
    ERROR: InvocationError: '….tox/py27/bin/python …test.py'
    py34 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py34 runtests: PYTHONHASHSEED='774086394'
    py34 runtests: commands[0] | ….tox/py34/bin/python …test.py
    {'ports': ['5000:5000'], 'build': '/tmp/testdc', 'volumes': ['…app:/srv/app', '…www:/srv/www']}
    _______________ summary _______________
    ERROR:   py27: commands failed
      py34: commands succeeded

    $ tox
    py27 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py27 runtests: PYTHONHASHSEED='2212156821'
    py27 runtests: commands[0] | ….tox/py27/bin/python …test.py
    {'ports': ['5000:5000'], 'volumes': ['…www:/srv/www', '…app:/srv/app'], 'build': '/tmp/testdc'}
    Traceback (most recent call last):
      File "…test.py", line 34, in <module>
        main()
      File "…test.py", line 31, in main
        assert volumes == sorted(volumes)
    AssertionError
    ERROR: InvocationError: '….tox/py27/bin/python …test.py'
    py34 installed: docker-compose==1.5.0,docker-py==1.5.0,…
    py34 runtests: PYTHONHASHSEED='2212156821'
    py34 runtests: commands[0] | ….tox/py34/bin/python …test.py
    {'build': '/tmp/testdc', 'volumes': ['…www:/srv/www', '…app:/srv/app'], 'ports': ['5000:5000']}
    Traceback (most recent call last):
      File "…test.py", line 34, in <module>
        main()
      File "…test.py", line 31, in main
        assert volumes == sorted(volumes)
    AssertionError
    ERROR: InvocationError: '….tox/py34/bin/python …test.py'
    _______________ summary _______________
    ERROR:   py27: commands failed
    ERROR:   py34: commands failed

__ http://docs.docker.com/compose/gettingstarted/

Conclusion
==========

While I understand that from the operational point of view this may be a non-issue (that is,
everything works, even if sub optimally), it's a bit surprising that the ordering of list items
changes between runs. It may have bad effects when for some reason the order is important (I
cannot imagine a use case right now, but maybe a future setting may relay on a particular
order...)
