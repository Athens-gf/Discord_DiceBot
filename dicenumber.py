import copy
import numpy
import numpy.random as nr
from enum import Enum
from powertable import sw_power_table as sw_table


class DiceType(Enum):
    """判定種類Enum"""
    Error = -1
    Normal = 0
    SWJ = 1
    SWP = 2
    COC = 3
    LHZ = 4
    MK = 5


class CompOp(Enum):
    """比較用Enum"""
    EQ = 0  # ==
    NE = 1  # !=
    LT = 2  # <
    LE = 3  # <=
    GT = 4  # >
    GE = 5  # >=

    def check(self, val):
        if self == CompOp.EQ:
            return val[0] == val[1]
        elif self == CompOp.NE:
            return val[0] != val[1]
        elif self == CompOp.LT:
            return val[0] < val[1]
        elif self == CompOp.LE:
            return val[0] <= val[1]
        elif self == CompOp.GT:
            return val[0] > val[1]
        elif self == CompOp.GE:
            return val[0] >= val[1]
        return False

    def __str__(self):
        if self == CompOp.EQ:
            return '='
        elif self == CompOp.NE:
            return '≠'
        elif self == CompOp.LT:
            return '<'
        elif self == CompOp.LE:
            return '≦'
        elif self == CompOp.GT:
            return '>'
        elif self == CompOp.GE:
            return '≧'
        return ''


def str_value(val):
    """valをintならそのまま，それ以外なら()に囲んで文字列化して返す"""
    if isinstance(val, int) or isinstance(val, numpy.int64) or isinstance(val, bool):
        return str(val)
    else:
        return '(%s -> %d)' % (str(val), +val)


class Number():
    def __init__(self, type=DiceType.Normal, option={}):
        self.number = []
        self.magni = []
        self.type = type
        self.option = option

    def __str__(self):
        if len(self.number) == 0:
            return '0'
        if len(self.number) == 1:
            return '%s -> %d' % (str(self.number[0]), +self)
        s = ' +'.join([str_value(x) for x in self.number]).replace('+-', '-')
        if not self.is_magni_one():
            s = '(%s)' % s
            for m in self.magni:
                s += (' * %d' if m[0] else ' / %d') % m[1]
        if str(+self) == s:
            return s
        return '%s -> %d' % (s, +self)

    def dice(self):
        return [x for x in self.number if isinstance(x, Dice)]

    def dice_value(self):
        return sum([+x for x in self.dice()])

    def __pos__(self):
        """return value"""
        value = sum([+x for x in self.number])
        for m in self.magni:
            value = value * m[1] if m[0] else value // m[1]
        return value

    def __neg__(self):
        num = copy.deepcopy(self)
        num.number = [-x for x in num.number]
        return num

    def is_magni_one(self):
        return len(self.magni) == 0

    def __mul__(self, other: int):
        num = copy.deepcopy(self)
        if other < 0:
            num = - num
            other *= -1
        if other != 1:
            if num.is_magni_one() or num.magni[-1][0] != True:
                num.magni.append([True, other])
            else:
                num.magni[-1][1] *= other
        return num

    def __truediv__(self, other: int):
        num = copy.deepcopy(self)
        if other < 0:
            num = - num
            other *= -1
        if other != 1:
            if num.is_magni_one():
                num.magni.append([False, other])
            else:
                if num.magni[-1][0] == False:
                    num.magni[-1][1] *= other
                elif num.magni[-1][1] == other:
                    del num.magni[-1]
                elif num.magni[-1][1] % other == 0:
                    num.magni[-1][1] //= other
                elif other % num.magni[-1][1] == 0:
                    m = [False, other // num.magni[-1][1]]
                    del num.magni[-1]
                    num.magni.append(m)
                else:
                    num.magni.append([False, other])
        return num

    def __floordiv__(self, other: int):
        return self.__truediv__(other)

    def _replace_copy(self):
        """新しいNumberを作成し，そのNumberに自身を追加して返す"""
        buff = Number()
        buff.number.append(copy.deepcopy(self))
        return buff

    def __add__(self, other):
        num = copy.deepcopy(self) \
            if self.is_magni_one() else self._replace_copy()
        if isinstance(other, int) and other == 0:
            return num
        numTypes = [type(x) for x in num.number]
        if isinstance(other, Number):
            if num.type != DiceType.Normal and other.type != DiceType.Normal:
                return
            if num.type == DiceType.Normal:
                num.type = other.type
            if other.is_magni_one():
                for n in other.number:
                    num += n
            else:
                num.number.append(other)
        elif type(other) in numTypes:
            index = numTypes.index(type(other))
            num.number[index] += other
        else:
            num.number.append(other)
        return num

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self + -other

    def __rsub__(self, other):
        return self - other

    def __eq__(self, other):
        return CompDice((self, other), CompOp.EQ, self.type, self.option)

    def __ne__(self, other):
        return CompDice((self, other), CompOp.NE, self.type, self.option)

    def __lt__(self, other):
        return CompDice((self, other), CompOp.LT, self.type, self.option)

    def __le__(self, other):
        return CompDice((self, other), CompOp.LE, self.type, self.option)

    def __gt__(self, other):
        return CompDice((self, other), CompOp.GT, self.type, self.option)

    def __ge__(self, other):
        return CompDice((self, other), CompOp.GE, self.type, self.option)


class Dice():
    def __init__(self, dice=(), type=DiceType.Normal, option={}):
        """dice = (n, m)"""
        self.type = type
        self.option = option

        self.dices = {}     # ダイス
        if len(dice) == 2:
            n = dice[0]
            m = dice[1]
            l = []
            if m == 66:
                l = [(nr.randint(1, 7) * 10 + nr.randint(1, 7))
                     for __ in range(n)]
            else:
                l = list(nr.randint(1, 1 + m, n))
            self.dices[m] = [True, l]

    def __pos__(self):
        """return value"""
        if self.type != DiceType.MK:
            return sum([sum(v) * (1 if op else -1)
                        for [op, v] in self.dices.values()])
        l6 = sorted(self.dices[6][1], reverse=True)
        if len(l6) > 2:
            l6 = l6[:2] * (1 if self.dices[6][0] else -1)
        value = sum([+x for x in l6]) + sum([sum(v) * (1 if op else -1)
                                             for d, [op, v] in self.dices.items() if d != 6])

        return value

    def __neg__(self):
        d = copy.deepcopy(self)
        for dice, [op, __] in d.dices.items():
            d.dices[dice][0] = not op
        return d

    def __str__(self):
        if len(self.dices) == 0:
            return '0'
        s = ''
        for dice, [op, vals] in self.dices.items():
            sumval = sum(vals)
            if self.type == DiceType.MK and dice == 6:
                vals = sorted(vals, reverse=True)
                if len(vals) > 2:
                    sumval = sum(vals[:2])
            str_d = '%s%d(%dD%d%s)' % ('+' if op else '-',
                                       sumval, len(vals), dice, str(vals))
            s += str_d.replace('+', '') if(s == '') else(' ' + str_d)
        return s

    def __add__(self, other):
        d = copy.deepcopy(self)
        if isinstance(other, Dice):
            for dice, [op, val] in other.dices.items():
                if dice in d.dices:
                    if d.dices[dice][0] == op:
                        d.dices[dice][1] += val
                    elif len(d.dices[dice][1]) == len(val):
                        if self.type == DiceType.LHZ:
                            d.dices[dice][1] = d.dices[dice][1][0:1]
                        else:
                            del d.dices[dice]
                    elif len(d.dices[dice][1]) > len(val):
                        d.dices[dice][1] = d.dices[dice][1][0:
                                                            len(d.dices[dice][1]) - len(val)]
                    else:
                        print(self.type)
                        if self.type == DiceType.LHZ:
                            d.dices[dice][1] = d.dices[dice][1][0:1]
                        else:
                            d.dices[dice][0] = not d.dices[dice][0]
                            d.dices[dice][1] = d.dices[dice][1][0:
                                                                len(val) - len(d.dices[dice][1])]
                else:
                    d.dices[dice] = [op, val]
            return d
        else:
            return Number(d.type, d.option) + d + other

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self + -other

    def __rsub__(self, other):
        return self - other

    def __mul__(self, other: int):
        d = copy.deepcopy(self)
        for dice in d.dices.keys():
            d.dices[dice][1] *= other
        return d

    def __truediv__(self, other: int):
        return (Number() + copy.deepcopy(self)) / other

    def __floordiv__(self, other: int):
        return self.__truediv__(other)

    def _comp(self, other, op):
        return CompDice(((Number() + copy.deepcopy(self)), other), op, self.type, self.option)

    def __eq__(self, other):
        return self._comp(other, CompOp.EQ)

    def __ne__(self, other):
        return self._comp(other, CompOp.NE)

    def __lt__(self, other):
        return self._comp(other, CompOp.LT)

    def __le__(self, other):
        return self._comp(other, CompOp.LE)

    def __gt__(self, other):
        return self._comp(other, CompOp.GT)

    def __ge__(self, other):
        return self._comp(other, CompOp.GE)


class CompDice():
    def __init__(self, obj, op: CompOp, type=DiceType.Normal, option={}):
        self.obj = obj
        self.op = op
        self.type = type
        self.option = option

    def __bool__(self):
        return self.op.check([+o for o in self.obj])

    def str_pre(self):
        s = ''
        if isinstance(self.obj[0], int):
            s += str(self.obj[0])
        else:
            s += '(%s)' % str(self.obj[0])
        s += ' %s ' % str(self.op)
        if isinstance(self.obj[1], int):
            s += str(self.obj[1])
        else:
            s += '(%s)' % str(self.obj[1])
        return s

    def __str__(self):
        s = self.str_pre() + ' -> '
        if self.type == DiceType.COC:
            val = [+o for o in self.obj]
            if val[0] <= self.option['C']:
                s += 'クリティカル！'
            elif val[0] <= val[1] / 5:
                s += 'スペシャル！'
            elif val[0] >= 101 - self.option['F']:
                s += 'ファンブル！'
            else:
                s += '成功' if self.__bool__() else '失敗'
        elif self.type == DiceType.SWJ:
            if self.obj[0].is_transcendence and self.obj[0].value() >= 41:
                s += '超成功！'
            elif self.obj[0].dice_value() >= 12:
                s += '自動的成功！'
            elif self.obj[0].dice_value() <= 2:
                s += '自動的失敗！'
            else:
                s += '成功' if self.__bool__() else '失敗'
        elif self.type == DiceType.LHZ:
            dice6 = self.obj[0].dice()[0].dices[6][1]
            if sum([x >= 6 for x in dice6]) >= 2:
                s += 'クリティカル！'
            elif sum([x <= 1 for x in dice6]) == len(dice6):
                s += 'ファンブル！'
            else:
                s += '成功' if self.__bool__() else '失敗'
        elif self.type == DiceType.MK:
            dice6 = sorted(self.obj[0].dice()[0].dices[6][1], reverse=True)
            if len(dice6) > 2:
                dice6 = dice6[:2]
            if sum(dice6) >= 12:
                s += '絶対成功！'
            elif len(dice6) == 2 and sum(dice6) == 2:
                s += '絶対失敗！'
            else:
                s += '成功' if self.__bool__() else '失敗'
        else:
            s += '成功' if self.__bool__() else '失敗'
        return s

    def fate_change(self, corre):
        if self.type == DiceType.SWJ:
            [s for s in self.obj if isinstance(s, SWJ)][0].fate_change(corre)
            return self


class SWJ(Number):
    def __init__(self, option):
        super().__init__(DiceType.SWJ)
        dn = Dice((2, 6), DiceType.SWJ)
        if '$' in option:
            self.fix = option['$']
            dn.dices[6][1][1] = self.fix
        self.number.append(dn)
        self.crit = max(option['@'], 3)
        self.is_transcendence = False
        if +self >= self.crit:
            self.is_transcendence = True
            while True:
                dn = Dice((2, 6), DiceType.SWJ)
                self.number.append(dn)
                if +dn < self.crit:
                    break

    def fate_change(self, corre):
        last_id = [i for i in range(len(self.number))
                   if isinstance(self.number[i], Dice)][-1]
        l = self.number[last_id].dices[6][1]
        self.number[last_id].dices[6][1] = \
            [7 - s for s in l[0:2]]
        if len(l) > 2:
            print(l[0:2])
            print(l[2:])
            self.number[last_id].dices[6][1].extend(l[2:])
        return self + corre


class SWP():
    def __init__(self, option):
        self.power = min(max(+option['Base'], 0), 100)
        self.critical = min(max(+option['@'], 3), 13) \
            if '@' in option else 10
        self.option = option
        self.result = []
        p = self.power
        while True:
            b = list(nr.randint(1, 7, 2))
            if len(self.result) == 0:
                if option['W']:
                    b = [nr.randint(1, 7)] * 2
                if '$' in option:
                    b = [nr.randint(1, 7)]
                    b.append(+option['$'])
                if '$+' in option:
                    b.append(+option['$+'])
            s = min(max(sum(b), 2), 12)
            self.result.append([sw_table[p][s - 2], s, b])
            if self.result[-1][1] < self.critical:
                break
            if '!' in option:
                p = max(min(p + option['!'], 100), 0)

    def __pos__(self):
        return sum([re[0] for re in self.result])

    def __str__(self):
        sp = str_value(self.power)
        sc = str_value(self.critical)
        sr = ''
        for re in self.result:
            if sr != '':
                sr += ' Crit! + '
            sr += '%d(%d%s)' % (re[0], re[1], str(re[2]))
        if len(self.result) != 1:
            sr = '((%s) -> %d回転)' % (sr, len(self.result) - 1)
        return 'SWP%s @%s -> %s' % (sp, sc, sr)

    def __add__(self, other):
        return Number() + copy.deepcopy(self) + other

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self + -other

    def __rsub__(self, other):
        return self - other

    def __mul__(self, other: int):
        return (Number() + copy.deepcopy(self)) * other

    def __truediv__(self, other: int):
        return (Number() + copy.deepcopy(self)) / other

    def __floordiv__(self, other: int):
        return (Number() + copy.deepcopy(self)) // other

    def fate_change(self, corre):
        p = self.power
        if '!' in self.option:
            p = min(p + self.option['!'] * (len(self.result) - 1), 100)
        cor = self.result[-1][2][2:]
        self.result[-1][2] = [7 - s for s in self.result[-1][2][0:2]]
        self.result[-1][2].extend(cor)
        self.result[-1][2].append(corre)
        self.result[-1][1] = min(max(sum(self.result[-1][2]), 2), 12)
        self.result[-1][0] = sw_table[p][self.result[-1][1] - 2]
        while True:
            if self.result[-1][1] < self.critical:
                break
            if '!' in self.option:
                p = min(p + self.option['!'], 100)
            b = list(nr.randint(1, 7, 2))
            s = min(max(sum(b), 2), 12)
            self.result.append([sw_table[p][s - 2], s, b])
        return self


class COC(Number):
    def __init__(self, option):
        dic = {'C': +option['Base']}
        dic['F'] = +option['_'] if '_' in option else dic['C']
        dic['C'] = max(1, min(50, dic['C']))
        dic['F'] = max(1, min(50, dic['F']))
        super().__init__(DiceType.COC, dic)
        self.number.append(Dice((1, 100), DiceType.COC))


class LHZ(Number):
    def __init__(self):
        super().__init__(DiceType.LHZ)
        self.number.append(Dice((2, 6), DiceType.LHZ))


class MK(Number):
    def __init__(self):
        super().__init__(DiceType.MK)
        self.number.append(Dice((2, 6), DiceType.MK))
