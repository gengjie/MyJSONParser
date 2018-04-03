#! /usr/bin/python
from enum import Enum
from StringIO import StringIO

import time


class TokenType(Enum):
    START_OBJ = 1
    END_OBJ = 2
    START_ARRAY = 3
    END_ARRAY = 4
    NULL = 5
    NUMBER = 6
    STRING = 7
    BOOLEAN = 8
    COLON = 9
    COMMA = 10
    END_DOC = 11


class Token(object):

    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value
    
    def is_type(self, _token_type):
        return self.token_type == _token_type

    def is_primary(self):
        return self.is_type(TokenType.STRING) or \
            self.is_type(TokenType.NUMBER) or \
            self.is_type(TokenType.BOOLEAN) or \
            self.is_type(TokenType.NULL)


class Tokenizer(object):

    def __init__(self, content):
        self.fd = StringIO(content)
        self.tokens = []
        self.__is_open = True
        self.c = '?'
        self.saved_c = '?'
        self.is_unread = False

    def tokenize(self):
        token  = self.start()
        self.tokens.append(token)
        while token.token_type != TokenType.END_DOC:
            token  = self.start()
            self.tokens.append(token)
        self.destory()
        return self.tokens

    def start(self):
        self.c = self.__read()
        while self.is_space(self.c):
            self.c = self.__read()
        if self.is_x(self.c, 'null'):
            return Token(TokenType.NULL, None)
        elif self.c == ',':
            return Token(TokenType.COMMA, ',')
        elif self.c == ':':
            return Token(TokenType.COLON, ':')
        elif self.c == '{':
            return Token(TokenType.START_OBJ, '{')
        elif self.c == '[':
            return Token(TokenType.START_ARRAY, '[')
        elif self.c == ']':
            return Token(TokenType.END_ARRAY, ']')
        elif self.c == '}':
            return Token(TokenType.END_OBJ, '}')
        elif self.is_true(self.c):
            return Token(TokenType.BOOLEAN, True)
        elif self.is_false(self.c):
            return Token(TokenType.BOOLEAN, False)
        elif self.c == '"':
            return self.read_str()
        elif self.is_num(self.c):
            self.__unread()
            return self.read_num()
        elif self.c == -1:
            return Token(TokenType.END_DOC, 'EOF')
        else:
            raise JsonParserException('Invalid JSON input.')

    def destory(self):
        if self.fd is not None:
            self.fd.close()

    def __read(self):
        if self.__is_open:
            if not self.is_unread:
                self.saved_c = self.fd.read(1)
                return self.saved_c
            else:
                self.is_unread = False
                return self.saved_c
        else:
            raise TokenizerException("Can not read an unopened stream!")

    def __unread(self):
        self.is_unread = True

    def is_x(self, c, x):
        assert isinstance(x, str)
        if not isinstance(c, str):
            return False
        if not x.startswith(c):
            return False
        for _c in x:
            if c == _c:
                c = self.__read()
            else:
                raise JsonParserException('Invalid JSON Input!')
        self.__unread()
        return True

    def is_null(self, c):
        if c == 'n':
            c = self.__read()
            if c == 'u':
                c = self.__read()
                if c == 'l':
                    c = self.__read()
                    if c == 'l':
                        return True
                    else:
                        raise JsonParserException('Invalid JSON input!')
                else:
                    raise JsonParserException('Invalid JSON input!')
            else:
                raise JsonParserException('Invalid JSON input!')
        else:
            return False

    def is_space(self, c):
        return c >= 0 and c <= ' '

    def is_true(self, c):
        return self.is_x(c, "true")

    def is_false(self, c):
        return self.is_x(c, "false")

    def is_escape(self, c):
        if c == '\\':
            c = self.__read()
            if c == '"' or c == '\\' or c == '/' or c == 'b' or c == 'f' or \
                    c == 'n' or c == 't' or c == 'r' or c == 'u':
                return
            else:
                raise JsonParserException('Invalid JSON input.')
        else:
            return False

    def is_digit(self,c):
        return c >= '0' and c <= '9'
    
    def is_digit_1_9(self, c):
        return c >= '1' and c <= '9'
    
    def is_num(self, c):
        return self.is_digit(c) or c == '-'
    
    def is_seperator(self, c):
        return c == '}' or c == ']' or c == ','

    def is_hex(self, c):
        return (c >= '0' and c <= '9') or (c >= 'a' and c <= 'f') or \
            (c >= 'A' and c <= 'F')

    def is_exp(self, c):
        return c == 'e' or c == 'E'

    def read_str(self):
        _str = ''
        while True:
            self.c = self.__read()
            if self.is_escape(self.c):  # \", \\, \/, \b, \f, \n, \t, \r
                if self.c == 'u':
                    _str += ('\u')
                    for _ in range(4):
                        self.c == self.__read()
                        if self.is_hex(self.c):
                            _str += self.c
                        else:
                            raise JsonParserException('')
                else:
                    _str += ('\\' + self.c)
            elif self.c == '"':
                return Token(TokenType.STRING, _str)
            elif self.c == '\r' or self.c == '\n':
                raise JsonParserException('Invalid JSON input.')
            else:
                _str += self.c

    def read_num(self):
        _num = ''
        c = self.__read()
        if c == '-':
            _num += c
            c = self.__read()
            if c == '0':
                _num += c
                _num = self.append_num(_num)
            elif self.is_digit_1_9(c):
                while self.is_digit(c):
                    _num += c
                    c = self.__read()
                self.__unread()
                _num = self.append_num(_num)
            else:
                raise JsonParserException('- not followed by digit')
        elif c == '0':
            _num += c
            _num = self.append_num(_num)
        elif self.is_digit_1_9(c):
            while self.is_digit(c):
                _num += c
                c = self.__read()
            self.__unread()
            _num = self.append_num(_num)
        return Token(TokenType.NUMBER, _num)
                
    def append_num(self, _num):
        c = self.__read()
        if c == '.':
            _num += c
            _num = self.append_frac(_num)
            if self.is_exp(c):
                _num += c
                _num = self.append_exp(_num)
        elif self.is_exp(c):
            _num += c
            _num = self.append_exp(_num)
        else:
            self.__unread()
        return _num

    def append_frac(self, _str):
        c = self.__read()
        while self.is_digit(c):
            _str += c
            c = self.__read()
        self.__unread()
        return _str
    
    def append_exp(self, _str):
        c = self.__read()
        if c == '+' or c == '-':
            _str += c
            if not self.is_digit(c):
                raise JsonParserException('e+(-) or E+(-) not followed by digit')
            else:
                while self.is_digit(c):
                    _str += c
                    c = self.__read()
                self.__unread()
        elif not self.is_digit(c):
            raise JsonParserException('e+(-) or E+(-) not followed by digit')
        else:
            while self.is_digit(c):
                _str += c
                c = self.__read()
            self.__unread()
        return _str

    def __enter__(self):
        pass


class TokenizerException(Exception):
    pass


class JsonParserException(TokenizerException):
    pass


json_obj = {
    "foo" : 0.123,
    "bar" : "lalalallalala",
    "test" : None,
    "mark" : True,
    "obj" : {
        "attr_1" : 1,
        "attr_2" : "dsfsdf",
        "man" : False,
        "elements" : [
            {"a_1" : 1, "b_1" : 2},
            {"a_3" : 3, "b_4" : 4}
        ]
    }
}
import json
json_str = json.dumps(json_obj)
print json_str

t = Tokenizer(json_str)
ts = t.tokenize()
for e in ts:
    print '%s\t\t%s' % (e.token_type, e.value)