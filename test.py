# -*- coding: utf-8 -*-

from min200 import Min200E
import time

if __name__ == '__main__':  
    modem = Min200E(baudrate=115200, debug=True, timeout=0.2)
    modem.open()
    sms_list = modem.get_all_sms()
    print len(sms_list), u'SMS não lidas'
    for sms in sms_list:
        print '[%s] %s' % (sms.source, sms.date.strftime('%d/%m/%Y %H:%M:%S'))
        print sms.message
    modem.close()