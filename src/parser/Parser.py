#! /usr/bin/python
import sys
sys.path.append('..')

from tokenizer.Tokenizer import Token
from tokenizer.Tokenizer import Tokenizer
from tokenizer.Tokenizer import TokenType
from tokenizer.Tokenizer import JsonParserException

class Parser(object):

    def __init__(self, json_str):
        self.tokens = Tokenizer(json_str).tokenize()
        self.last = None

    def __next(self):
        self.last = self.tokens[0]
        self.tokens.remove(self.last)
        return self.last

    def __top(self):
        return self.tokens[0]

    def parse(self):
        start_token = self.__next()
        if start_token.is_type(TokenType.START_OBJ):
            return self.parse_obj()
        elif start_token.is_type(TokenType.START_ARRAY):
            return self.parse_array()
        else:
            raise JsonParserException("Parse Error!")
    
    def parse_obj(self):
        obj = {}
        token = self.__next()
        if token.is_type(TokenType.END_OBJ):
            return obj
        elif token.is_type(TokenType.STRING):
            obj = self.parse_key(token.value, obj)
        return obj

    def parse_key(self, key, obj):
        token = self.__next()
        if not token.is_type(TokenType.COLON):
            raise JsonParserException('Invalid JSON input.')
        else:
            token = self.__next()
            if token.is_primary():
                obj[key] = token.value
            elif token.is_type(TokenType.START_ARRAY):
                array = self.parse_array()
                obj[key] = array
            elif token.is_type(TokenType.START_OBJ):
                _obj = self.parse_obj()
                obj[key] = _obj
            if self.__top().is_type(TokenType.COMMA):
                _ = self.__next() # consume ,
                if self.__top().is_type(TokenType.STRING):
                    key = self.__next().value
                    obj = self.parse_key(key, obj)
            elif self.__top().is_type(TokenType.END_OBJ):
                _ = self.__next()
                return obj
            else:
                raise JsonParserException('Invalid JSON Parse...')
        return obj

    def parse_array(self):
        array = []
        next = self.__next()
        # nest array
        if next.is_type(TokenType.START_ARRAY):
            nest_array = self.parse_array()
            array.append(nest_array)
            if self.__top().is_type(TokenType.COMMA):
                _ = self.__next() # consume ,
                _ = self.__next()
                array = self.parse_element(array)
        elif next.is_primary():
            array = self.parse_element(array)
        elif next.is_type(TokenType.START_OBJ):
            array.append(self.parse_obj())
            while self.__top().is_type(TokenType.COMMA):
                _ = self.__next() # consume ,
                next = self.__next()
                if next.is_type(TokenType.START_OBJ):
                    array.append(self.parse_obj())
        elif next.is_type(TokenType.END_ARRAY):
            return array
        _ = self.__next()
        return array

    def parse_element(self, array):
        if self.last.is_primary():
            array.append(self.last.value)
        next = self.__next()
        if next.is_type(TokenType.COMMA):
            next = self.__next()
            if next.is_primary():
                array = self.parse_element(array)
            elif next.is_type(TokenType.START_OBJ):
                array.append(self.parse_obj())
            elif next.is_type(TokenType.START_ARRAY):
                array.append(self.parse_array())
            else:
                raise JsonParserException('Invalid JSON input.')
        elif next.is_type(TokenType.END_ARRAY):
            return array
        else:
            raise JsonParserException('Invalid JSON input.')
        return array


if __name__ == '__main__':
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
    parser = Parser(json_str)
    print parser.parse()