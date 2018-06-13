import parse
import dicenumber as dn

import re


if __name__ == '__main__':
    while True:
        try:
            s = input('Script> ')
        except EOFError:
            break

        res, is_dice = parse.parse(436702436368056320, 'Athens', s)
        if res:
            print('\n'.join(res))
