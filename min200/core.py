#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import re
import time

class SMS(object):
    def __init__(self, id, status, source, date, message):
        self.id = id
        self.status = status
        self.source = source
        self.date = date
        self.message
        
    def __str__(self):
        return "%d, %s, %s" (self.id, self.status, self.source)
        
   
class Min200E(object):
    OK = '\r\nOK\r\n'
    ERROR = '\r\nERROR\r\n'
    
    def __init__(self, port='/dev/cu.usbserial-A600dXda', timeout=1):
        self.modem = serial.Serial(port=port, timeout=timeout)
        
    def __send_attention(self):
        """
        Envia o comando AT para o modem para verificar se está OK
        """
        self.modem.write('AT\r')
        if not self.check_ok():
            raise Exception(u'Erro ao incializar serviço.')
        
    def __check_return(self, expected=OK, is_regex=False):
        """
        Verifica se o retorno é igual ao esperado.
        """
        ret = ''
        while True:
            ret += self.modem.read(500)
            if ret == '':
                continue
            print ret
            if is_regex:
                pattern = re.compile(expected)
                if len(pattern.findall(ret)) > 0:
                    return True
                else:
                    if self.ERROR in ret:
                        return False
            else:
                if ret == expected:
                    return True
                else:
                    if self.ERROR in ret:
                        return False
            return False
    
    def __read_sms_to_list(self):
        """
        Lê as mensagens do modem e retorna uma lista do objeto SMS.
        """
        pattern = re.compile(r'\+CMGL: (?P<id>\d+),"(?P<status>[A-Z ]+)","(?P<source>[a-zA-z0-9+]+)",.*,"(?P<date>\d{2}/\d{2}/\d{2},\d{2}:\d{2}:\d{2}-\d{2})"\n(?P<message>.*)\n')
        raw_sms_list = self.modem.read(4096)
        print raw_sms_list
        sms = []
        print pattern.search(raw_sms_list)
        for match in pattern.findall(raw_sms_list):
            sms.append(SMS(int(match[0]), match[1], match[2], match[3], match[4]))
        return sms
        
    def check_msg_ok(self):
        """
        Verifica se a mensagem foi enviada com sucesso.
        """
        return self.__check_return(r'\r\n\+CMGS: \d+\r\n\r\nOK\r\n', is_regex=True)
        
    def check_error(self):
        """
        Verifica se retornou uma mensagem de erro.
        """
        ret = self.modem.read(500)
        return ret == self.ERROR
        
    def check_ok(self):
        """
        Verifica se o retorno é um OK
        """
        return self.__check_return(self.OK)
        
    def signal_level(self):
        self.__send_attention()
            
        self.modem.write('AT+CSQ\r')
        return self.modem.read(100)
       
    def send_sms(self, number, message):
        self.__send_attention()
            
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
            
        self.modem.write('AT+CMGS=%s\r\n' % number)
        if not self.__check_return('\r\n> '):
            raise Exception('Erro ao inicializar a mensagem.')
        
        self.modem.write(message + '\x1a\r')
        if not self.check_msg_ok():
            raise Exception('Erro ao enviar a mensagem.')
            
    def call_number(self, number):
        """
        Abre uma chamada para o numero desejado.
        """
        self.__send_attention()
        
        print self.modem.write('ATD%s;\r' % number)
        if not self.check_ok():
            raise Exception('Erro ao fazer chamada.')
            
    def end_call(self):
        """
        Termina a chamada ativa.
        """
        self.__send_attention()
        self.modem.write('ATH\r')
        
        if not self.check_ok():
            raise Exception('Erro ao encerrar a chamada.')
            
    def get_all_sms(self):
        """
        Retorna todas as mensagens.
        """
        self.__send_attention()
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
        self.modem.write('AT+CMGL="ALL"\r')
        
        return self.__read_sms_to_list()
        
    def get_unread_sms(self):
        """
        Retorna o numero de mensagens não lidas.
        """
        self.__send_attention()
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
        self.modem.write('AT+CMGL="REC UNREAD"\r')
        
        return self.__read_sms_to_list()
        
    def delete_sms(self, message_id):
        """
        Apaga a mensagem da memória do SIM card.
        """
        self.__send_attention()
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
        self.modem.write('AT+CMGD=%d\r' % message_id)
        
        
if __name__ == '__main__':  
    modem = Min200E()
    sms_list = modem.get_all_sms()
    print len(sms_list)
    for sms in sms_list:
        print sms
        print sms.message
    modem.modem.close()
    