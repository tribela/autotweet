Autotweet
=========

Learn your response pattern on twitter.

Installation
------------

.. code-block:: console

   $ pip install git+https://github.com/Kjwon15/autotweet.git


Usage
-----

Learning user's tweet
~~~~~~~~~~~~~~~~~~~~~

Autotweet can learn your tweet by collector.

.. code-block:: console

   $ autotweet collector


Automatic answering by clone account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your clone account can automatic answer by answer command

.. code-block:: console

   $ autotweet answer


Web chatting
~~~~~~~~~~~~

You can test answer or chatting on web by server command

.. code-block:: console

   $ autotweet server


Add manually
~~~~~~~~~~~~

You can add question/answer set manually.

.. code-block:: console

   $ autotweet add 'Question' 'Answer'


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
