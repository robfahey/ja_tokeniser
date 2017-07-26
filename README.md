# ja_tokeniser
MeCab-based Japanese Language Tokeniser optimised for Twitter Data

This is a simple Python object which encapsulates the various pre-processing and tokenisation steps for handling Japanese-language Twitter data which I outlined in [this blog post](http://www.robfahey.co.uk/blog/tidying-japanese-sns-data-machine-learning/).

### Requirements

You need to have MeCab installed, and to use the neologism dictionary (the default dictionary for this Tokeniser), you'll need that installed too. You can find installation instructions for MacOS and Ubuntu in [this blog post](http://www.robfahey.co.uk/blog/japanese-text-analysis-in-python/).

### Usage

Import the object: 

```python
from tokeniser import Tokeniser
```

Initialise it with your chosen options: 

```python
tokeniser = Tokeniser(keywords=['keyword1', 'keyword2'], dictionary='neologd|default', japanese_only=True)
```

*keywords* are terms which must appear in the tweet, or it will be marked as irrelevant (though it'll still be tokenised). This functionality is useful if you've downloaded Twitter data from somewhere like Crimson Hexagon, which makes a spectacular mess of Japanese language keyword searches and can return a lot of invalid results.

*dictionary* is a choice of which MeCab dictionary to use. The default is the ordinary MeCab dictionary; at present the only other option is to set this to 'neologd'. This will use the *mecab-ipadic-neologd* neologism dictionary, which is generally very good for handling social media data. Setting this value to anything else will fall back to the default MeCab dictionary. Note that the code presently assumes that the neologism dictionary is installed in */usr/local/lib/mecab/dic/mecab-ipadic-neologd* - if you have installed it elsewhere, you can edit line 63 of the code to fix this.

*japanese_only* enables a function which will exclude and ignore tweets that contain no Japanese language characters (hiragana, katakana, kanji).

The object is now ready to start processing tweets. There are two functions available to you: `Tokenise.return_features(text)` and `Tokenise.return_tokens(text)`

#### Tokenise.return_features(text)

Returns a dictionary of features describing the tweet passed in `text`. The features are:

* is_rt   (Boolean)
* is_reply  (Boolean)
* exclude  (Boolean \- set to *True* if no keywords could be matched or if the text contained no Japanese.)
* rt_account (String \- which account is being retweeted. *None* if this isn't an RT.)

#### Tokenise.return_tokens(text)

Returns a list of tuples in the form `(token, part-of-speech)` for the tweet passed in `text`. If *japanese_only* is enabled (as it is by default), in cases where the tweet contained no Japanese language characters, this instead returns the string `'NON_JAPANESE'` - be careful to check for this in your code before processing the tuples.

*part-of-speech* is normally the highest level output from MeCab \- i.e. something like 名詞 or 動詞 signifying the type of word.

There are also some special cases for part of speech:

* _USERNAME_ \- a Twitter username, including the @ sign.
* _HASHTAG_ \- a Twitter hashtag, including the # sign.
* _URL_ \- a web address.
* _EMOJI_ \- an emoji (returned as-is in unicode).
* _KAOMOJI_ \- a Japanese-style "smiley" made from punctuation characters etc.
* _KANDOUJI_ \- an "emotion" character like 笑 or 汗 enclosed in brackets.
* _RT\_MARKER_ \- the "RT" term used to denote a retweet.


