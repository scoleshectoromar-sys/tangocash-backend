#!/usr/bin/python
# -*- coding: latin-1 -*-

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import sys, os
from smtplib import SMTP
from ConfigParser import SafeConfigParser


def enviar_mail(conf_mail, motivo, destinatario, mensaje, archivo):
    msg = MIMEMultipart()
    msg['Subject'] = motivo
    msg['From'] = conf_mail['remitente']
    msg['Reply-to'] = conf_mail['remitente']
    msg['To'] = destinatario
    msg.preamble = 'Mensaje de multiples partes.\n'
    
    part = MIMEText(mensaje)
    msg.attach(part)
    
    if archivo:
        part = MIMEApplication(open(archivo,"rb").read())
        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(archivo))
        msg.attach(part)

    print "Enviando email: %s a %s" % (msg['Subject'], msg['To'])
    smtp = SMTP(conf_mail['servidor'])
    if conf_mail['usuario'] and conf_mail['clave']:
        smtp.ehlo()
        smtp.login(conf_mail['usuario'], conf_mail['clave'])
    smtp.sendmail(msg['From'], msg['To'], msg.as_string())

if __name__ == '__main__':
    config = SafeConfigParser()
    config.read("rece.ini")

    if len(sys.argv)<3:
        print "Parámetros: motivo destinatario [mensaje] [archivo]"
        sys.exit(1)

    conf_mail = dict(config.items('MAIL'))
    motivo = sys.argv[1]
    destinatario = sys.argv[2]
    mensaje = len(sys.argv)>3 and sys.argv[3] or conf_mail['cuerpo']
    archivo = len(sys.argv)>4 and sys.argv[4] or None
    
    print "Motivo: ", motivo
    print "Destinatario: ", destinatario
    print "Mensaje: ", mensaje
    print "Archivo: ", archivo
    
    enviar_mail(conf_mail, motivo, destinatario, mensaje, archivo)