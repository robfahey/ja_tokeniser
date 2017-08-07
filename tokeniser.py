import MeCab, re
import signal

# Create a Tokenise object as such:
#       tokeniser = Tokenise(keywords=['keyword1', 'keyword2'], dictionary='neologd', japanese_only=True)

class Tokeniser(object):
    def __init__(self, keywords=None, dictionary='default', japanese_only=True):
        self._KAOFINDER = make_kaofinder()
        self._BRACKETFINDER = make_bracketfinder()
        self._EMOJIFINDER = make_emojifinder()
        self._URLFINDER = make_urlfinder()
        self._japanese_only = japanese_only
        self._re_text = '[0-9A-Za-zぁ-ヶ一-龠]'
        if dictionary == 'neologd':
            self._dictionary = 'neologd'
        else:
            self._dictionary = 'default'
        if keywords is None:
            self.keywords = []
        else:
            self.keywords = keywords

    def _find_keywords(self, tweet):
        returnvalue = []
        for key in self.keywords:
            returnvalue = returnvalue + [key for i in range(tweet.count(key))]
        return returnvalue

    def _kaomoji_recursefind(self, teststring, facelist):
        faces = self._KAOFINDER.findall(teststring)
        for kao in faces:
            if len(kao) > 10:
                if len(re.findall(self._re_text, kao)) > 4:
                    firstthird = self._KAOFINDER.match(kao[:int(len(kao) / 3)])
                    if firstthird is not None:
                        facelist.append(firstthird.group())
                        facelist = self._kaomoji_recursefind(teststring.replace(firstthird.group(), ''), facelist)
                    else:
                        firsthalf = self._KAOFINDER.match(kao[:int(len(kao) / 2)])
                        if firsthalf is not None:
                            facelist.append(firsthalf.group())
                            facelist = self._kaomoji_recursefind(teststring.replace(firsthalf.group(), ''), facelist)
                else:
                    facelist.append(kao)
            else:
                facelist.append(kao)
        return facelist

    def _find_kaomoji(self, tweet):
        return self._kaomoji_recursefind(tweet, [])  # This just kicks off the recursion process in kaomoji_recursefind.

    def _find_emoji(self, tweet):
        return self._EMOJIFINDER.findall(tweet)

    def _find_brackets(self, tweet):
        return self._BRACKETFINDER.findall(tweet)

    def _find_ellipsis(self, tweet):
        return re.findall("…", tweet, re.I)

    def _find_tokens(self, tweet):
        if self._dictionary == 'neologd':
            mt = MeCab.Tagger("-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd")
        else:
            mt = MeCab.Tagger()
        mt.parse('')  # Who knows why this is required but it seems to fix UnicodeDecodeError appearing randomly.
        parsed = mt.parseToNode(tweet)
        components = []
        while parsed:
            if parsed.surface == 'RT':
                components.append(('RT', 'RT_MARKER'))
            elif parsed.surface != '' and parsed.feature.split(',')[0] != "記号":
                components.append((parsed.surface, parsed.feature.split(',')[0]))
            parsed = parsed.next
        for a_keyword in self.keywords:
            cindex = 0
            while True:
                if cindex >= len(components):
                    break
                temp_key = a_keyword
                if components[cindex][0] == temp_key:  # If the keyword is already tagged as one item, no problem.
                    cindex += 1
                    continue
                elif components[cindex][0] == temp_key[
                                              :len(components[cindex][0])]:  # We just matched the start of a keyword.
                    match = False
                    tempindex = cindex
                    temp_key = temp_key.replace(components[tempindex][0], '', 1)
                    while True:
                        tempindex += 1
                        if tempindex >= len(components):  # There is no next element, so break.
                            break
                        else:  # Test next element.
                            if components[tempindex][0] == temp_key[:len(
                                    components[tempindex][0])]:  # if it matches the next component...
                                temp_key = temp_key.replace(components[tempindex][0], '', 1)
                                if temp_key == '':
                                    match = True
                                    break
                                else:
                                    continue
                            else:
                                break
                    if match:
                        components[cindex] = (a_keyword, 'PROJECT_KEYWORD')
                        del components[cindex + 1:tempindex + 1]  # First component we want to remove : first to keep.
                    cindex += 1
                    continue
                else:
                    cindex += 1  # This component doesn't match the start of a keyword, so continue.
                    continue

        return components

    def return_features(self, tweet):
        tweet_features = {'is_rt': False,
                          'is_reply': False,
                          'exclude': False,
                          'rt_account': None}

        if self.keywords != []:
            if len(self._find_keywords(tweet)) == 0:
                tweet_features['exclude'] = True

        if self._japanese_only:
            if re.search(r'(?:[ぁ-ヶ一-龠]+)', tweet) is None:
                tweet_features['exclude'] = True

        if re.match(r"RT\s@[A-z0-9_]+", tweet) is not None:
            tweet_features['is_rt'] = True
            tweet_features['rt_account'] = re.search(r'@([A-z0-9_]+)', tweet).group()
        elif re.match(r"@([A-z0-9_]+)", tweet) is not None:
            tweet_features['is_reply'] = True

        return tweet_features


    def return_tokens(self, tweet):

        temp_content = tweet
        temp_tags = []

        if self._japanese_only:
            if re.search(r'(?:[ぁ-ヶ一-龠]+)', tweet) is None:
                return 'NON_JAPANESE'

        for an_emoji in self._find_emoji(temp_content):
            temp_tags.append((an_emoji, 'EMOJI'))
            temp_content = temp_content.replace(an_emoji, ' ')
        for a_username in re.findall("@([a-z0-9_]+)", temp_content, re.I):
            temp_tags.append(('@' + a_username, 'USERNAME'))
            temp_content = temp_content.replace('@' + a_username, ' ')
        for a_hashtag in re.findall("#([a-z0-9ぁ-ヶ一-龠_]+)", temp_content, re.I):
            temp_tags.append(('#' + a_hashtag, 'HASHTAG'))
            temp_content = temp_content.replace('#' + a_hashtag, ' ')
        with timeout(10, error_message='Timed out on: {}'.format(temp_content)):
            for a_url in self._URLFINDER.findall(temp_content):
                temp_tags.append((a_url[0], 'URL'))
                temp_content = temp_content.replace(a_url[0], ' ')
        temp_content = temp_content.replace('…', ' ')
        for a_bracket in self._find_brackets(temp_content):
            temp_tags.append((a_bracket.strip('\n'), 'KANDOUJI'))
            temp_content = temp_content.replace(a_bracket, ' ')
        for a_face in self._find_kaomoji(temp_content):
            temp_tags.append((a_face.strip('\n'), 'KAOMOJI'))
            temp_content = temp_content.replace(a_face, ' ')

        temp_tags = temp_tags + self._find_tokens(temp_content)

        return temp_tags


# Non-class methods below this line.

def make_kaofinder():
    re_text = '[0-9A-Za-zぁ-ヶ一-龠]'
    re_nontext = '[^0-9A-Za-zぁ-ヶ一-龠]'
    re_allowtext = '[ovっつ゜ニノ三二]'
    re_hwkana = '[ｦ-ﾟ]'
    re_openbracket = r'[\(∩꒰（]'
    re_closebracket = r'[\)∩꒱）]'
    re_aroundface = '(?:' + re_nontext + '|' + re_allowtext + ')*'
    re_face = '(?!(?:' + re_text + '|' + re_hwkana + '){3,}).{3,}'
    KAOFINDER = re.compile(re_aroundface + re_openbracket + re_face + re_closebracket + re_aroundface)
    # Based on Kurosaki, Y., Takagi, T. (2015),　'Word2Vec を用いた顔文字の感情分類',
    #   in Proceedings of the Annual Meeting of The Association for Natural Language Processing, March 2015
    return KAOFINDER


def make_bracketfinder():
    re_text = '[0-9A-Za-zぁ-ヶ一-龠]'
    BRACKETFINDER = re.compile(r'[\(（]' + re_text + r'[\)）]')
    return BRACKETFINDER


def make_emojifinder():
    with open('emoji_list.txt') as f:
        raw_regex = ''.join(f.readlines()).strip()
    EMOJIFINDER = re.compile(raw_regex)
    return EMOJIFINDER


def make_urlfinder():
    URLFINDER = re.compile(
        r'(?i)\b((?:https?:\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>ぁ-ヶ一-龠【】]+|\(([^\s()<>ぁ-ヶ一-龠【】]+|(\([^\s()<>ぁ-ヶ一-龠【】]+\)))*\))+(?:\(([^\s()<>ぁ-ヶ一-龠【】]+|(\([^\s()<>ぁ-ヶ一-龠【】]+\)))*\)|[^\sぁ-ヶ一-龠【】`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
    return URLFINDER


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)