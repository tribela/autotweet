0.4.3
-----

- Logging when recalculating.
- Minor enhancement.
- Make telegram as optional requires.


0.4.2
-----

- Fix python 3 support.


0.4.1
-----

- Remove raw_input.
- Calculate cosine similarity correctly.


0.4.0
-----

- Telegram bot support.
- Unicode compatibility for Python 2/3.


0.3.2
-----

- Fix logger for `learning`.
- Support python 3.5.


0.3.1
-----

- New subcommand `get` added.


0.3.0
-----

- Ignoring tweet like "@id  Hello" (2 or more spaces between mention and msg).
- Import from your last tweets with `import` command.
- Expand urls on your answer.
- Changed module structure.


0.2.4
-----

- Fix operand error.
- add `Base` to `__all__`
- Remove unneeded session.begin


0.2.3
-----

- Fix typo on polling timeline in answer module.
- Raise NoAnswerError when there is no matching grams.
- Get mentions when threshold is set.
- Compatibility with tweepy>=3.0.


0.2.2
-----

- Fix mentioning to retweeted status.
- Add streaming mode on after_death command.
- Filter tweet by myself before get answer.


0.2.1
-----

- Raise `NoAnswerError` when can not found answer.
- Documentation.


0.2
---

- Remove `database.init_db`.
- Modify column `idf` to real number.
- Handle Twitter error on answer.
- Add `after_death` command for tweet after you died.
- Don't learn from answer by autotweet self.
- Option for use polling instead of streaming.

0.1.1
-----

- Autotweet can save sentences that is shorter than GRAM_LENGTH.
