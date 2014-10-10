0.2.3
-----

- Fix typo on polling timeline in answer module.
- Raise NoAnswerError when there is no matching grams.
- Get mentions when threshold is set.


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
