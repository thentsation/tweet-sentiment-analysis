# Data files

* `vader_lexicon.txt`: the VADER sentiment lexicon as NLTK 3.10.4 distributes it (`nltk_data/sentiment/vader_lexicon.zip`).
  VADER is by C.J. Hutto and Eric Gilbert, MIT license: https://github.com/cjhutto/vaderSentiment. Hutto, C.J. &
  Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. ICWSM-14.
* `en-sentiment.xml`: the English subjectivity lexicon of the `pattern` library as TextBlob 0.20.1 ships it, by Tom De
  Smedt and Walter Daelemans, under the Public Domain Dedication and License (PDDL), as its header says. The code of
  `textblob.tvx` follows `textblob/_text.py` (pattern, BSD license, Copyright (c) 2011 University of Antwerp, Belgium)
  and `textblob/en/__init__.py` (TextBlob, MIT license, Steven Loria).
* `stopwords_english.txt`: the English stop words of the NLTK data (`corpora/stopwords/english`), taken from the
  Snowball lists of PostgreSQL and augmented by NLTK (https://github.com/nltk/nltk_data).
