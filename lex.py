import re
import ply.lex as lex
import numpy.random as nr

reserved = {
    'BOOL': r'([Tt]rue)|([Ff]alse)',
    'PRE': r'[Pp][Rr][Ee]',
    'DICE': r'[dD]',
    'TURN': r'([Tt][Uu][Rr][Nn])|[Tt]',
    'TURNALL': r'([Tt][Uu][Rr][Nn][Aa][Ll][Ll])|[Tt][Aa]',
    'CHOICEHEAD': r'[Cc]',
    'W': r'[Ww]',
    'SWJ': r'[Ss][Ww][Jj]',
    'SWP': r'[Ss][Ww][Pp]',
    'FATECHANGE': r'(([Ff][Aa][Tt][Ee])|[Ff])(([Cc][Hh][Aa][Nn][Gg][Ee])|[Cc])',
    'COC': r'[Cc][Oo][Cc]',
    'LHZ': r'[Ll][Hh][Zz]',
    'MK': r'[Mm][Kk]',
}

# 識別子IDを追加
tokens = [
    'STRING',

    'NUMBER',
    'IDENT',
    #    'CHOICE',

    'LPAREN',
    'RPAREN',

    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',

    'OPEQ',
    'OPNE',
    'OPLT',
    'OPLE',
    'OPGT',
    'OPGE',

    'REGIST',
    'PLUSEQUAL',
    'MINUSEQUAL',
    'PP',
    'MM',

    'COMMA',
    'QUESTION',
    'COLON',
    'AT',
    'DOLLAR',
    'EXCLAMATION',
    'UNDERLINE',
] + list(reserved.keys())

# Token rule by regex
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'

t_OPEQ = r'=='
t_OPNE = r'!='
t_OPLT = r'<'
t_OPLE = r'<='
t_OPGT = r'>'
t_OPGE = r'>='

t_REGIST = r':='
t_PLUSEQUAL = r'\+='
t_MINUSEQUAL = r'-='
t_PP = r'\+\+'
t_MM = r'--'

t_COMMA = r','
t_QUESTION = r'\?'
t_COLON = r':'
t_AT = r'@'
t_DOLLAR = r'\$'
t_EXCLAMATION = r'!'
t_UNDERLINE = r'_'

# Ignored characters
t_ignore = ' \t'
t_ignore_COMMENT = r'\#.*'


# 数値
def t_NUMBER(t):
    r"""\d+"""
    t.value = int(t.value)
    return t


# 文字列
def t_STRING(t):
    r'''([a-zA-Z一-龥ぁ-んァ-ン_]+)|(".+?")'''
    if t.value == '_':
        t.type = 'UNDERLINE'
        return t
    for key, pattern in reserved.items():
        ma = re.fullmatch(pattern, t.value)
        if ma:
            t.type = key
            if key == 'BOOL':
                t.value = (t.value.lower()[0] == 't')
            break
    if t.type == 'STRING' and t.value.startswith('"'):
        t.value = t.value[1:-1]
    return t


# データ登録識別子
def t_IDENT(t):
    r"""\[(!|([0-9a-zA-Z一-龥ぁ-んァ-ン_]+/))?[0-9a-zA-Z一-龥ぁ-んァ-ン_]+\]"""
    t.value = t.value[1:-1].split('/')
    if len(t.value) == 1:
        if t.value[0].startswith('!'):
            t.value[0] = t.value[0][1:]
            t.value.insert(0, '!')
        else:
            t.value.insert(0, '')
    return t


# Count line number
def t_newline(t):
    r"""\n+"""
    t.lexer.lineno += t.value.count("\n")


# Token Parse Error
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(t)


# Build the lexer
lex.lex(debug=0)
