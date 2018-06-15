import re
import lex
import math
import copy
import ply.yacc as yacc
import dicenumber as dn
import numpy.random as nr

# Import tokens
from lex import tokens


# Precedence rules for the arithmetic operators
precedence = (
    ('left', 'QUESTION', 'COLON'),
    ('left', 'OPEQ', 'OPNE', 'OPLT', 'OPLE', 'OPGT', 'OPGE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UPLUS', 'UMINUS'),
    ('left', 'DICE', 'SWJ', 'SWP', 'COC', 'LHZ', 'MK'),
    ('left', 'COMMA', 'AT', 'DOLLAR', 'EXCLAMATION', 'UNDERLINE', 'W'),
)


# data { serverID : { name : { VALUE : { key : value}, COMMAND : { key : command}, TURN : { key : Value} } } }
data = {}
ALL = '!All'
SETD = 'Set_D'
VALUE = 'Value'
COMMAND = 'Command'
TURN = 'Turn'
PRE = 'PreData'

# mes_buffer{ IS_USING : False, SERVER : serverID, NAME : '', OUT : [] }
# 現在パース中かどうか
IS_USING = 'Is_Using'
# 現在パース中かどうか
IS_CHOICE = 'Is_Choice'
# パースが成功したがどうか
IS_SUCCESS = 'Is_Success'
# ダイスを振ったかどうか
IS_DICE = 'Is_Dice'
# 現在の対象サーバーID
SERVER = 'Server'
# 発言者名
NAME = 'Name'
# 出力
OUT = 'Out'
mes_buff = {IS_USING: False}


def get_buff_data():
    return mes_buff[SERVER], mes_buff[NAME], mes_buff[OUT]


def setup_data(keys, init):
    buff = data
    for key in keys[:-1]:
        if key not in buff:
            buff[key] = {}
        buff = buff[key]
    buff[keys[-1]] = init


def is_exist_keys_in_data(keys):
    buff = data
    for key in keys:
        if key not in buff:
            return False
        buff = buff[key]
    return True


def reset_data(key, name, type_):
    server, _, _ = get_buff_data()
    setup_data((server, name, type_, key), 0)
    del data[server][name][type_][key]


def regist_data(tup):
    ident, value, type_ = tup
    server, name, out = get_buff_data()
    if ident[0] == '!':
        name = ALL
    elif ident[0] != '':
        name = ident[0]
    key = ident[1]
    reset_data(key, name, type_)
    val = +value
    data[server][name][type_][key] = val
    if name == ALL:
        out.append(u'Regist %s : [!%s] <- %s' %
                   (type_, key, dn.str_value(value)))
    else:
        out.append(u'Regist %s : [%s/%s] <- %s' %
                   (type_, name, key, dn.str_value(value)))


def get_data(ident, type_):
    server, name, _ = get_buff_data()
    if ident[0] != '':
        name = ident[0]
    key = ident[1]
    if is_exist_keys_in_data((server, name, type_, key)):
        return data[server][name][type_][key]
    if is_exist_keys_in_data((server, ALL, type_, key)):
        return data[server][ALL][type_][key]


# 数値登録
def p_statement_regist_value(p):
    """statement : IDENT REGIST expression"""
    p[0] = ('regist', p[1], p[3], VALUE)


# 数値加減算
def p_statement_change_value(p):
    """statement : IDENT PLUSEQUAL expression
                 | IDENT MINUSEQUAL expression
                 | IDENT PP
                 | IDENT MM"""
    server, name, out = get_buff_data()
    if p[1][0] == '!':
        name = ALL
    elif p[1][0] != '':
        name = p[1][0]
    key = p[1][1]
    if is_exist_keys_in_data((server, name, VALUE, key)):
        val = 1 if len(p) == 3 else p[3]
        pre_val = data[server][name][VALUE][key]
        op = ''
        if(p[2] == '+=') or (p[2] == '++'):
            data[server][name][VALUE][key] += +val
            op = '+'
        elif(p[2] == '-=') or (p[2] == '--'):
            data[server][name][VALUE][key] -= +val
            op = '-'
        if name == ALL:
            out.append('Value : [!%s] <- (%d %s %s -> %d)' %
                       (key, pre_val, op, dn.str_value(val), data[server][name][VALUE][key]))
        else:
            out.append('Value : [%s/%s] <- (%d %s %s -> %d)' %
                       (name, key, pre_val, op, dn.str_value(val), data[server][name][VALUE][key]))


# 数値取得
def p_expression_get_value(p):
    """expression : IDENT"""
    p[0] = get_data(p[1], VALUE)


# ターンカウント登録
def p_statement_regist_turn(p):
    """statement : TURN IDENT REGIST expression"""
    p[0] = ('regist', p[2], p[4], TURN)


def update_turn(is_all):
    server, name, out = get_buff_data()
    if is_all:
        name = ALL
    if is_exist_keys_in_data((server, name, TURN)):
        dic = data[server][name][TURN]
        if len(dic.keys()) == 0:
            return
        out.append("Turn update: ")
        del_keys = []
        for k in dic.keys():
            dic[k] -= 1
            if is_all:
                if dic[k] > 0:
                    out.append("  [!%s]: %d" % (k, dic[k]))
                else:
                    out.append("  [!%s]: Finish" % k)
                    del_keys.append(k)
            else:
                if dic[k] > 0:
                    out.append("  [%s/%s]: %d" % (name, k, dic[k]))
                else:
                    out.append("  [%s/%s]: Finish" % (name, k))
                    del_keys.append(k)
        for k in del_keys:
            del dic[k]


# ターン更新
def p_statement_update_turn(p):
    """statement : TURN"""
    p[0] = ('update turn', False)


def p_statement_update_turn_all(p):
    """statement : TURNALL"""
    p[0] = ('update turn', True)


# ターンカウント数取得
def p_expression_get_turn(p):
    """expression : TURN IDENT"""
    p[0] = get_data(p[2], TURN)
    if p[0] == None:
        p[0] = 0


# 四則演算
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression """
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        if p[3] == '0':
            p[0] = 'ZeroDivision'
        else:
            p[0] = p[1] // p[3]


# 0除算
def p_expression_zero_division(p):
    """statement : expression DIVIDE '0'"""
    p[0] = 'ZeroDivision'


# 比較演算
def p_expression_comp(p):
    """expression : expression OPEQ expression
                  | expression OPNE expression
                  | expression OPLT expression
                  | expression OPLE expression
                  | expression OPGT expression
                  | expression OPGE expression """
    if re.fullmatch(lex.t_OPEQ, p[2]):
        p[0] = p[1] == p[3]
    elif re.fullmatch(lex.t_OPNE, p[2]):
        p[0] = p[1] != p[3]
    elif re.fullmatch(lex.t_OPLT, p[2]):
        p[0] = p[1] < p[3]
    elif re.fullmatch(lex.t_OPLE, p[2]):
        p[0] = p[1] <= p[3]
    elif re.fullmatch(lex.t_OPGT, p[2]):
        p[0] = p[1] > p[3]
    elif re.fullmatch(lex.t_OPGE, p[2]):
        p[0] = p[1] >= p[3]


def p_expression_comp_list(p):
    """expression : expression OPEQ list
                  | expression OPNE list
                  | expression OPLT list
                  | expression OPLE list
                  | expression OPGT list
                  | expression OPGE list """
    l = ['comps']
    for val in p[3]:
        if re.fullmatch(lex.t_OPEQ, p[2]):
            l.append(p[1] == val)
        elif re.fullmatch(lex.t_OPNE, p[2]):
            l.append(p[1] != val)
        elif re.fullmatch(lex.t_OPLT, p[2]):
            l.append(p[1] < val)
        elif re.fullmatch(lex.t_OPLE, p[2]):
            l.append(p[1] <= val)
        elif re.fullmatch(lex.t_OPGT, p[2]):
            l.append(p[1] > val)
        elif re.fullmatch(lex.t_OPGE, p[2]):
            l.append(p[1] >= val)
    p[0] = tuple(l)


# +-から始まる
def p_expression_upm(p):
    """expression : PLUS expression %prec UPLUS
                  | MINUS expression %prec UMINUS """
    p[0] = +p[2] if p[1] == '+' else -p[2]


# ()
def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""
    p[0] = p[2]


# リスト
def p_list_element(p):
    """list_element : expression COMMA expression"""
    p[0] = [p[1], p[3]]


def p_list_element_append(p):
    """list_element : list_element COMMA expression"""
    p[0] = p[1]
    p[0].append(p[3])


def p_list_element_extend(p):
    """list_element : list_element COMMA list_element"""
    p[0] = p[1]
    p[0].extend(p[3])


def p_list(p):
    """list : LPAREN list_element RPAREN"""
    p[0] = p[2]


# 三項演算子
def p_expression_conditional_op(p):
    """expression : expression QUESTION expression COLON expression"""
    if p[1].__bool__():
        p[0] = p[3]
    else:
        p[0] = p[5]


# 文字列
def p_expression_string(p):
    """expression : STRING"""
    p[0] = p[1]


# 数値
def p_expression_number(p):
    """expression : NUMBER"""
    p[0] = p[1]


# bool値
def p_expression_bool(p):
    """expression : BOOL"""
    p[0] = p[1]


# 直前のデータ
def p_expression_pre(p):
    """expression : PRE"""
    server = mes_buff[SERVER]
    if is_exist_keys_in_data((server, PRE)):
        p[0] = data[server][PRE]
        if (not isinstance(p[0], bool)) and (not isinstance(p[0], dn.CompDice)):
            p[0] = +p[0]


# チョイス
def p_statement_choice(p):
    """statement : CHOICEHEAD list"""
    mes_buff[IS_CHOICE] = True
    p[0] = p[2][nr.randint(0, len(p[2]))]
    if isinstance(p[0], str):
        p[0] = p[0].strip()


# ダイス系：nDm,nBm,D66
def p_expression_dice_nm(p):
    """expression : expression DICE expression"""
    mes_buff[IS_DICE] = True
    p[0] = dn.Dice((p[1], p[3]))


def p_expression_dice_m(p):
    """expression : DICE expression"""
    mes_buff[IS_DICE] = True
    p[0] = dn.Dice((1, p[2]))


def p_expression_dice_n(p):
    """expression : expression DICE"""
    mes_buff[IS_DICE] = True
    p[0] = dn.Dice((p[1], 6))


def p_expression_dice(p):
    """expression : DICE"""
    mes_buff[IS_DICE] = True
    p[0] = dn.Dice((1, 6))


def get_symbol_dict(p0, p1, symbol):
    if isinstance(p0, dict):
        dic = copy.deepcopy(p0)
        dic[symbol] = p1
        return dic
    else:
        return {'Base': p0, symbol: p1}


def p_expression_symbol(p):
    """expression : expression AT expression
                  | expression DOLLAR expression
                  | expression EXCLAMATION expression
                  | expression UNDERLINE expression """
    p[0] = get_symbol_dict(p[1], p[3], p[2])


def p_expression_dollar_plus(p):
    """expression : expression DOLLAR PLUS expression"""
    p[0] = get_symbol_dict(p[1], p[4], '$+')


# SW2.0系
def p_expression_sw_judge(p):
    """expression : SWJ"""
    mes_buff[IS_DICE] = True
    p[0] = dn.SWJ({'@': 13})


# SW2.0 片側固定
def p_expression_sw_judge_fix(p):
    """expression : SWJ DOLLAR expression"""
    mes_buff[IS_DICE] = True
    p[0] = dn.SWJ({'@': 13, '$': p[3]})


# SW2.0 超越判定
def p_expression_sw_judge_crit(p):
    """expression : SWJ AT expression"""
    mes_buff[IS_DICE] = True
    p[0] = dn.SWJ({'@': p[3]})


# SW2.0 威力表
def p_expression_sw_power(p):
    """expression : SWP expression
                  | SWP expression W"""
    mes_buff[IS_DICE] = True
    dic = copy.deepcopy(p[2]) if isinstance(p[2], dict) else{'Base': p[2]}
    dic['W'] = (len(p) == 4)
    p[0] = dn.SWP(dic)


# 運命変転
def p_statement_fate_change(p):
    """statement : FATECHANGE
                 | FATECHANGE expression"""
    mes_buff[IS_DICE] = True
    server, name, _ = get_buff_data()
    if is_exist_keys_in_data((server, name, PRE)):
        pre_data = data[server][name][PRE]
        if isinstance(pre_data, dn.SWJ) or isinstance(pre_data, dn.SWP) or isinstance(pre_data, dn.CompDice):
            mes_buff[OUT].append('運命変転！')
            p[0] = pre_data.fate_change(0 if len(p) == 2 else p[2])


# CoC系
def p_expression_coc(p):
    """expression : COC
                  | COC expression
                  | COC list
                  | COC expression UNDERLINE list"""
    mes_buff[IS_DICE] = True
    if len(p) == 2:
        p[0] = dn.COC({'Base': 1})
    elif len(p) == 3:
        if isinstance(p[2], list) and len(p[2]) == 2:
            p[0] = dn.COC({'Base': 1}) <= 50 + 5 * (p[2][0] - p[2][1])
        elif isinstance(p[2], dict):
            p[0] = dn.COC(copy.deepcopy(p[2]))
        else:
            p[0] = dn.COC({'Base': p[2]})
    elif len(p) == 5:
        if (isinstance(p[2], int) or isinstance(p[2], dict))and isinstance(p[4], list) and len(p[4]) == 2:
            dic = copy.deepcopy(p[2]) if isinstance(
                p[2], dict) else{'Base': p[2]}
            p[0] = dn.COC(dic) <= 50 + 5 * (p[4][0] - p[4][1])


# LHZ系
def p_expression_lhz(p):
    """expression : LHZ"""
    p[0] = dn.LHZ()


# まよきん系
def p_expression_mk(p):
    """expression : MK"""
    mes_buff[IS_DICE] = True
    p[0] = dn.MK()


def p_statement_expr(p):
    """statement : expression"""
    if not isinstance(p[1], str) or mes_buff[IS_CHOICE]:
        p[0] = p[1]


# エラー例外
def p_error(p):
    print("syntax error")
    print(p)
    mes_buff[IS_SUCCESS] = False


parser = yacc.yacc()

# コマンド登録正規表現
re_regist_command = re.compile(
    r'^\s*\{\s*(?:(?P<all>!)|(?:(?P<name>[0-9a-zA-Z一-龥ぁ-んァ-ン_]+)\s*/))?\s*(?P<key>[0-9a-zA-Z一-龥ぁ-んァ-ン_]+)\s*\}\s*:=\s*(?P<com>.+)\s*')


def regist_command(line):
    """コマンド登録であればコマンドを登録しTrueを返す，そうでなければFalseを返す"""
    m = re_regist_command.fullmatch(line)
    if m:
        server, name, out = get_buff_data()
        if m.group('all'):
            name = ALL
        elif m.group('name'):
            name = m.group('name')
        key = m.group('key')
        com = m.group('com')
        reset_data(key, name, COMMAND)
        data[server][name][COMMAND][key] = com
        if name == ALL:
            out.append(u'Regist Command: {!%s} <- %s' % (key, com))
        else:
            out.append(u'Regist Command: {%s/%s} <- %s' % (name, key, com))
        return True
    return False


# コマンド正規表現
re_split_command = re.compile(
    r'(\{\s*(?:[0-9a-zA-Z一-龥ぁ-んァ-ン_]+\s*/)?\s*[0-9a-zA-Z一-龥ぁ-んァ-ン_]+\s*\})')
re_command = re.compile(
    r'^\{\s*(?:(?P<all>!)|(?:(?P<name>[0-9a-zA-Z一-龥ぁ-んァ-ン_]+)\s*/))?\s*(?P<key>[0-9a-zA-Z一-龥ぁ-んァ-ン_]+)\s*\}')


def replace_command(line):
    """コマンドで入力文字列を置き換える"""
    replace = ''
    server, user_name, _ = get_buff_data()
    for spl in re_split_command.split(line):
        m = re_command.fullmatch(spl)
        if m:
            name = user_name
            if m.group('all'):
                name = ALL
            elif m.group('name'):
                name = m.group('name')
            key = m.group('key')
            if is_exist_keys_in_data((server, name, COMMAND, key)):
                replace += data[server][name][COMMAND][key]
            elif is_exist_keys_in_data((server, ALL, COMMAND, key)):
                replace += data[server][ALL][COMMAND][key]
            else:
                replace += spl
        else:
            replace += spl
    return replace


def parse(serverID, name, input, debug=0):
    # 別のサーバーで使用中ならば待機
    while(mes_buff[IS_USING]):
        pass
    # バッファー初期化
    mes_buff[IS_DICE] = False
    mes_buff[IS_USING] = True
    mes_buff[IS_SUCCESS] = True
    mes_buff[SERVER] = serverID
    mes_buff[NAME] = name
    mes_buff[OUT] = []
    # パース処理
    # 改行で分割
    lines = input.split('\n')
    for line in lines:
        line = line.strip()
        if(line == '') or regist_command(line):
            continue
        rep_line = line
        for ___ in range(20):
            pre_rep_line = rep_line
            rep_line = replace_command(rep_line)
            if pre_rep_line == rep_line:
                break
        try:
            mes_buff[IS_CHOICE] = False
            result = yacc.parse(rep_line, debug=debug)
            if not mes_buff[IS_SUCCESS]:
                mes_buff[IS_USING] = False
                return None, False
            if(isinstance(result, bool) or isinstance(result, dn.CompDice) or result or result == 0) and \
                    not isinstance(result, dict):
                if isinstance(result, tuple):
                    if result[0] == 'regist':
                        regist_data(result[1:])
                    elif result[0] == 'update turn':
                        update_turn(result[1])
                    elif result[0] == 'comps':
                        mes_buff[OUT].append('%s -> ' % line)
                        count = 0
                        for comp in result[1:]:
                            mes_buff[OUT].append(str(comp))
                            if comp.__bool__():
                                count += 1
                        if count == 0:
                            mes_buff[OUT].append('全失敗')
                        elif count == len(result) - 1:
                            mes_buff[OUT].append('全成功')
                        setup_data((serverID, name, PRE), result[-1])
                        setup_data((serverID, PRE), result[-1])
                else:
                    setup_data((serverID, name, PRE), result)
                    setup_data((serverID, PRE), result)
                    if line == rep_line:
                        mes_buff[OUT].append('%s -> %s' % (line, str(result)))
                    else:
                        mes_buff[OUT].append('%s -> %s -> %s' %
                                             (line, rep_line, str(result)))
        except:
            mes_buff[IS_USING] = False
            return None, False
    mes_buff[IS_USING] = False
    return mes_buff[OUT], mes_buff[IS_DICE]


def delete_server(serverID):
    if serverID in data:
        del data[serverID]


def delete_regist_name(serverID, name):
    if (serverID in data) and(name in data[serverID]):
        del data[serverID][name]
        return True
    return False


def delete_regist_valcom(serverID, name, valcom):
    is_turn = valcom.lower().startswith('t')
    if is_turn:
        valcom = valcom[1:]
    s = valcom[1:-1].split('/')
    if len(s) == 1:
        if s[0].startswith('!'):
            s[0] = s[0][1:]
            s.insert(0, ALL)
        else:
            s.insert(0, name)
    if(serverID in data) and (s[0] in data[serverID]):
        if is_turn:
            if (valcom[0] == '[')and(valcom[-1] == ']')and (TURN in data[serverID][s[0]])and (s[1] in data[serverID][s[0]][TURN]):
                del data[serverID][s[0]][TURN][s[1]]
                return True
        else:
            if (valcom[0] == '[')and(valcom[-1] == ']')and (VALUE in data[serverID][s[0]])and (s[1] in data[serverID][s[0]][VALUE]):
                del data[serverID][s[0]][VALUE][s[1]]
                return True
            if (valcom[0] == '{')and(valcom[-1] == '}')and (COMMAND in data[serverID][s[0]])and (s[1] in data[serverID][s[0]][COMMAND]):
                del data[serverID][s[0]][COMMAND][s[1]]
                return True
    return False


def get_regist(serverID, name):
    if(serverID in data) and (name in data[serverID]):
        s = ''
        for t in (VALUE, COMMAND, TURN):
            if t not in data[serverID][name]:
                continue
            for k, v in data[serverID][name][t].items():
                if t == VALUE:
                    s += '[%s/%s] := %d\n' % (name, k, v)
                elif t == COMMAND:
                    s += '{%s/%s} := %s\n' % (name, k, v)
                elif t == TURN:
                    s += 'T[%s/%s] := %d\n' % (name, k, v)
        return s


def get_all_regist(serverID):
    if serverID in data:
        s = ''
        if ALL in data[serverID]:
            s += ' All\n'
            for t in (VALUE, COMMAND, TURN):
                if t not in data[serverID][ALL]:
                    continue
                for k, v in data[serverID][ALL][t].items():
                    if t == VALUE:
                        s += '[!%s] := %d\n' % (k, v)
                    elif t == COMMAND:
                        s += '{!%s} := %s\n' % (k, v)
                    elif t == TURN:
                        s += 'T[!%s] := %d\n' % (k, v)
            s += '\n'
        for name, val in data[serverID].items():
            if name == ALL or name == SETD or name == PRE:
                continue
            if (VALUE not in val) and (COMMAND not in val) and (TURN not in val):
                continue
            s += ' Name: %s\n' % name
            for t in (VALUE, COMMAND, TURN):
                if t not in val:
                    continue
                for k, v in val[t].items():
                    if t == VALUE:
                        s += '[%s/%s] := %d\n' % (name, k, v)
                    elif t == COMMAND:
                        s += '{%s/%s} := %s\n' % (name, k, v)
                    elif t == TURN:
                        s += 'T[%s/%s] := %d\n' % (name, k, v)
            s += '\n'
        return s


def set_d(serverID, flag):
    if serverID not in data:
        data[serverID] = {}
    data[serverID][SETD] = flag


def get_d(serverID):
    if (serverID not in data)or(SETD not in data[serverID]):
        return False
    return data[serverID][SETD]


def is_one_access_server():
    return len(data.keys()) <= 1
