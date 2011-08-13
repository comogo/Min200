# -*- coding: utf-8 -*-

from min200 import Min200E
import time

if __name__ == '__main__':  
    modem = Min200E()
    modem.open()
    modem.call_number('99838156')
    time.sleep(3)
    modem.end_call()
    modem.close()