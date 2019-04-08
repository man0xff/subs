import click
import re
import string
import nltk
import collections

def extract_speech(file):
    skip_re = re.compile(r'(^\s*$)|(^\d+$)|( --> )')
    tag_re = re.compile(r'<[^>]+>')
    dash_re = re.compile(r'^- ')

    speech = []
    phrase = []

    for line in file:
        line = line.rstrip()
        if skip_re.search(line):
            continue
        line = tag_re.sub('', line)
        phrase.append(line)
        if phrase[-1][-1] in '.?!':
            phrase = dash_re.sub('', ' '.join(phrase)).strip()
            speech.append(phrase)
            phrase = []

    phrase = dash_re.sub('', ' '.join(phrase)).strip()
    speech.append(phrase)
    return speech

broken_words = (
    (re.compile(r"n't"), re.compile(r'\S+')),
    (re.compile(r"'.*"), re.compile(r'\w+')),
    (re.compile('na'),   re.compile(r'gon')),
)

def combine_broken_words(ngrams, len_):
    for i in range(len_, len(ngrams)):
        for w in broken_words:
            if w[0].match(ngrams[i][0]) and w[1].match(ngrams[i - 1][0]):
                restored = ngrams[i - 1][0] + ngrams[i][0]
                ngrams[i][0] = restored
                ngrams[i - len_][-1] = restored
                for j in range(i - len_ + 1, i):
                    del ngrams[i - 1]
                    ngrams.insert(0, [''])

def extract_ngrams(texts, len_):
    dummy = ['' for x in range(len_)]
    phrases = collections.Counter()

    for text in texts:
        for sent in nltk.sent_tokenize(text):
            words = dummy + nltk.word_tokenize(sent) + dummy
            
            ngrams = [list(x) for x in nltk.ngrams(words, len_)]
            combine_broken_words(ngrams, len_)
            ngrams = filter(lambda x: all(word != '' for word in x), ngrams)
            ngrams = filter(lambda x: not any(all(c in string.punctuation
                                for c in word) for word in x), ngrams)
            for ngram in ngrams:
                phrases[' '.join(ngram).lower()] += 1

    return phrases

def extract_words(texts):
    skipped = "the you it's i'm and".split()
    words = extract_ngrams(texts, 1)
    for k in list(words.keys()):
        if len(k) < 3:
            del words[k]
    for w in skipped:
        del words[w]
    return words

@click.command()
@click.argument('file', type=click.File('r'))
@click.option('-n', '--ngrams', type=int)
def main(ngrams, file):
    speech = extract_speech(file)
    if ngrams:
        items = extract_ngrams(speech, ngrams)
    else:
        items = extract_words(speech)
    for k,v in sorted(items.items(), key=lambda x: x[1]):
        print(v, k)

    return

main()
