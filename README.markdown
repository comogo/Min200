# README

Interface Python para o modem min200 da Daruma.

Através desta interface é possível:

* Enviar SMS
* Apagar SMS
* Listar todos os SMSs
* Listar SMSs não lidos
* Efetuar uma chamada
* Encerrar a chamada ativa
* Obter nível de sinal

## Requisitos

Segue a lista de requisitos para a biblioteca funcionar corretamente.

* [pySerial](http://pypi.python.org/pypi/pyserial "Download do pySerial")

## Exemplos

### Obter nível de sinal

Obter a porcentagem do nível de sinal atual do modem. Vamos supor que o modem 
esteja conectado na porta *COM1*.

    # coding: -*- coding: utf-8 -*-
    from min200 import Min200E

    if __name__ == '__main__':  
        modem = Min200E(port='COM1', baudrate=115200, debug=True, timeout=0.2)
        modem.open()
        nivel_do_sinal = modem.signal_level()
        print u'O nível atual do modem é de %d%%' % nivel_do_sinal,
        modem.close()

### Enviar SMS

Enviar um SMS com o conteudo 'teste' para o número (044)9999-8888 
utilizando o dispositivo min200e (USB) conectado na porta */dev/ttyUSB1*.

    # coding: -*- coding: utf-8 -*-
    from min200 import Min200E

    if __name__ == '__main__':  
        modem = Min200E(port='/dev/ttyUSB1', baudrate=115200, debug=True, timeout=0.2)
        modem.open()
        modem.send_sms(number='04499998888', message='teste')
        modem.close()

### Apagar SMS

Apagar o SMS com id 5 da memória do SIM utilizando o dispositivo min200e (USB)
conectado na porta *COM1*.
 
    # coding: -*- coding: utf-8 -*-
    from min200 import Min200E

    if __name__ == '__main__':  
        modem = Min200E(port='COM1', baudrate=115200, debug=True, timeout=0.2)
        modem.open()
        modem.delete_sms(5)
        modem.close()
        
### Listar todos os SMSs

Listar todos os SMSs do SIM independente do status da mensagem. Supondo que
o dispositivo min200e esteja conectado na porta */dev/cu.usbserial-A600dXda*.

    # coding: -*- coding: utf-8 -*-
    from min200 import Min200E

    if __name__ == '__main__':  
        modem = Min200E(port='/dev/cu.usbserial-A600dXda', baudrate=115200, debug=True, timeout=0.2)
        modem.open()
        sms_list = modem.get_all_sms()
        print 'Foram lidos', len(sms_list), 'SMSs'
        for sms in sms_list:
            print '[%s]' % sms.source
            print sms.message, '\n'
        modem.close()
        
### Listar todos os SMSs não lidos

Listar todos os SMSs não lidos do SIM com status da mensagem como "Não Lido".
Supondo que o dispositivo min200e esteja conectado na porta *COM2*.

    # coding: -*- coding: utf-8 -*-
    from min200 import Min200E

    if __name__ == '__main__':  
        modem = Min200E(port='COM2', baudrate=115200, debug=True, timeout=0.2)
        modem.open()
        sms_list = modem.get_unread_sms()
        print 'Foram lidos', len(sms_list), 'SMSs'
        for sms in sms_list:
            print '[%s]' % sms.source
            print sms.message, '\n'
        modem.close()
        
### Efetuar uma chamada e encerrar após 10 segundos

Efetuar uma chamada para o número (44) 8888-9999 e encerrar a chamada em 10 
segundos após o telefone de destino atender a ligação. Supondo que o
dispositivo esteja conectado na porta */dev/ttyUSB0*.

    # coding: -*- coding: utf-8 -*-
    from min200 import Min200E
    import time

    if __name__ == '__main__':  
        modem = Min200E(port='/dev/ttyUSB0', baudrate=115200, debug=True, timeout=0.2)
        modem.open()
        modem.call_number('04488889999')
        time.sleep(10)
        modem.end_call()
        modem.close()