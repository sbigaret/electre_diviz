=============
electre_diviz
=============

This is a collection of modules written for MCDA framework/suite `Diviz
<http://diviz.org>`_. They implement following routines or concepts taken from
Electre family methods:

* (Electre Is) Binary Discordance, Binary Outranking, Find Kernel

* (Electre IV) Credibility

* (Electre TRI-C) Concordance, Discordances, Credibility, Class Assignment,
  Simplified Class Assignment

* (Electre TRI) Concordance, Discordances, Credibility, Class Assignment

* Concordance with Interactions Between Criteria.

The four modules from Electre TRI method are basically equivalent to
``ElectreTriExploitation`` module, which is already present in Diviz as a
single, "monolithic" module. The idea behind this split is that for some
use-cases it may be convenient (or even necessary) to get the possibility to
access those parts separately.

Please note that modules' names refer to certain methods (e.g. Electre TRI)
only as points of reference for their users (i.e. to hint where those modules
originate from) - they are *not* meant to suggest the only possible context in
which they should operate (although you rather don't want to use Credibility
from Electre TRI in Electre IV context, though).

More detailed descriptions of the modules can be found in their respective
``description-wsDD.xml`` files.


Installation
------------

All modules from this package are written in Python 2.7.3. Apart from Python
itself, there are certain requirements/dependencies that must be met, i.e.:
``docopt (0.6.1)``, ``lxml (3.2.3)`` and ``networkx (1.8.1)``. The easiest (and
thus recommended) way to install them is by using ``virtualenv`` and ``pip``
(both being de facto standard in Python's community).

Let's assume that the contents of this repo has been cloned to
``electre_diviz`` directory - after that, we need to create a virtualenv (named
``env``)::

    $ virtualenv env
    $ source env/bin/activate
    (env)$ cd electre_diviz
    (env)$ pip install -r ./requirements

``(env)$`` in the command prompt means that we have activated our newly created
virtualenv - further instructions assume that this step is completed
successfully.

Another component that is required is `PyXMCDA
<https://gitorious.org/decision-deck/pyxmcda>`_ library, which is included
with the modules for user's convenience, hence there's no need to install it
separately.


Usage
-----

Having installed all the requirements and activated the virtualenv, we can test
if everything works as expected, e.g.::

    (env)$ cd electre_diviz/ElectreIsFindKernel
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

This software is provided under the MIT License. For details, please refer to
the file ``LICENSE`` located in the main directory.
