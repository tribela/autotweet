Autotweet
=========

Learn your response pattern on twitter.

.. image:: https://travis-ci.org/Kjwon15/autotweet.svg?branch=master
    :target: https://travis-ci.org/Kjwon15/autotweet


Installation
------------

.. code-block:: console

   $ pip install autotweet
   # Or with telegram bot
   $ pip install 'autotweet[telegram]'


Usage
-----

Learning user's tweet
~~~~~~~~~~~~~~~~~~~~~

Autotweet can learn your tweet by collector.

.. code-block:: console

   $ autotweet collector


Automatic answering by clone account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your clone account can automatic answer by answer command.

.. code-block:: console

   $ autotweet answer


Automaticaly tweet after death
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Autotweet can be auto tweeting using your main account.
Use it when you are leaving from twitter for any reason.

.. code-block:: console

   $ autotweet after_death


Add manually
~~~~~~~~~~~~

You can add question/answer set manually.

.. code-block:: console

   $ autotweet add 'Question' 'Answer'


Telegram integration
~~~~~~~~~~~~~~~~~~~~

You can run a telegram bot with learned database.

.. code-block:: console

   $ autotweet telegram -h


Configure
---------

You can configure Autotweet by editing ``~/.autotweetrc`` file.

.. code-block:: cfg

   [auth]
   token = <OAuth token (automaticaly generated)>
   answerer_token = <OAuth token (automaticaly generated)>

   [database]
   db_url = <database url>

   [answer]
   threshold = <Auto answering to tweet that is not mention to answerer. (float 0.0 ~ 1.0)>

   [tweet after death]
   message0 = This is message sent by auto tweet.
   message1 = If you are reading this, I'm already dead.


Links
-----

Package Index (PyPI)
   https://pypi.python.org/pypi/autotweet/

   .. image:: http://img.shields.io/pypi/v/autotweet.svg
      :target: https://pypi.python.org/pypi/autotweet/

Docs (ReadTheDocs)
   https://autotweet.readthedocs.org/

   .. image:: https://readthedocs.org/projects/autotweet/badge/
      :target: https://autotweet.readthedocs.org/


License
-------

Autotweet is following MIT license.
