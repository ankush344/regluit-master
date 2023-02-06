# encoding: utf-8
## {{{ http://code.activestate.com/recipes/498104/ (r1)

## also https://stackoverflow.com/questions/4047511/checking-if-an-isbn-number-is-correct

import re

def check_digit_10(isbn):
    assert len(isbn) == 9
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        w = i + 1
        sum += w * c
    r = sum % 11
    if r == 10: return 'X'
    else: return str(r)

def check_digit_13(isbn):
    assert len(isbn) == 12
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        if i % 2: w = 3
        else: w = 1
        sum += w * c
    r = 10 - (sum % 10)
    if r == 10: return '0'
    else: return str(r)

def _convert_10_to_13(isbn):
    assert len(isbn) == 10
    prefix = '978' + isbn[:-1]
    check = check_digit_13(prefix)
    return prefix + check

def convert_10_to_13(isbn):
    try:
        isbn = ISBN(isbn)
        isbn.validate()
        if isbn.valid:
            return isbn.to_string()
        else:
            return None
    except:
        return None

ISBN_REGEX = re.compile(r'^(\d{9}[\dX]|\d{13})$')
DASH_REGEX = re.compile(u'[ \\-–—‐,;]+')  #includes unicode hyphen, endash and emdash
def strip(s):
    """Strips away any - or spaces and some punctuation.  If the remaining string is of length 10 or 13
    with digits only in anything but the last
    check digit (which may be X), then return '' -- otherwise return the remaining string
    """
    try:
        s = DASH_REGEX.sub('', s).upper()
        match = ISBN_REGEX.search(s)
    except:
        return None

    if not match:
        return None
    else:
        return s

def _convert_13_to_10(isbn):
    assert len(isbn) == 13
    # only ISBN-13 starting with 978 can have a valid ISBN 10 partner
    assert isbn[0:3] == '978'
    return isbn [3:12] + check_digit_10(isbn[3:12])

def convert_13_to_10(isbn):
    try:
        isbn = ISBN(isbn)
        isbn.validate()
        if isbn.valid:
            return isbn.to_string(type='10')
        else:
            return None
    except:
        return None

class ISBNException(Exception):
    pass

class ISBN(object):
    def __init__(self, input_isbn):
        self.input_isbn = input_isbn
        self.error = None

        stripped_isbn = strip(input_isbn)

        if stripped_isbn is None or len(stripped_isbn) not in (10, 13):
            self.error = "input_isbn does not seem to be a valid ISBN"
            self.__type = None
            self.__valid = False
            self.__isbn10 = None
            self.__valid_10 = None
            self.__isbn13 = None
            self.__valid_13 = None

        elif len(stripped_isbn) == 10:
            self.__type = '10'
            self.__isbn10 = stripped_isbn
            self.__valid_10 = stripped_isbn[0:9] + check_digit_10(stripped_isbn[0:9])
            self.__valid = (self.__isbn10 == self.__valid_10)

            # this is the corresponding ISBN 13 based on the assumption of a valid ISBN 10
            self.__isbn13 = _convert_10_to_13(stripped_isbn)
            self.__valid_13 = self.__isbn13

        elif len(stripped_isbn) == 13:
            # Assume ISBN 13 all have to begin with 978 or 979 and only 978 ISBNs
            # can possibly have ISBN-10 counterpart

            self.__type = '13'
            self.__isbn13 = stripped_isbn

            if stripped_isbn[0:3] not in ['978','979']:
                self.error = "ISBN 13 must begin with 978 or 979 not %s " % (stripped_isbn[0:3])
                self.__valid = False
                self.__valid_13  = None
            else:
                self.__valid_13 = stripped_isbn[0:12] + check_digit_13(stripped_isbn[0:12])
                self.__valid = (self.__isbn13 == self.__valid_13)

            # now check to see whether the isbn starts with 978 -- only then convert to ISBN -10
            if self.__isbn13[0:3] == '978':
                self.__isbn10 = _convert_13_to_10(stripped_isbn)
                self.__valid_10 = self.__isbn10
            else:
                self.__isbn10 = None
                self.__valid_10 = None

    @property
    def type(self):
        return self.__type
    @property
    def valid (self):
        return self.__valid
    def validate (self):
        """ replace the ISBN value with the checksumed version """
        if self.type == '10':
            self.__isbn10 = self.__valid_10
            self.__valid = True
            return self
        else:
            self.__isbn13 = self.__valid_13
            self.__valid = True
            return self
    def to_string(self, type='13', hyphenate=False):
        if not self.__valid:
            return None
        if type == '10' or type == 10:
            if self.__isbn10 is None:
                return None
            if hyphenate:
                s = self.__isbn10
                return "%s-%s-%s-%s" % (s[0], s[1:4], s[4:9], s[9])
            else:
                return self.__isbn10
        else:
            if hyphenate:
                s = self.__isbn13
                return "%s-%s-%s-%s-%s" % (s[0:3], s[3], s[4:7], s[7:12], s[12])
            else:
                return self.__isbn13
    def __unicode__(self):
        return unicode(self.to_string(type=self.type, hyphenate=False))
    def __str__(self):
        s = self.to_string(type=self.type, hyphenate=False)
        if s is not None:
            return s
        else:
            return ''
    def __eq__(self, other):
        """ both equal if both valid checksums and ISBN 13 equal """
        if isinstance(other, ISBN):
            if (self.valid and other.valid) and (self.to_string('13') == other.to_string('13')):
                return True
            else:
                return False
        else:
            try:
                other_isbn = ISBN(other)
                if ((self.valid and other_isbn.valid) and
                    (self.to_string('13') ==  other_isbn.to_string('13'))
                ):
                    return True
                else:
                    return False
            except:
                return False

    def __ne__(self, other):
        return not (self.__eq__(other))


