=============
electre_diviz
=============

This is a collection of modules written for MCDA suite `Diviz
<http://diviz.org>`_. They implement following methods/routines:

* Electre Is:     DiscordanceBinary, FindKernel, OutrankingBinary
* Electre IV:     Credibility
* Electre TRI-C:  ClassAssign, Concordance, Credibility, Discordances, SimplifiedClassAssign
* Electre TRI:    ClassAssign, Concordance, Credibility, Discordances

The last four of them are basically equivalent to ``ElectreTriExploitation``
module, which is already present in Diviz as a single, "monolithic" module. The
idea behind such split is that for some use-cases it may be convenient (or even
necessary) to get the possibility to access those parts separately.

Please note that modules' names refer to certain methods (e.g. Electre TRI)
only as a points of reference for their users (i.e. from where those modules
originate) - they are *not* meant to suggest the only possible context in which
they should operate (although you rather don't want to use e.g.  Credibility
from Electre TRI in Electre IV context, though).


Installation
------------

All modules from this package are written in Python 2.7.3. Apart from Python
itself, there are certain requirements/dependencies that must be met, namely:
``docopt (0.6.1)``, ``lxml (3.2.3)`` and ``networkx (1.8.1)``. The easiest (and
thus recommended) way to install them is by using ``virtualenv`` and ``pip``
(both being de facto standard in Python's community). Let's assume that
``electre_diviz.tgz`` got extracted to ``~/electre_diviz`` - after that, we
need to create a virtualenv (let's say we will name it just ``env``)::

    $ virtualenv env
    $ source env/bin/activate
    (env)$ pip install -r ~/electre_diviz/requirements

"``(env)$``" means that we have activated our newly created virtualenv - further
instructions assume that this step is completed successfully.

Another component that is required is `PyXMCDA
<https://gitorious.org/decision-deck/pyxmcda>`_ library, which is included
with the modules for user's convenience, hence there's no need to install it
separately.


Usage
-----

Having installed all the requirements and activated the virtualenv, we can test
if everything works as expected, e.g.::

    (env)$ cd ~/electre_diviz/ElectreIsFindKernel
    (env)$ mkdir test
    (env)$ ./ElectreIsFindKernel -i ./in -o ./test
    (env)$ diff -s ./out ./test

If we will get the message saying that the contents of the files in dirs
``out`` and ``test`` are identical, then it means that everything went fine.

It's also worth mentioning that there's a short help available for every
module, which can be displayed by using ``--help`` or ``-h`` switch, e.g.::

    (env)$ ./ElectreIsFindKernel --help


License
-------

This software is provided under MIT License. For details, please refer to the
file ``LICENSE`` located in the main directory.
