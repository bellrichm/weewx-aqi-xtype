#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

''' 
Test helper/common functions
'''

import random
import string

def random_string(length=32):
    ''' This is a random string with an alpha characater always as the first character. '''
    return random.choice(string.ascii_letters) + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable
