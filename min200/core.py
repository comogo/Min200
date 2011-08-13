#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import re
import datetime

class SMS(object):
    SMS_STATUS_TEXT_UNREAD = "REC UNREAD"
    SMS_STATUS_TEXT_READ = "REC READ"
    SMS_STATUS_TEXT_STORED_UNSENT = "STO UNSENT"
    SMS_STATUS_TEXT_STORED_SENT = "STO SENT"
    SMS_STATUS_TEXT_ALL = "ALL"
    
    SMS_STATUS_PDU_UNREAD = 0
    SMS_STATUS_PDU_READ = 1
    SMS_STATUS_PDU_STORED_UNSENT = 2
    SMS_STATUS_PDU_STORED_SENT = 3
    SMS_STATUS_PDU_ALL = 4
    
    def __init__(self, id, status, source, day, month, year, hour, minute, second, message):
        self.id = int(id)
        self.status = status
        self.source = source
        self.date = datetime.datetime(day=int(day), month=int(month), year=int(year), hour=int(hour), minute=int(minute), second=int(second))
        self.message = message
        
    def __str__(self):
        return "%d, %s, %s" % (self.id, self.status, self.source)
        
   
class Min200E(object):
    """
    Interface para acessar as funcionalidades dos modens min200D, min200E e 
    min300 da Daruma.
    
    Os métodos disponibilizados são:
        open() - Abre a conexão com o modem
        close() - Fecha a conexão com o modem
        signal_level() - Retorna a qualidade do sinal em %
        send_sms(numero, texto) - Envia um SMS para o número especificado
        call_number(numero) - Faz uma ligação para o número especificado
        end_call() - Encerra a chamada ativa
        get_all_sms() - Retorna uma lista com todas as mensagens ma memória
        get_unread_sms() - Retorna uma lista com todas as mensagens não lidas
        delete_sms(sms_id) - Apaga o SMS com o ID específico da memória
    """
    OK = '\r\nOK\r\n'
    ERROR = '\r\nERROR\r\n'
    CMS_ERROR = '\r\n+CMS ERROR\r\n'
    
    def __init__(self, port='/dev/cu.usbserial-A600dXda', timeout=0.25):
        self.timeout = timeout
        self.port = port
        self.modem = None
        
    def open(self):
        """
        Abre a conexão com o modem.
        """
        if self.modem:
            self.modem.close()
        self.modem = serial.Serial(port=self.port, timeout=self.timeout)
    
    def close(self):
        """
        Fecha a conexão com o modem.
        """
        self.modem.close()
        
    def __send_attention(self):
        """
        Envia o comando AT para o modem para verificar se está OK
        """
        self.modem.write('AT\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao incializar serviço.')
    
    def _read_data(self):
        """
        A função bloqueante. A função lê da porta até encontrar dados e chegar
        ao final dos mesmos.
        """
        data = ''
        while True:
            readed = self.modem.read(128)
            if len(readed) == 0 and len(data) > 0:
                break
            data += readed
        return data
                
    def __check_return(self, expected=OK, is_regex=False):
        """
        Verifica se o retorno é igual ao esperado.
        """
        ret = self._read_data()
        if is_regex:
            pattern = re.compile(expected)
            if len(pattern.findall(ret)) > 0:
                return ret
            else:
                if self.ERROR in ret:
                    return None
        else:
            if ret == expected:
                return ret
            else:
                if self.ERROR in ret:
                    return None
        return None
    
    def __read_sms_to_list(self):
        """
        Lê as mensagens do modem e retorna uma lista do objeto SMS.
        """
        raw_sms = self._read_data()        
        if raw_sms == self.ERROR:
            return []
        raw_sms = raw_sms[2:-6] # remove \r\n do início e final da mensagem
        raw_sms_list =  raw_sms.split('\r\n')
        del raw_sms
        
        pattern = re.compile(r'^\+CMGL: (?P<id>\d+),"(?P<status>[A-Z]{3} [A-Z]+)","(?P<source>[+a-zA-Z0-9]+)",,"(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{2}),(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})-\d{2}"$')
        i = 0
        sms_list = []
        while i < len(raw_sms_list):
            sms_header = pattern.search(raw_sms_list[i])
            if sms_header:
                sms_body = raw_sms_list[i+1]
                sms_dict = sms_header.groupdict()
                sms_dict.update({'message': sms_body})
                
                sms_list.append(SMS(**sms_dict))
                i += 2
            else:
                i+= 1

        return sms_list
        
    def check_msg_ok(self):
        """
        Verifica se a mensagem foi enviada com sucesso.
        """
        if self.__check_return(r'\r\n\+CMGS: \d+\r\n\r\nOK\r\n', is_regex=True):
            return True
        return False
        
    def check_error(self):
        """
        Verifica se retornou uma mensagem de erro.
        """
        ret = self._read_data()
        return ret == self.ERROR
        
    def check_ok(self):
        """
        Verifica se o retorno é um OK
        """
        if self.__check_return(self.OK):
            return True
        return False
        
    def signal_level(self):
        """
        Retorna o nível do sinal em porcentagem.
        0 -113 dBm or less
        1 -111 dBm
        2..30 -109... -53 dBm
        31 -51 dBm or greater
        99 not known or not detectable
        """
        self.__send_attention()
        self.modem.write('AT+CSQ\r\n')        
        data = self._read_data()
        data = data.replace(self.OK, '').replace('\r\n', '')
        pattern = re.compile(r'^\+CSQ: (?P<signal>\d+),(?P<errors>\d+)$')
        print data
        match = pattern.search(data)
        if not match:
            raise Exception('Erro ao obter leitura de sinal.')
        match_dict = match.groupdict()
        signal = int(match_dict.get('signal'))
        if signal == 99:
            return 0
        else:
            return ((signal * 100.0) / 31.0)
       
    def send_sms(self, number, message):
        self.__send_attention()
            
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
            
        self.modem.write('AT+CMGS=%s\r\n' % number)
        if not self.__check_return('\r\n> '):
            raise Exception('Erro ao inicializar a mensagem.')
        
        self.modem.write(message + '\x1a\r\n')
        if not self.check_msg_ok():
            raise Exception('Erro ao enviar a mensagem.')
            
    def call_number(self, number):
        """
        Abre uma chamada para o numero desejado.
        """
        self.__send_attention()
        
        print self.modem.write('ATD%s;\r\n' % number)
        if not self.check_ok():
            raise Exception('Erro ao fazer chamada.')
            
    def end_call(self):
        """
        Termina a chamada ativa.
        """
        self.__send_attention()
        self.modem.write('ATH\r\n')
        
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
        self.modem.write('AT+CMGL="ALL"\r\n')
        
        return self.__read_sms_to_list()
        
    def get_unread_sms(self):
        """
        Retorna o numero de mensagens não lidas.
        """
        self.__send_attention()
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
        self.modem.write('AT+CMGL="REC UNREAD"\r\n')
        
        return self.__read_sms_to_list()
        
    def delete_sms(self, message_id):
        """
        Apaga a mensagem da memória do SIM card.
        """
        self.__send_attention()
        self.modem.write('AT+CMGF=1\r\n')
        if not self.check_ok():
            raise Exception(u'Erro ao ativar modo texto.')
        self.modem.write('AT+CMGD=%d\r\n' % message_id)
        data = self._read_data()
        print data
        if data == self.ERROR or data == self.CMS_ERROR:
            raise Exception('Erro ao apagar mensagem')