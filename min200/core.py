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
        if len(year) == 2:
            year = '20' + year
        self.date = datetime.datetime(day=int(day), month=int(month), year=int(year), hour=int(hour), minute=int(minute), second=int(second))
        self.message = message
        
    def __str__(self):
        return "%d, %s, %s" % (self.id, self.status, self.source)


class Min200Error(Exception):
    """
    Exceção padrão lançada pelo módulo.
    """
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return  repr(self.message)

   
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
    
    def __init__(self, port='/dev/cu.usbserial-A600dXda', baudrate=115200, timeout=0.2, debug=False):
        self.timeout = timeout
        self.port = port
        self.baudrate = baudrate
        self.__modem = None
        self.__debug = debug
    
    def __log(self, message):
        """
        Caso esteja habilitado o modo debug, realiza o log das mensagens.
        """
        if self.__debug:
            print datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'), message
        
    def open(self):
        """
        Abre a conexão com o modem.
        """
        self.__log(u'Abrindo conexão com o modem.')
        if self.__modem:
            self.__modem.close()
        try:
            self.__modem = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        except Exception, e:
            self.__log(u'Erro ao abrir conexão: %s.' % e)
            raise Min200Error(u'Erro ao abrir a conexão com o modem.')
    
    def close(self):
        """
        Fecha a conexão com o modem.
        """
        self.__log(u'Fechando conexão com o modem.')
        self.__modem.close()
        
    def __send_attention(self):
        """
        Envia o comando AT para o modem para verificar se está OK
        """
        self.__log(u'Verificando disponibilidade do modem.')
        self.write_data('AT')
        if not self.check_ok():
            raise Min200Error(u'Erro ao incializar serviço.')
        self.__log(u'Modem disponível.')
    
    def write_data(self, data, append='\r'):
        """
        Envia dados para o modem. Os dados devem ser uma String(str).
        Adiciona o \r\n no final da string, isso pode ser alterado através do
        parâmetro append.
        """
        full_data = data + append
        self.__log("[OUT] '%s'" % repr(full_data))
        self.__modem.write(full_data)
    
    def read_data(self):
        """
        A função bloqueante. A função lê da porta até encontrar dados e chegar
        ao final dos mesmos.
        """
        data = ''
        while True:
            readed = self.__modem.read(128)
            if len(readed) == 0 and len(data) > 0:
                break
            data += readed
        self.__log("[IN] '%s'" % repr(data))
        return data
                
    def __check_return(self, expected=OK, is_regex=False):
        """
        Verifica se o retorno é igual ao esperado.
        """
        ret = self.read_data()
        self.__log('[ASK] %s == %s?' % (repr(ret), repr(expected)))
        if is_regex:
            pattern = re.compile(expected)
            if len(pattern.findall(ret)) > 0:
                self.__log('[ANSWER] SIM (REGEX)')
                return ret
            else:
                if self.ERROR in ret:
                    self.__log(u'[ANSWER] NÃO (ERRO)')
                    return None
        else:
            if ret == expected:
                self.__log(u'[ANSWER] SIM')
                return ret
            else:
                if self.ERROR in ret:
                    self.__log(u'[ANSWER] NÃO (ERRO)')
                    return None
        self.__log(u'[ANSWER] NÃO')
        return None
    
    def __read_sms_to_list(self):
        """
        Lê as mensagens do modem e retorna uma lista do objeto SMS.
        """
        raw_sms = self.read_data()        
        if raw_sms == self.ERROR:
            return []
        raw_sms = raw_sms[2:-6] # remove \r\n do início e final da mensagem
        raw_sms_list =  raw_sms.split('\r\n')
        del raw_sms
        
        pattern = re.compile(r'^\+CMGL: (?P<id>\d+),"(?P<status>[A-Z]{3} [A-Z]+)","(?P<source>[+a-zA-Z0-9]+)",,"(?P<year>\d{2})/(?P<month>\d{2})/(?P<day>\d{2}),(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})[-+]\d{2}"$')
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
        ret = self.read_data()
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
        self.__log(u'Verificando nível de sinal.')
        self.__send_attention()
        self.write_data('AT+CSQ')        
        data = self.read_data()
        data = data.replace(self.OK, '').replace('\r\n', '')
        pattern = re.compile(r'^\+CSQ: (?P<signal>\d+),(?P<errors>\d+)$')

        match = pattern.search(data)
        if not match:
            raise Min200Error('Erro ao obter leitura de sinal.')
        match_dict = match.groupdict()
        signal = int(match_dict.get('signal'))
        if signal == 99:
            return 0
        else:
            return ((signal * 100.0) / 31.0)
       
    def send_sms(self, number, message):
        self.__log(u'Enviando SMS.')
        self.__send_attention()
            
        self.write_data('AT+CMGF=1')
        if not self.check_ok():
            raise Min200Error(u'Erro ao ativar modo texto.')
            
        self.write_data('AT+CMGS=%s' % number)
        if not self.__check_return('\r\n> '):
            raise Min200Error('Erro ao inicializar a mensagem.')
        
        self.write_data(message + '\x1a')
        if not self.check_msg_ok():
            raise Min200Error('Erro ao enviar a mensagem.')
        self.__log(u'SMS enviado com sucesso.')
            
    def call_number(self, number):
        """
        Abre uma chamada para o numero desejado.
        """
        self.__log(u'Efetuando uma chamada.')
        self.__send_attention()
        
        self.write_data('ATD%s;' % number)
        if not self.check_ok():
            raise Min200Error('Erro ao fazer chamada.')
        self.__log(u'Chamada efetuada com sucesso.')
            
    def end_call(self):
        """
        Termina a chamada ativa.
        """
        self.__log(u'Encerrando a chamada ativa.')
        self.__send_attention()
        self.write_data('ATH')
        
        if not self.check_ok():
            raise Min200Error('Erro ao encerrar a chamada.')
        self.__log(u'Chamada ativa encerrada com sucesso.')
            
    def get_all_sms(self):
        """
        Retorna todas as mensagens.
        """
        self.__log(u'Recuperando a lista de todos os SMS.')
        self.__send_attention()
        self.write_data('AT+CMGF=1')
        
        if not self.check_ok():
            raise Min200Error(u'Erro ao ativar modo texto.')
            
        self.write_data('AT+CMGL="ALL"')
        return self.__read_sms_to_list()
        
    def get_unread_sms(self):
        """
        Retorna o número de mensagens não lidas.
        """
        self.__log(u'Recuperando a lista de SMS não lidos.')
        self.__send_attention()
        self.write_data('AT+CMGF=1')
        
        if not self.check_ok():
            raise Min200Error(u'Erro ao ativar modo texto.')

        self.write_data('AT+CMGL')        
        return self.__read_sms_to_list()
        
    def delete_sms(self, message_id):
        """
        Apaga a mensagem da memória do SIM card.
        """
        self.__log(u'Apagando uma mensagem.')
        self.__send_attention()
        self.write_data('AT+CMGF=1')
        
        if not self.check_ok():
            raise Min200Error(u'Erro ao ativar modo texto.')
            
        self.write_data('AT+CMGD=%d' % message_id)
        data = self.read_data()
        
        if data == self.ERROR or data == self.CMS_ERROR:
            raise Min200Error('Erro ao apagar mensagem')
        self.__log(u'Mensagem apagada com sucesso.')