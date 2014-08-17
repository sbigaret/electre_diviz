=============
electre_diviz
=============

This is a collection of modules written for MCDA framework/suite `Diviz
<http://diviz.org>`_. They implement following concepts taken from the Electre
family of methods:

* concordance ('classic', with interactions between criteria, with reinforced
  preference)

* discordance (with pre-veto, counter-veto), binary discordance (Electre Is)

* credibility (Electre TRI, Electre IV, with counter-veto)

* finding the kernel of a graph (Electre Is)

* class assignments (Electre TRI, TRI-C, TRI-rC)

* outranking (crisp)

Please note that we refer to certain methods here (e.g. Electre TRI) only as
points of reference for their users (i.e. as a hint where these concepts
originate from) - they are *not* meant to suggest the only possible context in
which they should operate (although you rather don't want to use Credibility
from Electre TRI in Electre IV context).

It is also worth mentioning that most of the modules can accept as input both
'alternatives vs alternatives' and 'alternatives vs profiles' (boundary,
central) types of comparisons ('most' i.e. 'where it makes sense').

More detailed descriptions of the modules can be found in their respective
``description-wsDD.xml`` files.


Installation
------------

All modules from this package are written in Python 2.7.3. Apart from Python
itself, there are certain requirements/dependencies that must be met, i.e.:
``docopt (0.6.1)``, ``lxml (3.2.3)`` and ``networkx (1.8.1)``. The easiest (and
thus recommended) way to install them is by using ``virtualenv`` and ``pip`` -
let's assume that the contents of this repo has been cloned to
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

    (env)$ cd electre_diviz
    (env)$ ./tests_all.sh

If we don't get any errors in the output, then it means that everything went
fine.

It's also worth mentioning that there's a short help available for every
module, which can be displayed by using ``--help`` or ``-h`` switch, e.g.::

    (env)$ ./ElectreIsFindKernel --help


License
-------

This software is provided under the MIT License. For details, please refer to
the file ``LICENSE`` located in the main directory.
