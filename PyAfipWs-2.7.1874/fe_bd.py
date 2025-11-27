#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo de Intefase Factura Electrónica por base de datos"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.49b"

from decimal import Decimal
import os
import sys
import time
import traceback
import random
from ConfigParser import SafeConfigParser
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib

# revisar la instalación de pyafip.ws:
import wsaa, wsfe, wsfex, wsfev1, wsfexv1, wsmtx
from php import SimpleXMLElement, SoapClient, SoapFault, date
try:
    from fpdf import Template
except:
    pass

HOMO = False
DEBUG = False
XML = False
XML_PATH = "."
CONFIG_FILE = "rece.ini"
WEBSERVICE = ""
CHARSET = "latin1"
FIX_ENCODING = False
TIMEOUT = 30
if '--wsmtx' in sys.argv:
    QTY = [12, 2]
    IMPTE = [15, 2]
    PRECIO = [12,6]
    SUBTOTAL = [14,2]
elif '--dec=6' in sys.argv:
    QTY = [18, 6]
    PRECIO = [18, 6]
    SUBTOTAL = [15, 2]
else:
    QTY = [12, 2]
    IMPTE = [15, 3]
    PRECIO = [12, 3]
    SUBTOTAL = [14, 3]
DESC = 'ds'
DESC1 = 'ds'
SCHEMA = {'encabezado': 'encabezado', 'detalle':'detalle', 'permiso':'permiso', 'cmp_asoc':'cmp_asoc', 'iva':'iva', 'tributo':'tributo', 'xml':''}
VT = ["{13}", "\v"]
CAE_NULL = None
FECHA_VTO_NULL = None
RESULTADO_NULL = None
NULL = None

LICENCIA = u"""
fe_db.py: Interfaz por base de datos para generar Facturas Electrónica 
Copyright (C) 2008/2009/2010/2011/2012 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA=u"""
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --esquema: muestra el esquema de la base de datos a utilizar
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una factura de prueba (no usar en producción!)
  --cargar: carga un archivo de entrada (txt) a la base de datos
  --grabar: graba un archivo de salida (txt) con los datos de los comprobantes procesados
  --xml: almacena los requerimientos y respuestas XML (depuración)
  --pdf: genera la imágen de factura en PDF
  --email: envia el pdf generado por correo electronico
  
  --wsfe o -wsfev1 o --wsfex: selecciona el webservice a utilizar

  --dummy: consulta estado de servidores
  --aut: obtiene el código de autorización electrónico (sino no llama al webservice)
  --get: recupera datos de un comprobante autorizado previamente (verificación)
  --ult: consulta último número de comprobante
  --id: recupera último número de transacción

Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
"""

# definición del formato del archivo de intercambio:
N = 'Numerico'
A = 'Alfanumerico'
I = 'Importe'
ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('webservice', 6, A), # wsfe, wsbfe, wsfex, wsfev1
    ('fecha_cbte', 8, A),
    ('tipo_cbte', 2, N), ('punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ('tipo_expo', 1, N), # 1:bienes, 2:servicios,... 
    ('permiso_existente', 1, A), # S/N/
    ('dst_cmp', 3, N), # 203
    ('nombre_cliente', 200, A), # 'Joao Da Silva'
    ('tipo_doc', 2, N),
    ('nro_doc', 11, N), # cuit_pais_cliente 50000000016
    ('domicilio_cliente', 300, A), # 'Rua 76 km 34.5 Alagoas'
    ('id_impositivo', 50, A), # 'PJ54482221-l'    
    ('imp_total', IMPTE, I), 
    ('imp_tot_conc', IMPTE, I),
    ('imp_neto', IMPTE, I), ('impto_liq', IMPTE, I),
    ('impto_liq_nri', IMPTE, I), ('imp_op_ex', IMPTE, I),
    ('impto_perc', 15, I), ('imp_iibb', IMPTE, I),
    ('impto_perc_mun', IMPTE, I), ('imp_internos', IMPTE, I),
    ('imp_trib', IMPTE, I),
    ('moneda_id', 3, A),
    ('moneda_ctz', (10,6), I), #10,6
    ('obs_comerciales', 1000, A),
    ('obs', 1000, A),
    ('forma_pago', 50, A),
    ('incoterms', 3, A),
    ('incoterms_ds', 20, A),
    ('idioma_cbte', 1, A),
    ('zona', 5, A),
    ('fecha_venc_pago', 8,A),
    ('presta_serv', 1, N),
    ('fecha_serv_desde', 8, A),
    ('fecha_serv_hasta', 8, A),
    ('cae', 14, N), ('fecha_vto', 8, A),
    ('resultado', 1, A), 
    ('reproceso', 1, A),
    ('motivo', 40, A),
    ('id', 15, N),
    ('telefono_cliente', 50, A),
    ('localidad_cliente', 50, A),
    ('provincia_cliente', 50, A),
    ('formato_id', 10, N),
    ('email', 100, A),
    ('pdf', 100, A),
    ('err_code', 6, A),
    ('err_msg', 1000, A),
    ('dato_adicional1', 30, A),
    ('dato_adicional2', 30, A),
    ('dato_adicional3', 30, A),
    ('dato_adicional4', 100, A),
    ('dato_adicional5', 100, A),
    ('dato_adicional6', 100, A),
    ('dato_adicional7', 1000, A),
    ('descuento', IMPTE, I), 
    ('imp_subtotal', IMPTE, I),
    ]

DETALLE = [
    ('tipo_reg', 1, N), # 1: detalle item
    ('codigo', 30, A),
    ('qty', QTY, I),
    ('umed', 2, N),
    ('precio', PRECIO, I),
    ('imp_total', SUBTOTAL, I),
    ('iva_id', 5, N),
    ('ds', 4000, A),
    ('ncm', 15, A),
    ('sec', 15, A),
    ('bonif', 15, I),
    ('imp_iva', 15, I),
    ('dato_a', 15, A),
    ('dato_b', 15, A),
    ('dato_c', 50, A),
    ('dato_d', 50, A),
    ('dato_e', 100, A), 
    ('u_mtx', 10, N),
    ('cod_mtx', 30, A),
    ('obs', 4000, A),
    ]

PERMISO = [
    ('tipo_reg', 1, N), # 2: permiso
    ('id_permiso', 16, A),
    ('dst_merc', 3, N),
    ]

CMP_ASOC = [
    ('tipo_reg', 1, N), # 3: comprobante asociado
    ('cbte_tipo', 3, N), ('cbte_punto_vta', 4, N),
    ('cbte_nro', 8, N), 
    ]

IVA = [
    ('tipo_reg', 1, N), # 4: alícuotas de iva
    ('iva_id', 5, N),
    ('base_imp', IMPTE, I), 
    ('importe', IMPTE, I), 
    ]

TRIBUTO = [
    ('tipo_reg', 1, N), # 5: tributos
    ('tributo_id', 5, N),
    (DESC, 100, A),
    ('base_imp', IMPTE, I), 
    ('alic', 15, I), 
    ('importe', IMPTE, I), 
    ]


def autenticar(cert, privatekey, url, webservice, force=False, ttl=60*60*5, proxy=None):
    if webservice=='wsfev1':
        webservice='wsfe'
    elif webservice=='wsfexv1':
        webservice='wsfex'
    elif webservice=='wsmtx':
        webservice='wsmtxca'
    xml_path = "ta-%s.xml" % webservice
    if force or not os.path.exists(xml_path) or os.path.getmtime(xml_path)+(ttl)<time.time():
        if DEBUG or True:
            print "creando %s" % xml_path
        ws = wsaa.WSAA()
        tra = ws.CreateTRA(webservice, ttl=ttl)
        if DEBUG:
            print "-" * 78
            print tra
            print "-" * 78
        cms = ws.SignTRA(str(tra),str(cert),str(privatekey))
        ws.Conectar("", url, proxy=proxy, cacert=CACERT, timeout=TIMEOUT)
        xml = ws.LoginCMS(str(cms))
        f = open(xml_path, "w")
        f.write(xml)
        f.close()
    if DEBUG:
        print "leyendo %s" % xml_path
    f = open(xml_path, "r")
    xml = f.read()
    f.close()
    if DEBUG:
        print xml
    ta = SimpleXMLElement(xml)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    return token, sign

keys_map = {'ncm':'Pro_codigo_ncm', 'bonif':'Imp_bonif', 'precio':'Pro_precio_uni', 'sec':'Pro_codigo_sec', 
                'ds':'Pro_ds', 'umed':'Pro_umed', 'qty':'Pro_qty', 'imp_moneda_id':'Imp_moneda_Id', 
                'moneda_id':'Moneda_Id'}

det_wsfex_map = {'codigo':'Pro_codigo', 'precio':'Pro_precio_uni','imp_total':'Pro_total_item',  
                'ds':'Pro_ds', 'umed':'Pro_umed', 'qty':'Pro_qty', }

cmp_wsfex_map = {'cbte_tipo':'CBte_tipo', 'cbte_punto_vta':'Cbte_punto_vta','cbte_nro':'Cbte_nro', }
permiso_wsfex_map = {'id_permiso':'Id_permiso', 'dst_merc':'Dst_merc'}

def ar_to_iso(d):
    if d:
        dd = d[:4] + "-" + d[4:6] + "-" + d[6:]
        return dd

def iso_to_ar(d):
    return d and d.strip("-")

def autorizar(client, token, sign, cuit, fact, informar_caea=False):
    # prevengo problemas si hay errores
    # limpio 'cae', 'fecha_vto', 'resultado', 'reproceso', 'motivo', 'err_code', 'err_msg')
    fact.update({"motivo": "", "reproceso": "", 'resultado': "", 
                 'err_code': "", 'err_msg': "",})
    if not informar_caea:
        fact.update({'cae': "", 'fecha_vto': "", })
    ult_cbte = None

    if False and (not type(id) is long and (not fact['id'].strip() or int(fact['id'])==0)):
        # TODO: habria que leer y/o grabar el id en el archivo
        ##id += 1 # incremento el nº de transacción 
        # Por el momento, el id se calcula con el tipo, pv y nº de comprobant
        i = long(fact['cbte_nro'])
        i += (int(fact['cbte_nro'])*10**4 + int(fact['punto_vta']))*10**8
        fact['id'] = i

    if WEBSERVICE == "wsfe":
        kwargs = dict([(k,v) for k,v in fact.items() if k in ('tipo_doc', 'nro_doc',
            'tipo_cbte', 'punto_vta', 'fecha_cbte', 'fecha_venc_pago',  
            'imp_total', 'imp_neto', 'impto_liq', 'imp_tot_conc', 'impto_liq_rni', 'imp_op_ex', 
            'presta_serv', 'fecha_serv_desde', 'fecha_serv_hasta')])
        kwargs['cbt_desde'] = fact['cbte_nro']
        kwargs['cbt_hasta'] = fact['cbte_nro']
    elif WEBSERVICE == "wsfex":
        kwargs = dict([(k in keys_map and keys_map[k] or k.capitalize(),v) for k,v in fact.items() if k in ('fecha_cbte', 
            'tipo_cbte', 'punto_vta', 'cbte_nro', 'tipo_expo', 'permiso_existente', 
            'dst_cmp', 'nombre_cliente', 'tipo_doc', 'nro_doc', 'domicilio_cliente', 
            'id_impositivo', 'imp_total', 'moneda_id', 'moneda_ctz', 
            'obs_comerciales', 'obs', 'forma_pago', 'incoterms', 'incoterms_ds', 
            'idioma_cbte', 'Items', 'Cmps_asoc', 'Permisos')])        
        kwargs['Cliente'] = kwargs['Nombre_cliente']
        kwargs['Cuit_pais_cliente'] = kwargs['Nro_doc']
        del kwargs['Nro_doc']
        del kwargs['Tipo_doc']
        del kwargs['Nombre_cliente']
        items = []
        for item in kwargs['Items']:
            items.append(dict((det_wsfex_map[k],v) for k, v in item['Item'].items() if k in det_wsfex_map))
        kwargs['Items'] = [{'Item': item} for item in items]
        if 'Cmps_asoc' in kwargs:
            cmps_asoc = []
            for cmp_asoc in kwargs['Cmps_asoc']:
                cmps_asoc.append(dict((cmp_wsfex_map[k],v) for k, v in cmp_asoc['Cmp_asoc'].items() if k in cmp_wsfex_map))
            kwargs['Cmps_asoc'] = [{'Cmp_asoc': cmp_asoc} for cmp_asoc in cmps_asoc]
        if 'Permisos' in kwargs:
            permisos = []
            for permiso in kwargs['Permisos']:
                permisos.append(dict((permiso_wsfex_map[k],v) for k, v in permiso['Permiso'].items() if k in permiso_wsfex_map))
            kwargs['Permisos'] = [{'Permiso': permiso} for permiso in permisos]
        
        if DEBUG:
            print kwargs        

    elif WEBSERVICE == 'wsfev1':
        if not fact['cbte_nro'] or int(fact['cbte_nro']) == 0:
            ult_cbte = client.CompUltimoAutorizado(fact['tipo_cbte'], fact['punto_vta'])
            if not ult_cbte:
                ult_cbte = 0
            if DEBUG: print "actualizando ultimo cbte_nro:", ult_cbte
            fact['cbte_nro'] = long(ult_cbte) + 1

        client.Token = token
        client.Sign = sign
        client.Cuit = str(cuit)
        client.CrearFactura(
            concepto=fact['presta_serv']+1,
            tipo_doc=fact['tipo_doc'], 
            nro_doc=fact['nro_doc'], 
            tipo_cbte=fact['tipo_cbte'], 
            punto_vta=fact['punto_vta'],
            cbt_desde=fact['cbte_nro'], 
            cbt_hasta=fact['cbte_nro'], 
            imp_total=fact['imp_total'], 
            imp_tot_conc=fact['imp_tot_conc'], 
            imp_neto=fact['imp_neto'],
            imp_iva=fact['impto_liq'],
            imp_trib=fact['imp_trib'],
            imp_op_ex=fact['imp_op_ex'], 
            fecha_cbte=fact['fecha_cbte'], 
            fecha_venc_pago=fact['fecha_venc_pago'], 
            fecha_serv_desde=fact['fecha_serv_desde'], 
            fecha_serv_hasta=fact['fecha_serv_hasta'],
            moneda_id=fact['moneda_id'], 
            moneda_ctz=fact['moneda_ctz'])

        if 'Cmps_asoc' in fact:
            for it in fact['Cmps_asoc']:
                cmp_asoc = it['Cmp_asoc']
                client.AgregarCmpAsoc(
                    tipo=cmp_asoc['cbte_tipo'], 
                    pto_vta=cmp_asoc['cbte_punto_vta'], 
                    nro=cmp_asoc['cbte_nro'])

        if 'Ivas' in fact:
            for it in fact['Ivas']:
                iva = it['Iva']
                client.AgregarIva(
                    iva_id=iva['iva_id'], 
                    base_imp=iva['base_imp'], 
                    importe=iva['importe'])

        if 'Tributos' in fact:
            for it in fact['Tributos']:
                tributo = it['Tributo']
                client.AgregarTributo(
                    tributo_id=tributo['tributo_id'], 
                    desc=tributo[DESC1], 
                    base_imp=tributo['base_imp'], 
                    alic=tributo['alic'], 
                    importe=tributo['importe'])

        kwargs = client.factura

    elif WEBSERVICE == 'wsfexv1':
        client.Token = token
        client.Sign = sign
        client.Cuit = str(cuit)
        client.CrearFactura(
            tipo_cbte=fact['tipo_cbte'], 
            punto_vta=fact['punto_vta'],
            cbte_nro=fact['cbte_nro'],
            fecha_cbte=fact['fecha_cbte'],
            imp_total=fact['imp_total'], 
            tipo_expo=fact['tipo_expo'],
            permiso_existente=fact['permiso_existente'], 
            pais_dst_cmp=fact['dst_cmp'],
            nombre_cliente=fact['nombre_cliente'], 
            cuit_pais_cliente=fact['nro_doc'], 
            domicilio_cliente=fact['domicilio_cliente'],
            id_impositivo=fact['id_impositivo'], 
            moneda_id=fact['moneda_id'], 
            moneda_ctz=fact['moneda_ctz'],
            obs_comerciales=fact['obs_comerciales'], 
            obs_generales=fact['obs'], 
            forma_pago=fact['forma_pago'], 
            incoterms=fact['incoterms'], 
            idioma_cbte=fact['idioma_cbte'], 
            incoterms_ds=fact['incoterms_ds'],
            )

        if 'Cmps_asoc' in fact:
            for it in fact['Cmps_asoc']:
                cmp_asoc = it['Cmp_asoc']
                client.AgregarCmpAsoc(
                    cbte_tipo=cmp_asoc['cbte_tipo'], 
                    cbte_punto_vta=cmp_asoc['cbte_punto_vta'], 
                    cbte_nro=cmp_asoc['cbte_nro'])

        if 'Permisos' in fact:
            for it in fact['Permisos']:
                permiso = it['Permiso']
                client.AgregarPermiso(
                    id_permiso=permiso['id_permiso'], 
                    dst_merc=permiso['dst_merc'])

        if 'Items' in fact:
            for it in fact['Items']:
                item = it['Item']
                client.AgregarItem(
                    codigo=item['codigo'], 
                    ds=item['ds'], 
                    qty=item['qty'], 
                    umed=item['umed'], 
                    precio=item['precio'], 
                    importe=item['imp_total'], 
                    bonif=item['bonif'],
                )
    
        kwargs = client.factura

    elif WEBSERVICE == 'wsmtx':
        client.Token = token
        client.Sign = sign
        client.Cuit = str(cuit)
        client.CrearFactura(
            concepto=fact['presta_serv']+1,
            tipo_doc=fact['tipo_doc'], 
            nro_doc=fact['nro_doc'], 
            tipo_cbte=fact['tipo_cbte'], 
            punto_vta=fact['punto_vta'],
            cbt_desde=fact['cbte_nro'], 
            cbt_hasta=fact['cbte_nro'], 
            imp_total=fact['imp_total'], 
            imp_tot_conc=fact['imp_tot_conc'], 
            imp_neto=fact['imp_neto'],
            imp_subtotal=fact['imp_subtotal'], 
            imp_trib=fact['imp_trib'],
            imp_op_ex=fact['imp_op_ex'], 
            fecha_cbte=ar_to_iso(fact['fecha_cbte']), 
            fecha_venc_pago=ar_to_iso(fact['fecha_venc_pago']), 
            fecha_serv_desde=ar_to_iso(fact['fecha_serv_desde']), 
            fecha_serv_hasta=ar_to_iso(fact['fecha_serv_hasta']),
            moneda_id=fact['moneda_id'], 
            moneda_ctz=fact['moneda_ctz'],
            caea=fact['cae'] if informar_caea else None, 
            fch_venc_cae=ar_to_iso(fact['fecha_vto']) if informar_caea else None,
            obs='')

        if 'Cmps_asoc' in fact:
            for it in fact['Cmps_asoc']:
                cmp_asoc = it['Cmp_asoc']
                client.AgregarCmpAsoc(
                    tipo=cmp_asoc['cbte_tipo'], 
                    pto_vta=cmp_asoc['cbte_punto_vta'], 
                    nro=cmp_asoc['cbte_nro'])

        if 'Ivas' in fact:
            for it in fact['Ivas']:
                iva = it['Iva']
                client.AgregarIva(
                    iva_id=iva['iva_id'], 
                    base_imp=iva['base_imp'], 
                    importe=iva['importe'])

        if 'Tributos' in fact:
            for it in fact['Tributos']:
                tributo = it['Tributo']
                client.AgregarTributo(
                    tributo_id=tributo['tributo_id'], 
                    desc=tributo[DESC1], 
                    base_imp=tributo['base_imp'], 
                    alic=tributo['alic'], 
                    importe=tributo['importe'])

        if 'Items' in fact:
            for it in fact['Items']:
                item = it['Item']
                ##if item['precio'] is None:
                ##    continue
                client.AgregarItem(
                    u_mtx=item['u_mtx'],
                    cod_mtx=item['cod_mtx'],
                    codigo=item['codigo'],
                    ds=item['ds'],
                    qty=item['qty'],
                    umed=item['umed'],
                    precio=item['precio'],
                    bonif=item['bonif'],
                    iva_id=item['iva_id'],
                    imp_iva=item['imp_iva'],
                    imp_subtotal=item['imp_total'],
                    )
        kwargs = client.factura
    else:
        kwargs = {}

    if DEBUG:
        print '\n'.join(["%s='%s'" % (k,v) for k,v in kwargs.items()])
        print 'id:', fact['id']

    if True or not DEBUG or raw_input("Facturar (S/n)?")=="S":

        if WEBSERVICE == 'wsfe':
            ret = wsfe.aut(client, token, sign, cuit, id=fact['id'], **kwargs)
            fact.update(ret)
        elif WEBSERVICE == 'wsfex':
            ##raise RuntimeError("no soportado")
            try:
                auth, events = wsfex.authorize(client, token, sign, cuit,
                                               id=fact['id'],
                                               factura=kwargs)
                dic={'cae': auth['cae'].encode(CHARSET, 'ignore'),
                     "motivo": auth['obs'].encode(CHARSET, 'ignore'),
                     "reproceso":auth['reproceso'].encode(CHARSET, 'ignore'),
                     'fecha_vto': auth['fch_venc_cae'].encode(CHARSET, 'ignore'), 
                     'resultado': auth['resultado'].encode(CHARSET, 'ignore')}
            except wsfex.FEXError, e:
                dic={'cae': '',
                     "motivo": '',
                     "reproceso": '',
                     'fecha_vto': '', 
                     'resultado': 'E',
                     'err_msg': e.msg,
                     'err_code': e.code,
                     }
            fact.update(dic)
        elif WEBSERVICE == 'wsfev1':
            cae = client.CAESolicitar()
            dic={'cae': client.CAE.encode(CHARSET, 'ignore'),
                "motivo": client.Obs.encode(CHARSET, 'ignore'),
                "reproceso": client.Reproceso.encode(CHARSET, 'ignore'),
                'fecha_vto': (client.Vencimiento or '').encode(CHARSET, 'ignore'), 
                'resultado': client.Resultado.encode(CHARSET, 'ignore'),
                'err_msg': client.ErrMsg.encode('ascii', 'replace').replace("\n", " | "),
                }
            if ult_cbte is not None:
                fact['cbte_nro'] = client.CbteNro or 0
                if DEBUG: print "estableciendo cbte_nro = ", fact['cbte_nro']
            fact.update(dic)
        elif WEBSERVICE == 'wsfexv1':
            ##raise RuntimeError("no soportado")
            cae = client.Authorize(id=fact['id'])
            dic={'cae': client.CAE.encode(CHARSET, 'ignore'),
                "motivo": client.Obs and client.Obs.encode(CHARSET, 'ignore') or '',
                "reproceso": client.Reproceso.encode(CHARSET, 'ignore'),
                'fecha_vto': (client.FchVencCAE or '').encode(CHARSET, 'ignore'), 
                'resultado': client.Resultado.encode(CHARSET, 'ignore'),
                'err_msg': client.ErrMsg.encode('ascii', 'replace').replace("\n", " | "),
                }
            fact.update(dic)
        elif WEBSERVICE == 'wsmtx':
            if not informar_caea:
                cae = client.AutorizarComprobante()
                dic = {'cae': client.CAE.encode(CHARSET, 'ignore')}
            else:
                cae = client.InformarComprobanteCAEA()
                dic = {}
            dic.update({
                "motivo": client.Obs.encode(CHARSET, 'ignore'),
                "reproceso": client.Reproceso.encode(CHARSET, 'ignore'),
                'fecha_vto': (client.Vencimiento or '').encode(CHARSET, 'ignore').replace("/", ""), 
                'resultado': client.Resultado.encode(CHARSET, 'ignore'),
                'err_msg': client.ErrMsg.encode(CHARSET, 'ignore').replace("\n", " | "),
                })
            fact.update(dic)
        else:
            raise RuntimeError("NO indico webservice!")
    return fact


def leer_linea_txt(linea, formato):
    dic = {}
    comienzo = 1
    for (clave, longitud, tipo) in formato:    
        if isinstance(longitud, (tuple, list)):
            longitud, decimales = longitud
        else:
            decimales = 2
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if tipo == N:
                if valor:
                    valor = int(valor)
                else:
                    valor = 0
            elif tipo == I:
                if valor:
                    try:
                        valor = valor.strip(" ")
                        if '.' in valor:
                            valor = Decimal(valor)
                        else:
                            valor = Decimal(("%%s.%%0%sd" % decimales) % (int(valor[:-decimales] or '0'), int(valor[-decimales:] or '0')))
                    except ValueError:
                        raise ValueError("Campo invalido: %s = '%s'" % (clave, valor))
                else:
                    valor = 0.00
            elif tipo == A:
                for c in VT:
                    valor = valor.replace(c, "\n") # reemplazo salto de linea
            dic[clave] = valor
            comienzo += longitud
        except Exception, e:
            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic


def cargar_archivo(entrada):
    f_entrada = open(entrada,"r")
    try:
        facts = []
        for linea in f_entrada:
            # testear!
            linea = unicode(linea, CHARSET, 'replace')
            if FIX_ENCODING:
                linea = linea.encode("ascii", 'replace')
            if str(linea[0])=='0':
                encabezado = fact = leer_linea_txt(linea, ENCABEZADO)
                facts.append(encabezado)
                detalles = fact['Items'] = []
                permisos = fact['Permisos'] = []
                cbtasocs = fact['Cmps_asoc'] = []
                ivas = fact['Ivas'] = []
                tributos = fact['Tributos'] = []         
                if fact['id']==0:
                    # genero un ID "autonumerico"
                    i = long(fact['cbte_nro'])
                    i += (int(fact['tipo_cbte'])*10**4 + int(fact['punto_vta']))*10**8
                    fact['id'] = i
            elif str(linea[0])=='1':
                detalle = leer_linea_txt(linea, DETALLE)
                detalle['id'] = encabezado['id']
                detalles.append({'Item': detalle})
            elif str(linea[0])=='2':
                permiso = leer_linea_txt(linea, PERMISO)
                permiso['id'] = encabezado['id']
                permisos.append({'Permiso': permiso})
            elif str(linea[0])=='3':
                cbtasoc = leer_linea_txt(linea, CMP_ASOC)
                cbtasoc['id'] = encabezado['id']
                cbtasocs.append({'Cmp_asoc': cbtasoc})
            elif str(linea[0])=='4':
                iva = leer_linea_txt(linea, IVA)
                iva['id'] = encabezado['id']
                ivas.append({'Iva': iva})
            elif str(linea[0])=='5':
                tributo = leer_linea_txt(linea, TRIBUTO)
                tributo['id'] = encabezado['id']
                tributos.append({'Tributo': tributo})
            else:
                print "Tipo de registro incorrecto:", linea[0]
        
        return facts
    finally:
        f_entrada.close()

def escribir_linea_txt(dic, formato):
    linea = " " * 335
    comienzo = 1
    for (clave, longitud, tipo) in formato:
        if isinstance(longitud, (tuple, list)):
            longitud, decimales = longitud
        else:
            decimales = 2
        try:
            if clave.lower() in dic:
                clave = clave.lower()
            valor = dic.get(clave,"")
            if not isinstance(valor, basestring):
                valor = str(valor)
            if isinstance(valor, unicode):
                valor = valor.encode(CHARSET)
            if valor == 'None':
                valor = ''
            if valor=="" and clave in keys_map:
                valor = str(dic.get(keys_map[clave],""))
            if tipo == N and valor and valor!="NULL":
                valor = ("%%0%dd" % longitud) % int(valor)
            elif tipo == I and valor:
                valor = ("%%0%dd" % longitud) % (float(valor)*(10**decimales))
            else:
                valor = ("%%-%ds" % longitud) % valor.replace("\n", VT[0]) # reemplazo salto de linea
            linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
            comienzo += longitud
        except Exception, e:
            ##raise
            raise ValueError("Error al escribir campo %s val '%s': %s" % (
                clave, valor, str(e)))
    return linea + "\n"


def grabar_archivo(fact, archivo):
    f_salida = open(salida,"a")

    fact['tipo_reg'] = 0
    f_salida.write(escribir_linea_txt(fact, ENCABEZADO))
    for it in fact['Items']:
        it['Item']['tipo_reg'] = 1
        f_salida.write(escribir_linea_txt(it['Item'], DETALLE))
    for it in fact.get('Ivas', []):
        it['Iva']['tipo_reg'] = 4
        f_salida.write(escribir_linea_txt(it['Iva'], IVA))
    for it in fact.get('Tributos', []):
        it['Tributo']['tipo_reg'] = 5
        f_salida.write(escribir_linea_txt(it['Tributo'], TRIBUTO))
    f_salida.close()

def max_id(conexion):
    cur = conexion.cursor()
    query = ("SELECT MAX(%%(id)s) FROM %(encabezado)s" % SCHEMA) % conf_encabezado
    if DEBUG: print "ejecutando",query
    ret = None
    try:
        execute(cur, query)
        for row in cur:
            ret = row[0]
        if not ret:
            ret = 20000
        print "MAX_ID = ", ret
        return ret
    finally:
        cur.close()

def redondear(formato, clave, valor):
    # corregir redondeo (aparentemente sqlite no guarda correctamente los decimal)
    import decimal
    long = [fmt[1] for fmt in formato if fmt[0]==clave]
    tipo = [fmt[2] for fmt in formato if fmt[0]==clave]
    if not tipo:
        return valor
    tipo = tipo[0]
    if DEBUG: print "tipo", tipo, clave, valor, long
    if valor is None:
        return None
    if valor == "":
        return ""
    if tipo == A:
        return valor
    if tipo == N:
        return int(valor)
    if isinstance(valor, (int, float)):
        valor = str(valor)
    if isinstance(valor, basestring):
        valor = Decimal(valor) 
    if long and isinstance(long[0], (tuple, list)):
        decimales = Decimal('1')  / Decimal(10**(long[0][1]))
    else:
        decimales = Decimal('.01')
    valor1 = valor.quantize(decimales, rounding=decimal.ROUND_DOWN)
    if valor != valor1 and DEBUG:
        print "REDONDEANDO ", clave, decimales, valor, valor1
    return valor1


def leer_facturas(conexion,ids=None):
    cur = conexion.cursor()
    if not ids:
        query = ("SELECT * FROM %(encabezado)s WHERE (%%(resultado)s IS NULL OR %%(resultado)s='' OR %%(resultado)s=' ') AND (%%(id)s IS NOT NULL) AND %%(webservice)s=? ORDER BY %%(tipo_cbte)s, %%(punto_vta)s, %%(cbte_nro)s" % SCHEMA) % conf_encabezado
        if WEBSERVICE == "wsfexv1":
            webservice = "wsfex1"
        else:
            webservice = WEBSERVICE
        ids = [webservice]
    else:
        query = ("SELECT * FROM %(encabezado)s WHERE " % SCHEMA) + " OR ".join(["%(id)s=?" % conf_encabezado for id in ids])
    if DEBUG: print "ejecutando",query, ids
    try:
        execute(cur, query,ids)
        rows = cur.fetchall()
        description = cur.description
        for row in rows:
            detalles = []
            encabezado = {}
            for i, k in enumerate(description):
                val = row[i]
                if isinstance(val,str):
                    val = val.decode(CHARSET)
                if isinstance(val,basestring):
                    val = val.strip()
                key = conf_encabezado_rev.get(k[0], k[0].lower())
                val = redondear(ENCABEZADO, key, val)                
                encabezado[key] = val
            print encabezado
            detalles = []
            if DEBUG: print ("SELECT * FROM %(detalle)s WHERE %%(id)s = ?" % SCHEMA) % conf_detalle, [encabezado['id']]
            execute(cur, ("SELECT * FROM %(detalle)s WHERE %%(id)s = ?" % SCHEMA) % conf_detalle, [encabezado['id']]) 
            for it in cur.fetchall():
                detalle = {}
                for i, k in enumerate(cur.description):
                    val = it[i]
                    if isinstance(val,str):
                        val = val.decode(CHARSET)
                    key = conf_detalle_rev.get(k[0], k[0].lower())
                    val = redondear(DETALLE, key, val)
                    detalle[key] = val
                detalles.append(detalle)
            encabezado['Items'] = [{'Item': detalle} for detalle in detalles]

            cmps_asoc = []
            if DEBUG: print ("SELECT * FROM %(cmp_asoc)s WHERE %%(id)s = ?" % SCHEMA) % conf_cmp_asoc, [encabezado['id']]
            execute(cur, ("SELECT * FROM %(cmp_asoc)s WHERE %%(id)s = ?" % SCHEMA) % conf_cmp_asoc, [encabezado['id']]) 
            for it in cur.fetchall():
                cmp_asoc = {}
                for i, k in enumerate(cur.description):
                    val = it[i]
                    key = conf_cmp_asoc_rev.get(k[0], k[0].lower())
                    cmp_asoc[key] = val
                cmps_asoc.append(cmp_asoc)
            if cmps_asoc:
                encabezado['Cmps_asoc'] = [{'Cmp_asoc': cmp_asoc} for cmp_asoc in cmps_asoc]

            permisos = []
            if DEBUG: print ("SELECT * FROM %(permiso)s WHERE %%(id)s = ?" % SCHEMA) % conf_permiso, [encabezado['id']]
            execute(cur, ("SELECT * FROM %(permiso)s WHERE %%(id)s = ?" % SCHEMA) % conf_permiso, [encabezado['id']]) 
            for it in cur.fetchall():
                permiso = {}
                for i, k in enumerate(cur.description):
                    val = it[i]
                    key = conf_permiso_rev.get(k[0], k[0].lower())
                    permiso[key] = val
                permisos.append(permiso)
            if permisos:
                encabezado['Permisos'] = [{'Permiso': permiso} for permiso in permisos]

            ivas = []
            if DEBUG: print ("SELECT * FROM %(iva)s WHERE %%(id)s = ?" % SCHEMA) % conf_iva, [encabezado['id']]
            execute(cur, ("SELECT * FROM %(iva)s WHERE %%(id)s = ?" % SCHEMA) % conf_iva, [encabezado['id']]) 
            for it in cur.fetchall():
                iva = {}
                for i, k in enumerate(cur.description):
                    val = it[i]
                    key = conf_iva_rev.get(k[0], k[0].lower())
                    val = redondear(IVA, key, val)
                    iva[key] = val
                ivas.append(iva)
            if ivas:
                encabezado['Ivas'] = [{'Iva': iva} for iva in ivas]

            tributos = []
            if DEBUG: print ("SELECT * FROM %(tributo)s WHERE %%(id)s = ?" % SCHEMA) % conf_tributo, [encabezado['id']]
            execute(cur, ("SELECT * FROM %(tributo)s WHERE %%(id)s = ?" % SCHEMA) % conf_tributo, [encabezado['id']]) 
            for it in cur.fetchall():
                tributo = {}
                for i, k in enumerate(cur.description):
                    val = it[i]
                    key = conf_tributo_rev.get(k[0], k[0].lower())
                    val = redondear(TRIBUTO, key, val)
                    tributo[key] = val
                tributos.append(tributo)
            if tributos:
                encabezado['Tributos'] = [{'Tributo': tributo} for tributo in tributos]
            
            yield encabezado
        conexion.commit()
    finally:
        cur.close()

def escribir_facturas(facts, conexion, commit=True):
    cur = conexion.cursor()
    try:
        for dic in facts:
            query = "INSERT INTO %(encabezado)s (%%s) VALUES (%%s)" % SCHEMA
            fields = ','.join([conf_encabezado.get(k, k) for k,t,n in ENCABEZADO if k in dic])
            values = ','.join(['?' for k,t,n in ENCABEZADO if k in dic])
            if DEBUG: print "Ejecutando2: %s %s" % (query % (fields, values), [dic[k] for k,t,n in ENCABEZADO if k in dic])
            execute(cur, query % (fields, values), [dic[k] for k,t,n in ENCABEZADO if k in dic])
            query = ("INSERT INTO %(detalle)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % SCHEMA) % conf_detalle
            for it in dic['Items']:
                item = it['Item']
                fields = ','.join([conf_detalle.get(k, k) for k,t,n in DETALLE if k in item])
                values = ','.join(['?' for k,t,n in DETALLE if k in item])
                if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in DETALLE if k in item])
                execute(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in DETALLE if k in item])
            if 'Cmps_asoc' in dic and conf_cmp_asoc: 
                query = ("INSERT INTO %(cmp_asoc)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % SCHEMA) % conf_cmp_asoc
                for it in dic['Cmps_asoc']:
                    item = it['Cmp_asoc']
                    fields = ','.join([conf_cmp_asoc.get(k, k) for k,t,n in CMP_ASOC if k in item])
                    values = ','.join(['?' for k,t,n in CMP_ASOC if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in CMP_ASOC if k in item])
                    execute(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in CMP_ASOC if k in item])
            if 'Permisos' in dic: 
                query = ("INSERT INTO %(permiso)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % SCHEMA) % conf_permiso
                for it in dic['Permisos']:
                    item = it['Permiso']
                    fields = ','.join([conf_permiso.get(k, k) for k,t,n in PERMISO if k in item])
                    values = ','.join(['?' for k,t,n in PERMISO if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in PERMISO if k in item])
                    execute(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in PERMISO if k in item])
            if 'Tributos' in dic: 
                query = ("INSERT INTO %(tributo)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % SCHEMA) % conf_tributo
                for it in dic['Tributos']:
                    item = it['Tributo']
                    fields = ','.join([conf_tributo.get(k, k) for k,t,n in TRIBUTO if k in item])
                    values = ','.join(['?' for k,t,n in TRIBUTO if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in TRIBUTO if k in item])
                    execute(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in TRIBUTO if k in item])
            if 'Ivas' in dic: 
                query = ("INSERT INTO %(iva)s (%%(id)s, %%%%s) VALUES (?, %%%%s)" % SCHEMA) % conf_iva
                for it in dic['Ivas']:
                    item = it['Iva']
                    fields = ','.join([conf_iva.get(k, k) for k,t,n in IVA if k in item])
                    values = ','.join(['?' for k,t,n in IVA if k in item])
                    if DEBUG: print "Ejecutando: %s %s" % (query % (fields, values), [dic['id']] + [item[k] for k,t,n in IVA if k in item])
                    execute(cur, query % (fields, values), [dic['id']] + [item[k] for k,t,n in IVA if k in item])
        if commit:
            conexion.commit()
    finally:
        pass


def actualizar_factura(dic, conexion):
    update = ('cae', 'fecha_vto', 'resultado', 'reproceso', 'motivo', 'err_code', 'err_msg', 'cbte_nro')
    cur = conexion.cursor()
    if dic['cae']=='NULL' or dic['cae']=='' or dic['cae']==None:
        dic['cae'] = CAE_NULL
        dic['fecha_vto'] = FECHA_VTO_NULL
    if 'null' in conf_db and dic['resultado']==None or dic['resultado']=='':
        dic['resultado'] = RESULTADO_NULL
    for k in ['reproceso', 'motivo', 'err_code', 'err_msg']:
        if 'null' in conf_db and dic[k]==None or dic[k]=='':
            if DEBUG: print k, "NULL"
            dic[k] = NULL
    try:
        query = ("UPDATE %(encabezado)s SET %%%%s WHERE %%(id)s=?" % SCHEMA) % conf_encabezado
        fields = [conf_encabezado.get(k, k) for k,t,n in ENCABEZADO if k in update and k in dic]
        values = [dic[k] for k,t,n in ENCABEZADO if k in update and k in dic]
        query = query % ','.join(["%s=?" % f for f in fields])
        if DEBUG: print query, values+[dic['id']]
        execute(cur, query, values+[dic['id']] )
        conexion.commit()
    except:
        raise
    finally:
        pass


def depurar_xml(client, conexion=None, fact_id=None):
    if SCHEMA['xml'] and conexion:
        cur = conexion.cursor()
        query = "INSERT INTO %(xml)s (id,request,response) VALUES (?, ?,?)" % SCHEMA
        if DEBUG: print query
        execute(cur, query, (fact_id,client.xml_request, client.xml_response) )
        conexion.commit()
    else:
        fecha = time.strftime("%Y%m%d%H%M%S")
        f=open(os.path.join(XML_PATH, "request-%s.xml" % fecha),"w")
        f.write(client.xml_request)
        f.close()
        f=open(os.path.join(XML_PATH, "response-%s.xml" % fecha),"w")
        f.write(client.xml_response)
        f.close()


def digito_verificador_modulo10(codigo):
    "Rutina para el cálculo del dígito verificador 'módulo 10'"
    # http://www.consejo.org.ar/Bib_elect/diciembre04_CT/documentos/rafip1702.htm
    etapa1 = sum([int(c) for i,c in enumerate(codigo) if not i%2])
    etapa2 = etapa1 * 3
    etapa3 = sum([int(c) for i,c in enumerate(codigo) if i%2])
    etapa4 = etapa2 + etapa3
    digito = 10 - (etapa4 - (int(etapa4 / 10) * 10))
    if digito == 10:
        digito = 0
    return str(digito)


def generar_pdf(fact, conexion=None):
    def fmtdate (d):
        if not d or len(d)!=8:
            return ''
        else:
            return "%s/%s/%s" % (d[6:8], d[4:6], d[0:4])
    def fmtnum(i, fmt="%0.2f", monetary=True):
        if i is not None and str(i):
            loc = conf_fact.get('locale','')
            if loc:
                import locale
                locale.setlocale(locale.LC_ALL, loc)
                return locale.format(fmt, Decimal(str(i).replace(",",".")), grouping=True, monetary=monetary)
            else:
                return (fmt % Decimal(str(i).replace(",","."))).replace(".",",")
        else:
            return ''
    fmtimp = lambda i: fmtnum(i, "%0.2f")
    fmtqty = lambda i: fmtnum(i, "%" + conf_fact.get('fmt_cantidad', "0.2") + "f", False)
    fmtpre = lambda i: fmtnum(i, "%" + conf_fact.get('fmt_precio', "0.2") + "f")
    fmtcuit = lambda c: len(c)==11 and "%s-%s-%s" % (c[0:2], c[2:10], c[10:]) or c
    

    # TODO: crear tabla 'umed(id,ds,iso)' en la base de datos...
    umeds_ds = {0: u' ', 1: u'kg', 2: u'm', 3: u'm2', 4: u'm3', 5: u'l', 
             6: u'1000 kWh', 7: u'unidades', 
             8: u'pares', 9: u'docenas', 10: u'quilates', 11: u'millares', 
            14: u'g', 15: u'mm', 16: u'mm3', 17: u'km', 18: u'hl', 20: u'cm', 
            25: u'jgo. pqt. mazo naipes', 27: u'cm3', 29: u'tn', 
            30: u'dam3', 31: u'hm3', 32: u'km3', 33: u'ug', 34: u'ng', 35: u'pg', 41: u'mg', 47: u'mm', 
            48: u'curie', 49: u'milicurie', 50: u'microcurie', 51: u'uiacthor', 52: u'muiacthor', 
            53: u'kg base', 54: u'gruesa', 61: u'kg bruto', 
            62: u'uiactant', 63: u'muiactant', 64: u'uiactig', 65: u'muiactig', 66: u'kg activo', 
            67: u'gramo activo', 68: u'gramo base', 96: u'packs', 97: u'hormas', 
            98: u'bonificaci\xf3n', 99: u'otras unidades'}

    # TODO: crear tabla 'pais(id,ds,iso)' en la base de datos...
    paises = {512: u'FIJI, ISLAS', 513: u'PAPUA NUEVA GUINEA', 514: u'KIRIBATI, ISLAS', 515: u'MICRONESIA,EST.FEDER', 516: u'PALAU', 517: u'TUVALU', 518: u'SALOMON,ISLAS', 519: u'TONGA', 520: u'MARSHALL,ISLAS', 521: u'MARIANAS,ISLAS', 597: u'RESTO OCEANIA', 598: u'INDET.(OCEANIA)', 101: u'BURKINA FASO', 102: u'ARGELIA', 103: u'BOTSWANA', 104: u'BURUNDI', 105: u'CAMERUN', 107: u'REP. CENTROAFRICANA.', 108: u'CONGO', 109: u'REP.DEMOCRAT.DEL CONGO EX ZAIRE', 110: u'COSTA DE MARFIL', 111: u'CHAD', 112: u'BENIN', 113: u'EGIPTO', 115: u'GABON', 116: u'GAMBIA', 117: u'GHANA', 118: u'GUINEA', 119: u'GUINEA ECUATORIAL', 120: u'KENYA', 121: u'LESOTHO', 122: u'LIBERIA', 123: u'LIBIA', 124: u'MADAGASCAR', 125: u'MALAWI', 126: u'MALI', 127: u'MARRUECOS', 128: u'MAURICIO,ISLAS', 129: u'MAURITANIA', 130: u'NIGER', 131: u'NIGERIA', 132: u'ZIMBABWE', 133: u'RWANDA', 134: u'SENEGAL', 135: u'SIERRA LEONA', 136: u'SOMALIA', 137: u'SWAZILANDIA', 138: u'SUDAN', 139: u'TANZANIA', 140: u'TOGO', 141: u'TUNEZ', 142: u'UGANDA', 144: u'ZAMBIA', 145: u'TERRIT.VINCULADOS AL R UNIDO', 146: u'TERRIT.VINCULADOS A ESPA\xd1A', 147: u'TERRIT.VINCULADOS A FRANCIA', 149: u'ANGOLA', 150: u'CABO VERDE', 151: u'MOZAMBIQUE', 152: u'SEYCHELLES', 153: u'DJIBOUTI', 155: u'COMORAS', 156: u'GUINEA BISSAU', 157: u'STO.TOME Y PRINCIPE', 158: u'NAMIBIA', 159: u'SUDAFRICA', 160: u'ERITREA', 161: u'ETIOPIA', 197: u'RESTO (AFRICA)', 198: u'INDETERMINADO (AFRICA)', 200: u'ARGENTINA', 201: u'BARBADOS', 202: u'BOLIVIA', 203: u'BRASIL', 204: u'CANADA', 205: u'COLOMBIA', 206: u'COSTA RICA', 207: u'CUBA', 208: u'CHILE', 209: u'REP\xdaBLICA DOMINICANA', 210: u'ECUADOR', 211: u'EL SALVADOR', 212: u'ESTADOS UNIDOS', 213: u'GUATEMALA', 214: u'GUYANA', 215: u'HAITI', 216: u'HONDURAS', 217: u'JAMAICA', 218: u'MEXICO', 219: u'NICARAGUA', 220: u'PANAMA', 221: u'PARAGUAY', 222: u'PERU', 223: u'PUERTO RICO', 224: u'TRINIDAD Y TOBAGO', 225: u'URUGUAY', 226: u'VENEZUELA', 227: u'TERRIT.VINCULADO AL R.UNIDO', 228: u'TER.VINCULADOS A DINAMARCA', 229: u'TERRIT.VINCULADOS A FRANCIA AMERIC.', 230: u'TERRIT. HOLANDESES', 231: u'TER.VINCULADOS A ESTADOS UNIDOS', 232: u'SURINAME', 233: u'DOMINICA', 234: u'SANTA LUCIA', 235: u'SAN VICENTE Y LAS GRANADINAS', 236: u'BELICE', 237: u'ANTIGUA Y BARBUDA', 238: u'S.CRISTOBAL Y NEVIS', 239: u'BAHAMAS', 240: u'GRENADA', 241: u'ANTILLAS HOLANDESAS', 250: u'AAE Tierra del Fuego - ARGENTINA', 251: u'ZF La Plata - ARGENTINA', 252: u'ZF Justo Daract - ARGENTINA', 253: u'ZF R\xedo Gallegos - ARGENTINA', 254: u'Islas Malvinas - ARGENTINA', 255: u'ZF Tucum\xe1n - ARGENTINA', 256: u'ZF C\xf3rdoba - ARGENTINA', 257: u'ZF Mendoza - ARGENTINA', 258: u'ZF General Pico - ARGENTINA', 259: u'ZF Comodoro Rivadavia - ARGENTINA', 260: u'ZF Iquique', 261: u'ZF Punta Arenas', 262: u'ZF Salta - ARGENTINA', 263: u'ZF Paso de los Libres - ARGENTINA', 264: u'ZF Puerto Iguaz\xfa - ARGENTINA', 265: u'SECTOR ANTARTICO ARG.', 270: u'ZF Col\xf3n - REP\xdaBLICA DE PANAM\xc1', 271: u'ZF Winner (Sta. C. de la Sierra) - BOLIVIA', 280: u'ZF Colonia - URUGUAY', 281: u'ZF Florida - URUGUAY', 282: u'ZF Libertad - URUGUAY', 283: u'ZF Zonamerica - URUGUAY', 284: u'ZF Nueva Helvecia - URUGUAY', 285: u'ZF Nueva Palmira - URUGUAY', 286: u'ZF R\xedo Negro - URUGUAY', 287: u'ZF Rivera - URUGUAY', 288: u'ZF San Jos\xe9 - URUGUAY', 291: u'ZF Manaos - BRASIL', 295: u'MAR ARG ZONA ECO.EX', 296: u'RIOS ARG NAVEG INTER', 297: u'RESTO AMERICA', 298: u'INDETERMINADO (AMERICA)', 301: u'AFGANISTAN', 302: u'ARABIA SAUDITA', 303: u'BAHREIN', 304: u'MYANMAR (EX-BIRMANIA)', 305: u'BUTAN', 306: u'CAMBODYA (EX-KAMPUCHE)', 307: u'SRI LANKA', 308: u'COREA DEMOCRATICA', 309: u'COREA REPUBLICANA', 310: u'CHINA', 312: u'FILIPINAS', 313: u'TAIWAN', 315: u'INDIA', 316: u'INDONESIA', 317: u'IRAK', 318: u'IRAN', 319: u'ISRAEL', 320: u'JAPON', 321: u'JORDANIA', 322: u'QATAR', 323: u'KUWAIT', 324: u'LAOS', 325: u'LIBANO', 326: u'MALASIA', 327: u'MALDIVAS ISLAS', 328: u'OMAN', 329: u'MONGOLIA', 330: u'NEPAL', 331: u'EMIRATOS ARABES UNIDOS', 332: u'PAKIST\xc1N', 333: u'SINGAPUR', 334: u'SIRIA', 335: u'THAILANDIA', 337: u'VIETNAM', 341: u'HONG KONG', 344: u'MACAO', 345: u'BANGLADESH', 346: u'BRUNEI', 348: u'REPUBLICA DE YEMEN', 349: u'ARMENIA', 350: u'AZERBAIJAN', 351: u'GEORGIA', 352: u'KAZAJSTAN', 353: u'KIRGUIZISTAN', 354: u'TAYIKISTAN', 355: u'TURKMENISTAN', 356: u'UZBEKISTAN', 357: u'TERR. AU. PALESTINOS', 397: u'RESTO DE ASIA', 398: u'INDET.(ASIA)', 401: u'ALBANIA', 404: u'ANDORRA', 405: u'AUSTRIA', 406: u'BELGICA', 407: u'BULGARIA', 409: u'DINAMARCA', 410: u'ESPA\xd1A', 411: u'FINLANDIA', 412: u'FRANCIA', 413: u'GRECIA', 414: u'HUNGRIA', 415: u'IRLANDA', 416: u'ISLANDIA', 417: u'ITALIA', 418: u'LIECHTENSTEIN', 419: u'LUXEMBURGO', 420: u'MALTA', 421: u'MONACO', 422: u'NORUEGA', 423: u'PAISES BAJOS', 424: u'POLONIA', 425: u'PORTUGAL', 426: u'REINO UNIDO', 427: u'RUMANIA', 428: u'SAN MARINO', 429: u'SUECIA', 430: u'SUIZA', 431: u'VATICANO(SANTA SEDE)', 433: u'POS.BRIT.(EUROPA)', 435: u'CHIPRE', 436: u'TURQUIA', 438: u'ALEMANIA,REP.FED.', 439: u'BIELORRUSIA', 440: u'ESTONIA', 441: u'LETONIA', 442: u'LITUANIA', 443: u'MOLDAVIA', 444: u'RUSIA', 445: u'UCRANIA', 446: u'BOSNIA HERZEGOVINA', 447: u'CROACIA', 448: u'ESLOVAQUIA', 449: u'ESLOVENIA', 450: u'MACEDONIA', 451: u'REP. CHECA', 453: u'MONTENEGRO', 454: u'SERBIA', 997: u'RESTO CONTINENTE', 998: u'INDET.(CONTINENTE)', 497: u'RESTO EUROPA', 498: u'INDET.(EUROPA)', 501: u'AUSTRALIA', 503: u'NAURU', 504: u'NUEVA ZELANDIA', 505: u'VANATU', 506: u'SAMOA OCCIDENTAL', 507: u'TERRITORIO VINCULADOS A AUSTRALIA', 508: u'TERRITORIOS VINCULADOS AL R. UNIDO', 509: u'TERRITORIOS VINCULADOS A FRANCIA', 510: u'TER VINCULADOS A NUEVA. ZELANDA', 511: u'TER. VINCULADOS A ESTADOS UNIDOS'}

    # TODO: crear tabla 'moneda(id,ds,iso)' en la base de datos...
    monedas_ds = {'DOL': u'USD: Dólar', 'PES': u'ARS: Pesos', '010': u'MXN: Pesos Mejicanos', '011': u'UYU: Pesos Uruguayos', '012': u'BRL: Real', '014': u'Coronas Danesas', '015': u'Coronas Noruegas', '016': u'Coronas Suecas', '019': u'JPY: Yens', '018': u'CAD: D\xf3lar Canadiense', '033': u'CLP: Peso Chileno', '056': u'Forint (Hungr\xeda)', '031': u'BOV: Peso Boliviano', '036': u'Sucre Ecuatoriano', '051': u'D\xf3lar de Hong Kong', '034': u'Rand Sudafricano', '053': u'D\xf3lar de Jamaica', '057': u'Baht (Tailandia)', '043': u'Balboas Paname\xf1as', '042': u'Peso Dominicano', '052': u'D\xf3lar de Singapur', '032': u'Peso Colombiano', '035': u'Nuevo Sol Peruano', '061': u'Zloty Polaco', '060': u'EUR: Euro', '063': u'Lempira Hondure\xf1a', '062': u'Rupia Hind\xfa', '064': u'Yuan (Rep. Pop. China)', '009': u'Franco Suizo', '025': u'Dinar Yugoslavo', '002': u'USD: D\xf3lar Libre EEUU', '027': u'Dracma Griego', '026': u'D\xf3lar Australiano', '007': u'Florines Holandeses', '023': u'VEB: Bol\xedvar Venezolano', '047': u'Riyal Saudita', '046': u'Libra Egipcia', '045': u'Dirham Marroqu\xed', '044': u'C\xf3rdoba Nicarag\xfcense', '029': u'G\xfcaran\xed', '028': u'Flor\xedn (Antillas Holandesas)', '054': u'D\xf3lar de Taiwan', '040': u'Lei Rumano', '024': u'Corona Checa', '030': u'Shekel (Israel)', '021': u'Libra Esterlina', '055': u'Quetzal Guatemalteco', '059': u'Dinar Kuwaiti'}

    ivas_ds = {3: '0%', 4: '10.5%', 5: '21%', 6: '27%'}

    if fact['motivo'] and fact['motivo']<>'00':
        motivos_ds = u"Irregularidades observadas por AFIP (F136): %s" % fact['motivo']
    #elif HOMO and 'wsaahomo' in wsaa_url:
    #    motivos_ds = u"Ejemplo Sin validez fiscal - Homologación - Testing"
    else:
        motivos_ds = ""
        
    # determino tipo de comprobante, letra y número con prefijo
    tipos_fact = { (1, 6, 11, 19): 'Factura', (2, 7, 12, 20): 'Nota de Débito', 
        (3, 8, 13, 21): 'Nota de Crédito',
        (4, 9): 'Recibo', (10,): 'Notas de Venta al contado', 
        (60, 61): 'Cuenta de Venta y Líquido producto',
        (63, 64): 'Liquidación',
        (39, 40): '???? (R.G. N° 3419)'}
    letras_fact = {(1, 2, 3, 4, 5, 39, 60, 63): 'A',
                   (6, 7, 8, 9, 10, 40, 61, 64): 'B',
                   (11, 12, 13): 'C',
                   (19, 20, 21): 'E',
                }
    def fmt_fact(tipo_cbte, punto_vta, cbte_nro):
        n = "%04d-%08d" % (int(punto_vta), int(cbte_nro))
        for k,v in tipos_fact.items():
            if int(int(tipo_cbte)) in k:
                t = v
        for k,v in letras_fact.items():
            if int(int(tipo_cbte)) in k:
                l = v
        return t, l, n

    tipo_fact, letra_fact, numero_fact = fmt_fact(fact['tipo_cbte'], fact['punto_vta'], fact['cbte_nro'])
    
    if fact['tipo_cbte'] in (19,20,21):
        tipo_fact_ex = tipo_fact + " de Exportación"
    else:
        tipo_fact_ex = tipo_fact 

    # si se especifica formato, lo leo desde la base
    if '--test' in sys.argv:
        import pickle
        fields = pickle.load(open("formato.pkl"))
        #import pdb; pdb.set_trace()
    elif conexion and 'formato_id' in fact and fact['formato_id'] and int(fact['formato_id'])!=0:
        if DEBUG: print "leyendo formato ", fact['formato_id']
        cur = conexion.cursor()
        execute(cur, "SELECT * FROM formatos_pdf WHERE formato_id = ?", [fact['formato_id']]) 
        fields = []
        for row in cur.fetchall():
            dic = {}
            for i, k in enumerate(cur.description):
                dic[k[0]] = row[i]
            fields.append(dic)
        print fields
    else:
        fields = []
    
    # genero el renderizador con propiedades del PDF
    f = Template(elements=fields, 
             format=conf_fact.get('papel','A4'), 
             orientation=conf_fact.get("orientacion", 'portrait'),             
             title="%s %s %s" % (tipo_fact, letra_fact, numero_fact),
             author="CUIT %s" % cuit,
             subject="CAE %s" % fact['cae'],
             keywords="AFIP Factura Electrónica", ##str(fact),
             creator='fe.py %s (http://www.PyAfipWs.com.ar)' % __version__,)
    # cargar formato
    if not fields:
        f.parse_csv(infile=conf_fact.get('formato','factura.csv'),delimiter=";")

    if HOMO:
        field = {
                'name': 'homo', 
                'type': 'T', 
                'x1': 150, 'y1': 350, 'x2': 0, 'y2': 0, 
                'font': "Arial", 'size': 70, 'rotate': 45,
                'bold': True, 'italic': False, 'underline': False, 
                'foreground': 0xC0C0C0, 'background': 0xFFFFFF,
                'align': "L", 'text': "HOMOLOGACION", 'priority': -1}
        f.elements.append(field)

    # configuración específica
    qty_pos = conf_fact.get('cant_pos','izq')     # posición cantidad (izq/der)
    imp_pos = conf_fact.get('imp_pos','inf')      # posición importes (sup/inf)
    
    # dividir y contar líneas:
    lineas = 0
    li_items = []
    for it in fact['Items']:
        qty = qty_pos=='izq' and it['Item']['qty'] or None
        codigo = it['Item']['codigo']
        umed = it['Item']['umed']
        ##if DEBUG: print "dividiendo", it['Item']['ds']
        ds = it['Item']['ds']
        if 'obs' in it['Item'] and it['Item']['obs']:
            ds = ds + '\n' + it['Item']['obs']  
        # divido la descripción (simil célda múltiple de PDF) 
        n_li = 0
        for ds in f.split_multicell(ds, 'Item.Descripcion01'):
            ##if DEBUG: print "multicell", ds
            # agrego un item por linea (sin precio ni importe):
            li_items.append(dict(codigo=codigo, ds=ds, qty=qty, umed=umed, precio=None, imp_total=None))
            # limpio cantidad y código (solo en el primero)
            umed = qty = codigo = None
            n_li += 1
        # asigno el precio a la última línea del item 
        if imp_pos == "sup":
            i = -n_li           # muestro los importes en el primer renglón
        else:
            i = -1              # muestro los importes en el último renglón
        li_items[i].update(imp_total = it['Item']['imp_total'],
                            qty = (n_li==1 or qty_pos=='der') and it['Item']['qty'] or None,
                            precio = it['Item']['precio'],
                            bonif = it['Item'].get('bonif'),
                            iva_id = it['Item'].get('iva_id'), imp_iva = it['Item'].get('imp_iva'),
                            dato_a = it['Item'].get('dato_a'), dato_b = it['Item'].get('dato_b'),
                            dato_c = it['Item'].get('dato_c'), dato_d= it['Item'].get('dato_d'),
                            dato_e = it['Item'].get('dato_d'),
                            )

    # divido las observaciones por linea:
    if fact['obs'] and not f.has_key('obs') and not f.has_key('ObservacionesGenerales1'):
        obs="\n<U>Observaciones:</U>\n\n" + fact['obs']
        for ds in f.split_multicell(obs, 'Item.Descripcion01'):
            li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, imp_total=None))
    if fact['obs_comerciales'] and not f.has_key('obs_comerciales') and not f.has_key('ObservacionesComerciales1'):
        obs="\n<U>Observaciones Comerciales:</U>\n\n" + fact['obs_comerciales']
        for ds in f.split_multicell(obs, 'Item.Descripcion01'):
            li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, imp_total=None))

    # agrego permisos a descripciones (si corresponde)
    permisos =  [u'Codigo de Despacho %s - Destino de la mercadería: %s' % (
                 p['Permiso']['id_permiso'], paises.get(p['Permiso']['dst_merc'], p['Permiso']['dst_merc'])) 
                 for p in fact.get('Permisos',[])]
    if not f.has_key('permisos') and permisos:
        obs="\n<U>Permisos de Embarque:</U>\n\n" + '\n'.join(permisos)
        for ds in f.split_multicell(obs, 'Item.Descripcion01'):
            li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, imp_total=None))
    permisos_ds = ', '.join(permisos)

    # agrego comprobantes asociados
    cmps_asoc = [unicode('%s %s %s' % fmt_fact(c['Cmp_asoc']['cbte_tipo'], 
                                                c['Cmp_asoc']['cbte_punto_vta'], 
                                                c['Cmp_asoc']['cbte_nro']), 'latin1')
                  for c in fact.get('Cmps_asoc',[])]
    if not f.has_key('cmps_asoc') and cmps_asoc:
        obs="\n<U>Comprobantes Asociados:</U>\n\n" + '\n'.join(cmps_asoc)
        for ds in f.split_multicell(obs, 'Item.Descripcion01'):
            li_items.append(dict(codigo=None, ds=ds, qty=None, umed=None, precio=None, imp_total=None))
    cmps_asoc_ds = ', '.join(permisos)

    # calcular cantidad de páginas:
    lineas = len(li_items)
    lineas_max = int(conf_fact.get('lineas_max', "24"))
    if lineas_max>0:
        hojas = lineas / (lineas_max - 1)
        if lineas % (lineas_max - 1): hojas = hojas + 1
    else:
        hojas = 1

    copias = {1: 'Original', 2: 'Duplicado', 3: 'Triplicado'}

    num_copias = int(conf_fact.get('copias', 1))
    for copia in range(1, num_copias+1):
        
        # completo campos y hojas
        for hoja in range(1, hojas+1):
            f.add_page()
            f.set('copia', copias.get(copia, "Adicional %s" % copia))
            f.set('hoja', str(hoja))
            f.set('hojas', str(hojas))
            f.set('pagina', 'Pagina %s de %s' % (hoja, hojas))
            if hojas>1 and hoja<hojas:
                s = 'Continúa en hoja %s' % (hoja+1)
            else:
                s = ''
            f.set('continua', s)
            f.set('Item.Descripcion%02d' % (lineas_max+1), s)
                
            if DEBUG: print u"generando página %s de %s" % (hoja, hojas)
            
            # establezco campos según configuración:
            for k,v in conf_pdf.items():
                f.set(k,v)

            # establezco campos según tabla encabezado:
            for k,v in fact.items():
                f.set(k,v)

            f.set('Numero', numero_fact)
            f.set('Fecha', fmtdate(fact['fecha_cbte']))
            f.set('Vencimiento', fmtdate(fact['fecha_venc_pago']))
            
            f.set('LETRA', letra_fact)
            f.set('TipoCBTE', "COD.%02d" % int(fact['tipo_cbte']))

            f.set('Comprobante.L', tipo_fact)
            f.set('ComprobanteEx.L', tipo_fact_ex)

            if fact['fecha_serv_desde']:
                f.set('Periodo.Desde', fmtdate(fact['fecha_serv_desde']))
                f.set('Periodo.Hasta', fmtdate(fact['fecha_serv_hasta']))
            else:
                for k in 'Periodo.Desde', 'Periodo.Hasta', 'PeriodoFacturadoL':
                    f.set(k, '')

            f.set('Cliente.Nombre', fact.get('nombre', fact.get('nombre_cliente')))
            f.set('Cliente.Domicilio', fact.get('domicilio', fact.get('domicilio_cliente')))
            f.set('Cliente.Localidad', fact.get('localidad_cliente'))
            f.set('Cliente.Provincia', fact.get('provincia_cliente'))
            f.set('Cliente.Telefono', fact.get('telefono_cliente'))
            f.set('Cliente.IVA', fact.get('categoria', fact.get('id_impositivo')))
            f.set('Cliente.CUIT', fmtcuit(str(fact['nro_doc'])))
            f.set('Cliente.TipoDoc', {'80':'CUIT:','86':'CUIL:','96':'DNI:'}.get(str(fact['tipo_doc']), ""))
            f.set('Cliente.Observaciones', fact['obs_comerciales'])
            f.set('Cliente.PaisDestino', paises.get(fact['dst_cmp'], fact['dst_cmp']) or '')

            if fact['moneda_id']:
                f.set('moneda_ds', monedas_ds.get(fact['moneda_id'],''))
            else:
                for k in 'moneda.L', 'moneda_id', 'moneda_ds', 'moneda_ctz.L', 'moneda_ctz':
                    f.set(k, '')

            if not fact['incoterms']:
                for k in 'incoterms.L', 'incoterms', 'incoterms_ds':
                    f.set(k, '')

            li = 0
            k = 0
            subtotal = Decimal("0.00")
            descuento = Decimal("0.00")
            for it in li_items:
                k = k + 1
                if k > hoja * (lineas_max - 1):
                    break
                if it['imp_total'] and str(it.get('umed',0)) != '99':
                    subtotal += Decimal("%.6f" % it['imp_total'])
                elif str(it.get('umed', 0)) == '99':
                    descuento += Decimal("%.6f" % it['imp_total'])
                if it.get('bonif') is not None:
                    descuento += Decimal("%.6f" % it['bonif'])

                if k > (hoja - 1) * (lineas_max - 1):
                    if DEBUG: print "it", it
                    li += 1
                    umed0 = str(it.get('umed',"")) == '0'
                    if it['qty'] is not None and not umed0:
                        f.set('Item.Cantidad%02d' % li, fmtqty(it['qty']))
                    if it['codigo'] is not None:
                        f.set('Item.Codigo%02d' % li, it['codigo'])
                    if it['umed'] is not None:
                        f.set('Item.Umed%02d' % li, umeds_ds[it['umed']])
                    f.set('Item.Descripcion%02d' % li, it['ds'])
                    if it['precio'] is not None and not umed0:
                        f.set('Item.Precio%02d' % li, fmtpre(it['precio']))
                    if it['imp_total'] is not None and not umed0:
                        f.set('Item.Importe%02d' % li, fmtnum(it['imp_total']))
                    # iva y bonificacion
                    if    letra_fact=="B":
                        f.set('Item.IvaId%02d' % li, "")
                        f.set('Item.AlicuotaIva%02d' % li, "")
                        f.set('Item.ImporteIva%02d' % li, "")
                    else:
                        if it.get('iva_id') is not None and not umed0 and letra_fact=="A":
                            f.set('Item.IvaId%02d' % li, it['iva_id'])
                            f.set('Item.AlicuotaIva%02d' % li, ivas_ds.get(int(it['iva_id'])))
                        if it.get('imp_iva') is not None and not umed0:
                            f.set('Item.ImporteIva%02d' % li, fmtpre(it['imp_iva']))
                    if it.get('bonif') is not None and not umed0:
                        f.set('Item.Bonif%02d' % li, fmtpre(it['bonif']))
                    # datos adicionales de items
                    for adic in ['dato_a', 'dato_b', 'dato_c', 'dato_d', 'dato_e']:
                        if adic in it:
                            f.set('Item.%s%02d' % (adic, li), it[adic])

            if hojas == hoja:
                # última hoja, imprimo los totales
                li += 1

                if not descuento and 'descuento' in fact and fact['descuento']:
                    descuento = Decimal("%.6f" % float(fact['descuento']))
                f.set('descuento', fmtimp(descuento))
                subtotal -= descuento
                f.set('subtotal', fmtimp(subtotal))

                f.set('imp_neto', fmtimp(fact['imp_neto']))
                f.set('impto_liq', fmtimp(fact['impto_liq']))
                f.set('imp_total', fmtimp(fact['imp_total']))

                f.set('IMPTO_PERC', fmtimp(fact['impto_perc']))
                f.set('IMP_OP_EX', fmtimp(fact['imp_op_ex']))
                f.set('IMP_IIBB', fmtimp(fact['imp_iibb']))
                f.set('IMPTO_PERC_MUN', fmtimp(fact['impto_perc_mun']))
                f.set('IMP_INTERNOS', fmtimp(fact['imp_internos']))
                f.set('IMP_TRIB', fmtnum(fact.get('imp_trib',0)))

                li = 0
                for tributo in fact.get('Tributos', []):
                    it = tributo['Tributo']
                    li += 1
                    if it.get(DESC1) is not None:
                        f.set('Tributo.Descripcion%02d' % li, it[DESC1])
                    if it['alic'] is not None:
                        f.set('Tributo.Alicuota%02d' % li, fmtnum(it['alic']) + "%")
                    if it['base_imp'] is not None:
                        f.set('Tributo.BaseImp%02d' % li, fmtnum(it['base_imp']))
                    if it['importe'] is not None:
                        f.set('Tributo.Importe%02d' % li, fmtnum(it['importe']))

                if letra_fact=='A':
                    f.set('NETO', fmtimp(fact['imp_neto']))
                    f.set('IVALIQ', fmtimp(fact['impto_liq']))
                    f.set('LeyendaIVA',"")
                    
                    for it in fact.get('Ivas', []):
                        iva = it['Iva']
                        a = {3: '0', 4: '10.5', 5: '21', 6: '27'}[int(iva['iva_id'])]
                        f.set('IVA%s' % a, fmtnum(iva['importe']))
                        f.set('IVA%s.L' % a, "I.V.A. %s %%" % a)
                else:
                    f.set('NETO.L',"")
                    f.set('IVA.L',"")
                    f.set('Item.AlicuotaIVA',"")
                    f.set('LeyendaIVA', "")
                    ##del f.elements['Linea.IVA']
                    for a in {3: '0', 4: '10.5', 5: '21', 6: '27'}.values():
                        f.set('IVA%s' % a, "")
                        f.set('IVA%s.L' % a, "")

                f.set('Total.L', 'Total:')
                f.set('TOTAL', fmtimp(fact['imp_total']))
            else:
                for k in ('imp_neto', 'impto_liq', 'imp_total', 'impto_perc', 'imp_trib',
                          'imp_op_ex', 'IMP_IIBB', 'imp_iibb', 'impto_perc_mun', 'imp_internos',
                          'NETO', 'IVA21', 'IVA10.5', 'IVA27', 'IVA10.5.L', 'IVA21.L', 'IVA27.L'):
                    f.set(k,"")
                f.set('NETO.L',"")
                f.set('IMP_TRIB.L',"")
                f.set('IVA.L',"")
                f.set('LeyendaIVA', "")
                f.set('Total.L', 'Subtotal:')
                f.set('TOTAL', fmtimp(subtotal))

            f.set('cmps_asoc_ds', cmps_asoc_ds)
            f.set('permisos_ds', permisos_ds)

            f.set('motivos_ds', motivos_ds)
            if not motivos_ds:
                f.set('motivos_ds.L', "")
            f.set('CAE', fact['cae'])
            f.set('CAE.Vencimiento', fmtdate(fact['fecha_vto']))
            if fact['cae'] and fact['cae']!="NULL" and str(fact['cae']).isdigit() and fact['fecha_vto'] and str(fact['fecha_vto']).isdigit():
                barras = ''.join([cuit, "%02d" % fact['tipo_cbte'], "%04d" % fact['punto_vta'], 
                    str(fact['cae']), fact['fecha_vto']])
                barras = barras + digito_verificador_modulo10(barras)
            else:
                barras = ""

            f.set('CodigoBarras', barras)
            f.set('CodigoBarrasLegible', barras)

            if f.has_key('observacionesgenerales1'):
                for i, txt in enumerate(f.split_multicell(fact['obs'], 'ObservacionesGenerales1')):
                    f.set('ObservacionesGenerales%d' % (i+1), txt)

            if f.has_key('observacionescomerciales1'):
                for i, txt in enumerate(f.split_multicell(fact['obs_comerciales'], 'ObservacionesComerciales1')):
                    f.set('ObservacionesComerciales%d' % (i+1), txt)
                    
            if f.has_key('motivos_ds1') and motivos_ds:
                if int(fact['tipo_cbte']) in (1,2,3): 
                    msg_no_iva = u"El IVA discriminado no puede computarse como Crédito Fiscal (RG2485/08 Art. 30 inc. c)."
                    if not f.has_key('leyenda_credito_fiscal'):
                        motivos_ds += u"\n%s" % msg_no_iva
                    else:
                        f.set('leyenda_credito_fiscal', msg_no_iva)

                for i, txt in enumerate(f.split_multicell(motivos_ds, 'motivos_ds1')):
                    f.set('motivos_ds%d' % (i+1), txt)

            # evaluo fórmulas (expresiones python)
            for field in f.elements:
                if field['name'].startswith("="):
                    formula = field['text']
                    if DEBUG: print "**** formula: %s %s" % (field, formula)
                    try:
                        value = eval(formula,dict(fact=fact))
                        f.set(field['name'], value)
                        if DEBUG: print "set(%s,%s)" % (field, value)
                    except Exception, e:
                        #import pdb; pdb.set_trace()
                        print "Error al evaluar %s formula '%s': %s" % (field, formula, e)
                        #raise RuntimeError("Error al evaluar %s formula '%s': %s" % (field, formula, e))

    if not 'pdf' in fact or not fact['pdf']:
        # genero el nombre de archivo según datos de factura
        fs = conf_fact.get('archivo','numero').split(",")
        it = fact.copy()
        it['tipo'] = tipo_fact.replace(" ", "_")
        it['letra'] = letra_fact
        it['numero'] = numero_fact
        it['mes'] = fact['fecha_cbte'][4:6]
        it['año'] = fact['fecha_cbte'][0:4]
        it['mesaño'] = fact['fecha_cbte'][0:6]
        d = os.path.join(conf_fact.get('directorio', "."), it['fecha_cbte'])
        clave_subdir = conf_fact.get('subdirectorio','')
        if clave_subdir:
            d = os.path.join(d, it[clave_subdir])
        if not os.path.isdir(d):
            os.makedirs(d)
        fn = ''.join([str(it.get(ff,ff)) for ff in fs])
        fn = fn.decode(CHARSET).encode('ascii', 'replace').replace('?','_')
        archivo = os.path.join(d, "%s.pdf" % fn)
    else:
        archivo = fact['pdf']
    f.render(archivo)
    return archivo

def enviar_mail(item, archivo):
    global smtp
    if item['email']:
        msg = MIMEMultipart()
        msg['Subject'] = conf_mail['motivo'].replace("NUMERO",str(item['cbte_nro']))
        msg['From'] = conf_mail['remitente']
        msg['Reply-to'] = msg['From']
        msg['To'] = item['email']
        msg.preamble = 'Mensaje de multiples partes.\n'
        
        part = MIMEText(conf_mail['cuerpo'].replace("\v","\n"))
        msg.attach(part)
        
        part = MIMEApplication(open(archivo,"rb").read())
        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(archivo))
        msg.attach(part)

        if DEBUG: print "Enviando email: %s a %s" % (msg['Subject'], msg['To'])
        if not smtp:
            servidor = conf_mail['servidor']
            puerto = int(conf_mail.get('puerto', 25))
            if puerto != 465:
                smtp = smtplib.SMTP(servidor, puerto)
            else:
                # creo una conexión segura (SSL, no disponible en Python<2.6):
                smtp = smtplib.SMTP_SSL(servidor, puerto)
            if DEBUG:
                smtp.set_debuglevel(1)
            if puerto in (587, 777):
                # inicio una sesión segura (TLS)
                smtp.starttls()
            smtp.ehlo()
            auth = conf_mail.get('auth')
            if auth:
                smtp.esmtp_features["auth"] = auth
            usuario, clave = conf_mail.get('usuario'), conf_mail.get('clave')
            if usuario and clave:
                smtp.login(usuario, clave)
        smtp.sendmail(msg['From'], msg['To'], msg.as_string())
        

def esquema_sql():
    for tabla, formato in [('encabezado', ENCABEZADO), ('detalle', DETALLE), ('permiso', PERMISO), ('cmp_asoc', CMP_ASOC), ('iva', IVA), ('tributo', TRIBUTO)]:
        sql = []
        sql.append("CREATE TABLE %s (" % tabla)
        if tabla!='encabezado':
            # agrego id como fk
            id = [('id', 15, N)]
        else:
            id = []
        for (clave, longitud, tipo) in id+formato:
            clave_orig = clave
            if tabla == 'encabezado':
                clave = conf_encabezado.get(clave, clave)
            if tabla == 'detalle':
                clave = conf_detalle.get(clave, clave)
            if tabla == 'iva':
                clave = conf_iva.get(clave, clave)
            if tabla == 'tributo':
                clave = conf_tributo.get(clave, clave)
            if tabla == 'cmp_asoc':
                clave = conf_cmp_asoc.get(clave, clave)
            if tabla == 'permiso':
                clave = conf_permiso.get(clave, clave)
            if isinstance(longitud, (tuple, list)):
                longitud, decimales = longitud
            else:
                decimales = 2
            sql.append ("    %s %s %s%s%s" % (
                clave, 
                {N: 'INTEGER', I: 'NUMERIC', A: 'VARCHAR'}[tipo], 
                {I: "(%s, %s)" % (longitud, decimales), A: '(%s)' % longitud, N: ''}[tipo],
                clave == 'id' and (tabla=='encabezado' and " PRIMARY KEY" or " FOREING KEY encabezado") or "",
                formato[-1][0]!=clave_orig and "," or ""))
        sql.append(")")
        sql.append(";")
        if DEBUG: print '\n'.join(sql)
        yield '\n'.join(sql)


if __name__ == "__main__":
    # establecer el encoding de la salida (cuando es a un archivo)
    import sys, codecs, locale, traceback
    if True or sys.stdout.encoding is None:
        class SafeWriter:
            def __init__(self, target):
                self.target = target
                self.encoding = 'utf-8'
                self.errors = 'replace'
                self.encode_to = 'latin-1'
            def write(self, s):
                self.target.write(self.intercept(s))        
            def flush(self):
                self.target.flush()
            def intercept(self, s):
                if not isinstance(s, unicode):
                    s = s.decode(self.encode_to, self.errors)
                return s.encode(self.encoding, self.errors)

        sys.stdout = SafeWriter(sys.stdout)
        #sys.stderr = SafeWriter(sys.stderr)
        print "Encodign in %s" % locale.getpreferredencoding()

    client = None
    smtp = None
    cnn = None
    fact_id = None
    try:

        if '--ayuda' in sys.argv:
            ##print LICENCIA
            print AYUDA
            sys.exit(0)
        
        DEBUG = '--debug' in sys.argv
        
        if DEBUG: print "VERSION:",__version__

        if len(sys.argv)>1 and not sys.argv[1].startswith("--"):
            CONFIG_FILE = sys.argv.pop(1)
        if DEBUG: print "CONFIG_FILE:", CONFIG_FILE
        
        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        cert = config.get('WSAA','CERT')
        privatekey = config.get('WSAA','PRIVATEKEY')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = wsaa.WSAAURL

        if config.has_option('WSAA','TTL'):
            wsaa_ttl = int(config.get('WSAA','TTL'))
        else:
            wsaa_ttl = 60*60*5 # 5 hs

        if config.has_option('WSAA','TIMEOUT'):
            TIMEOUT = float(config.get('WSAA','TIMEOUT'))
            print "TIMEOUT = ", TIMEOUT

        CACERT = config.has_option('WSAA', 'CACERT') and config.get('WSAA', 'CACERT') or None

        if config.has_option('WSFE','URL') and not HOMO:
            wsfe_url = config.get('WSFE','URL')
        else:
            wsfe_url = wsfe.WSFEURL
        if config.has_option('WSFEX','URL') and not HOMO:
            wsfex_url = config.get('WSFEX','URL')
        else:
            wsfex_url = wsfex.WSFEXURL
        if config.has_option('WSFEv1','URL') and not HOMO:
            wsfev1_url = config.get('WSFEv1','URL')
        else:
            wsfev1_url = ""
        if config.has_option('WSFEXv1','URL') and not HOMO:
            wsfexv1_url = config.get('WSFEXv1','URL')
        else:
            wsfexv1_url = ""
        if config.has_option('WSMTXCA','URL') and not HOMO:
            wsmtx_url = config.get('WSMTXCA','URL')
        else:
            wsmtx_url = ""

        if config.has_option('WSFEv1','REPROCESAR'):
            wsfev1_reprocesar = config.get('WSFEv1','REPROCESAR') == 'S'
        else:
            wsfev1_reprocesar = None
        if config.has_option('WSMTXCA','REPROCESAR'):
            wsmtx_reprocesar = config.get('WSMTXCA','REPROCESAR') == 'S'
        else:
            wsmtx_reprocesar = None

        if config.has_section('FACTURA'):
            conf_fact = dict(config.items('FACTURA'))
        else:
            conf_fact = {}

        if config.has_section('PROXY'):
            proxy_dict = dict(("proxy_%s" % k,v) for k,v in config.items('PROXY'))
            proxy_dict['proxy_port'] = int(proxy_dict['proxy_port'])
        else:
            proxy_dict = {}
            
        if config.has_section('BASE_DATOS'):
            conf_db = dict(config.items('BASE_DATOS'))
        else:
            conf_db = {}

        if config.has_section('ENCABEZADO'):
            conf_encabezado = dict(config.items('ENCABEZADO'))
        else:
            conf_encabezado = dict([(k, k) for k,t,n in ENCABEZADO])
        conf_encabezado_rev = dict([(v, k) for k, v in conf_encabezado.items()])

        if config.has_section('DETALLE'):
            conf_detalle = dict(config.items('DETALLE'))
        else:
            conf_detalle = dict([(k, k) for k,t,n in DETALLE])
            conf_detalle['id'] = 'id'
        conf_detalle_rev = dict([(v, k) for k, v in conf_detalle.items()])

        if config.has_section('IVA'):
            conf_iva = dict(config.items('IVA'))
        else:
            conf_iva = dict([(k, k) for k,t,n in IVA])
            conf_iva['id'] = 'id'
        conf_iva_rev = dict([(v, k) for k, v in conf_iva.items()])

        if config.has_section('TRIBUTO'):
            conf_tributo = dict(config.items('TRIBUTO'))
        else:
            conf_tributo = dict([(k, k) for k,t,n in TRIBUTO])
            conf_tributo['id'] = 'id'
        conf_tributo_rev = dict([(v, k) for k, v in conf_tributo.items()])

        if config.has_section('CMP_ASOC'):
            conf_cmp_asoc = dict(config.items('CMP_ASOC'))
        else:
            conf_cmp_asoc = dict([(k, k) for k,t,n in CMP_ASOC])
            conf_cmp_asoc['id'] = 'id'
        conf_cmp_asoc_rev = dict([(v, k) for k, v in conf_cmp_asoc.items()])

        if config.has_section('PERMISO'):
            conf_permiso = dict(config.items('PERMISO'))
        else:
            conf_permiso = dict([(k, k) for k,t,n in PERMISO])
            conf_permiso['id'] = 'id'
        conf_permiso_rev = dict([(v, k) for k, v in conf_permiso.items()])

        conf_pdf = dict(config.items('PDF'))
        conf_mail = dict(config.items('MAIL'))

        if config.has_section('TXT'):
            conf_txt = dict(config.items('TXT'))
            for l, cfg in  ((IMPTE, 'importe'), (PRECIO, 'precio'), (SUBTOTAL, 'subtotal')):
                del l[1]
                del l[0]
                l.append(int(conf_txt.get("%s.long" % cfg)))
                l.append(int(conf_txt.get("%s.dec" % cfg)))
                if DEBUG: print "Usando ", cfg, l

        if config.has_section('XML'):
            conf_xml = dict(config.items('XML'))
            XML_PATH=conf_xml.get("path")
            if DEBUG: print "Usando XML_PATH", XML_PATH

        XML = '--xml' in sys.argv
        PDF = '--pdf' in sys.argv

        if '--wsfe'in sys.argv:
            WEBSERVICE = "wsfe"
            cuit = config.get('WSFE','CUIT')
            entrada = config.get('WSFE','ENTRADA')
            salida = config.get('WSFE','SALIDA')
        elif '--wsfev1'in sys.argv:
            WEBSERVICE = "wsfev1"
            cuit = config.get('WSFEv1','CUIT')
            entrada = config.get('WSFEv1','ENTRADA')
            salida = config.get('WSFEv1','SALIDA')
        elif '--wsfex'in sys.argv:
            WEBSERVICE = "wsfex"
            cuit = config.get('WSFEX','CUIT')
            entrada = config.get('WSFEX','ENTRADA')
            salida = config.get('WSFEX','SALIDA')
        elif '--wsfexv1'in sys.argv:
            WEBSERVICE = "wsfexv1"
            cuit = config.get('WSFEXv1','CUIT')
            entrada = config.get('WSFEXv1','ENTRADA')
            salida = config.get('WSFEXv1','SALIDA')
        elif '--wsmtx'in sys.argv:
            WEBSERVICE = "wsmtx"
            cuit = config.get('WSMTXCA','CUIT')
            entrada = config.get('WSMTXCA','ENTRADA')
            salida = config.get('WSMTXCA','SALIDA')
        else:
            raise RuntimeError("No se especifica webservice (--wsfe, --wsfev1, --wsfex, --wsfexv1, --wsmtx)")

        if DEBUG:
            print "wsaa_url %s\nwsfex_url %s\nwsfev1_url %s" % (wsaa_url, wsfex_url, wsfev1_url)
            if proxy_dict: print "proxy_dict=",proxy_dict

        if '--esquema' in sys.argv:
            print "Esquema:"
            for sql in esquema_sql():
                print sql
            sys.exit(0)

        if '--formato' in sys.argv:
            print "Formato:"
            
            ##for msg, formato in [('Encabezado', ENCABEZADO), ('Detalle', DETALLE), ('Permiso', PERMISO), ('Comprobante Asociado', CMP_ASOC)]:
            ##    comienzo = 1
            ##    print "%s: %s" % (msg, ', '.join([clave for (clave, longitud, tipo) in formato]))
            
            for msg, formato in [('Encabezado', ENCABEZADO), ('Detalle', DETALLE), ('Permiso', PERMISO), ('Comprobante Asociado', CMP_ASOC), ('Iva', IVA), ('Tributo', TRIBUTO)]:
                comienzo = 1
                print "== %s ==" % msg
                for (clave, longitud, tipo) in formato:
                    if msg == 'Encabezado' and conf_encabezado:
                        clave = conf_encabezado.get(clave, clave)
                    if msg == 'Detalle' and conf_detalle:
                        clave = conf_detalle.get(clave, clave)
                    if msg == 'Iva' and conf_iva:
                        clave = conf_iva.get(clave, clave)
                    if msg == 'Tributo' and conf_tributo:
                        clave = conf_tributo.get(clave, clave)
                    print " * %s (Tipo: %s, Comienzo: %s Longitud: %s)" % (
                        clave, tipo, comienzo, str(longitud))
                    comienzo += isinstance(longitud, (tuple, list)) and longitud[0] or longitud
            sys.exit(0)

        if '--ini' in sys.argv:
            print "Formato INI:"
                        
            for msg, formato in [('ENCABEZADO', ENCABEZADO), ('DETALLE', DETALLE), ('PERMISO', PERMISO), ('CMP_ASOC', CMP_ASOC), ('IVA', IVA), ('TRIBUTO', TRIBUTO)]:
                comienzo = 1
                print "[%s]" % msg
                for (clave, longitud, tipo) in formato:
                    print "%s = %s" % (clave, clave)
            sys.exit(0)

        def execute(cur, sql, params=None):
            if params is None:
                return cur.execute(sql)
            else:
                return cur.execute(sql, params)
        
        # conectarse a la base:
        if conf_db and 'driver' in conf_db and conf_db['driver']!='sqlite':
            if conf_db['driver']=='kinterbasdb':
                import kinterbasdb
                kinterbasdb.init(type_conv=200)
                cnn_params = dict(dsn=conf_db.get('dsn'), 
                                  database=conf_db.get('database'), 
                                  host=conf_db['server'], port=conf_db.get('port'), 
                                  user=conf_db['uid'], password=conf_db['pwd'],
                                  charset='UNICODE_FSS', #'UTF8',
                                  )
                if DEBUG: print "conectado %s " % (cnn_params,)
                cnn = kinterbasdb.connect(**cnn_params )
                tpb = ( kinterbasdb.isc_tpb_write + kinterbasdb.isc_tpb_read_committed + kinterbasdb.isc_tpb_rec_version)
                cnn.default_tpb= tpb
            elif conf_db['driver']=='pg8000':
                import pg8000
                pg8000.DBAPI.paramstyle = "qmark"
                cnn = pg8000.DBAPI.connect(
                    host=conf_db['server'],
                    database=conf_db.get('database'), 
                    user=conf_db['uid'], password=conf_db['pwd'],
                    port=conf_db.get('port', 5432), 
                    ssl=False,
                    )
                #cnn._client_encoding="latin1"
                cnn.cursor().execute("SET CLIENT_ENCODING TO 'win1252'")
                cnn.commit()
            elif conf_db['driver']=='cx_oracle':
                import cx_Oracle
                conn_str = u'%(uid)s/%(pwd)s@%(server)s:%(port)s/%(database)s' % conf_db
                #cx_Oracle.paramstyle="qmark"   # named!
                cnn = cx_Oracle.connect(conn_str)

                def execute(cur, sql, params=[]):
                    # convertir parametros
                    s = ""
                    i = 0
                    for c in sql:
                        if c != '?':
                            s += c
                        else:
                            s += ":%s" % chr(65+i)
                            i += 1
                        if i > 90: raise
                    p = dict([(chr(65+i), v) for i, v in enumerate(params)])
                    if True:
                        print "ORACLE consulta reescrita", s
                        print "ORACLE parametros", p
                    # evitar segv!!
                    import sys
                    sys.stdout.flush()
                    #raw_input()
                    (cur).execute(s, p)
            else:
                import pyodbc
                if DEBUG: print "db config %s ..." % conf_db
                cnn_strs = {
                    'pgsql': "Driver={PostgreSQL ANSI};SERVER=%(server)s;PORT=5432;DATABASE=%(database)s;UID=%(uid)s;PWD=%(pwd)s;CONNSETTINGS=SET Datestyle TO 'DMY'%%3bSET CLIENT_ENCODING TO 'WIN1252'%%3b;BOOLSASCHAR=0;TEXTASLONGVARCHAR=1;TrueIsMinus1=1;SSLMODE=prefer;",
                    'mssql': u'DRIVER={SQL Server};SERVER=%(server)s;DATABASE=%(database)s;UID=%(uid)s;PWD=%(pwd)s',
                    }
                if conf_db['driver'].lower() in cnn_strs:
                    cnn_str = cnn_strs[conf_db['driver'].lower()]
                else: # si el driver no figura, usar DSN
                    cnn_str = u'DSN=%(dsn)s;SERVER=%(server)s;DATABASE=%(database)s;UID=%(uid)s;PWD=%(pwd)s'
                cnn = pyodbc.connect(cnn_str % conf_db)
                if DEBUG: print "conectado %s " % (cnn_str % conf_db)
            if 'encabezado' in conf_db:
                SCHEMA['encabezado'] = conf_db['encabezado']
            if 'detalle' in conf_db:
                SCHEMA['detalle'] = conf_db['detalle']
            if 'cmp_asoc' in conf_db:
                SCHEMA['cmp_asoc'] = conf_db['cmp_asoc']
            if 'permiso' in conf_db:
                SCHEMA['permiso'] = conf_db['permiso']
            if 'iva' in conf_db:
                SCHEMA['iva'] = conf_db['iva']
            if 'tributo' in conf_db:
                SCHEMA['tributo'] = conf_db['tributo']
            if 'xml' in conf_db:
                SCHEMA['xml'] = conf_db['xml']
        else:
            import sqlite3
            if not 'database' in conf_db:
                if DEBUG: print "Creando base de datos en memoria y definiendo el esquema"
                database = ":memory:"
            else:
                database = conf_db['database']
            if DEBUG: print "conectando a sqlite: %s" % database
            cnn = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
            sqlite3.register_converter('numeric', Decimal)
            sqlite3.register_adapter(Decimal, lambda d: '%s' % d)
            cur = cnn.cursor()
            try:
                for sql in esquema_sql():
                    execute(cur, sql)
                cnn.commit()
            except sqlite3.OperationalError, e:
                if DEBUG: print str(e)
            finally:
                cur.close()
        
        if 'null' in conf_db:
            NULL = eval(conf_db['null'])
            if DEBUG: print "NULL = ", repr(NULL)
            CAE_NULL = NULL
            FECHA_VTO_NULL = NULL
            RESULTADO_NULL = NULL
        # instancio el cliente soap según el webservice:
        if WEBSERVICE == "wsfe":
            client = SoapClient(wsfe_url, action=wsfe.SOAP_ACTION, namespace=wsfe.SOAP_NS,
                            trace=DEBUG, exceptions=True, proxy = proxy_dict)
        elif WEBSERVICE == "wsfev1":
            client = wsfev1.WSFEv1()
            client.Conectar("",wsfev1_url, proxy=proxy_dict, timeout=TIMEOUT)
        elif WEBSERVICE == "wsfex":
            client = SoapClient(wsfex_url, action=wsfex.SOAP_ACTION, namespace=wsfex.SOAP_NS,
                            trace=DEBUG, exceptions=True, proxy = proxy_dict)
        elif WEBSERVICE == "wsfexv1":
            client = wsfexv1.WSFEXv1()
            client.Conectar("",wsfexv1_url, proxy=proxy_dict, timeout=TIMEOUT)
        elif WEBSERVICE == "wsmtx":
            client = wsmtx.WSMTXCA()
            client.Conectar("",wsmtx_url, proxy=proxy_dict, timeout=TIMEOUT)
        else:
            client = None
            
        if '--dummy' in sys.argv:
            print "Consultando estado de servidores..."
            if WEBSERVICE=='wsfe':
                print wsfe.dummy(client)
            elif WEBSERVICE=='wsfev1':
                print client.Dummy()
            elif WEBSERVICE=='wsfex':
                print wsfex.dummy(client)
            elif WEBSERVICE=='wsfexv1':
                print client.Dummy()
                
            sys.exit(0)

        # solicito acceso al webservice (WSAA):
        if WEBSERVICE:
            token, sign = autenticar(cert, privatekey, wsaa_url, WEBSERVICE, ttl=wsaa_ttl, proxy=proxy_dict)
            if WEBSERVICE in ('wsfev1', 'wsfexv1', 'wsmtx'):
                client.Token = token
                client.Sign = sign
                client.Cuit = cuit
            if WEBSERVICE == 'wsfev1' and wsfev1_reprocesar is not None:
                client.Reprocesar = wsfev1_reprocesar
            if WEBSERVICE == 'wsmtx' and wsmtx_reprocesar is not None:
                client.Reprocesar = wsmtx_reprocesar
        else:
            token, sign = '', ''

        informar_caea = '--informar_caea' in sys.argv
        
        if '--prueba' in sys.argv:
            # generar el archivo de prueba para la próxima factura
            simple = '--simple' in sys.argv
            fecha = date('Ymd')
            punto_vta = 2
            if WEBSERVICE in ('wsfe', 'wsfev1', 'wsmtx'):
                tipo_cbte = 1
                if WEBSERVICE=='wsfev1':
                    ult_cbte = -1    # pedirlo automáticamente
                    id = max_id(cnn) + 1
                    ctz = 1.00 # client.ParamGetCotizacion('PES') # WSFEv1 no devuelve cotizacion!
                elif WEBSERVICE=='wsmtx':
                    ult_cbte = client.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
                    if not ult_cbte:
                        ult_cbte = 0
                    ult_cbte = long(ult_cbte)
                    id = max_id(cnn) + 1
                    ctz = 1
                else:
                    ult_cbte = wsfe.recuperar_last_cmp(client, token, sign, cuit, punto_vta, tipo_cbte)
                    id = wsfe.ultnro(client, token, sign, cuit) + 1
                    ctz = 1
                dic = dict(
                    tipo_doc = 80, nro_doc = 33693450239,
                    presta_serv=1, fecha_serv_desde=fecha, fecha_serv_hasta=fecha,
                    domicilio_cliente='Balcarce 50',
                    id_impositivo='Consumidor Final',
                    moneda_id='PES', moneda_ctz=Decimal(ctz),
                    forma_pago='Cuenta Corriente',
                    incoterms='',
                    )
            else:
                tipo_cbte = 19
                if WEBSERVICE == 'wsfexv1':
                    ult_cbte = client.GetLastCMP(tipo_cbte, punto_vta)
                    if not ult_cbte:
                        ult_cbte = 0
                    ult_cbte = long(ult_cbte)
                    id = client.GetLastID() + 1
                else:
                    ult_cbte = wsfex.get_last_cmp(client, token, sign, cuit, tipo_cbte, punto_vta )
                    ult_cbte = int(ult_cbte[0])
                    id = int(wsfex.get_last_id(client, token, sign, cuit)[0]) + 1
                dic = dict(
                    tipo_doc = 80, nro_doc = 50000000016,
                    tipo_expo=1,
                    permiso_existente='N',
                    dst_cmp=203,
                    domicilio_cliente='Montevideo, UY',
                    id_impositivo='RUC 123123',
                    moneda_id='DOL',
                    moneda_ctz=3.85,
                    forma_pago='Taka taka',
                    incoterms='FOB',
                    incoterms_ds="Franco A Bordo",
                    idioma_cbte= '2',
                    )
            dic.update(dict(                    
                id=id,
                webservice=WEBSERVICE,
                fecha=fecha,
                fecha_cbte=fecha, fecha_venc_pago=fecha,
                obs_comerciales='observaciones comerciales...',
                obs='observaciones generales...',
                email='reingart@gmail.com',
                tipo_cbte=tipo_cbte, 
                punto_vta=punto_vta,
                cbte_nro=ult_cbte+1, 
                imp_total=Decimal("0.00"), imp_tot_conc=Decimal("0.00"), imp_neto=Decimal("0.00"),
                impto_liq=Decimal("0.00"), impto_liq_rni=Decimal("0.00"), imp_op_ex=Decimal("0.00"),
                dato_adicional1='datoa1',
                dato_adicional2='datoa2',
                dato_adicional3='datoa3',
                dato_adicional4='datoa4',
                dato_adicional5='datoa5', #'0999015500000011001000000000000000110001',
                dato_adicional6='datoa6',
                ))
            dic['nombre_cliente'] = 'Mariano Prueba'
            #dic['id_impositivo'] = 'Monotributo'
            dic['localidad_cliente'] = 'Capital'
            dic['provincia_cliente'] = 'Buenos Aires'
            dic['telefono_cliente'] = '4450-0716'
            ds = u"S" #Lore mipsumdolo rsitametco ñáéíóú nsectetur"
            if not simple:
                ds = ds.upper()*5
            factor = 1
            if WEBSERVICE=='wsfev1':
                imp_total = Decimal('131.00')*factor
            else:
                imp_total = Decimal('100.00')*factor
            imp_trib = Decimal('0')
            imp_op_ex = Decimal('0.00')
            imp_tot_conc = Decimal('0')
            imp_neto = Decimal('0')
            impto_liq = Decimal('0')
            dic['Items'] = [
                            #{'Item': dict(codigo="", qty=0, umed=0, 
                            #    precio=str(0.00), 
                            #    imp_total=str(0.00),
                            #    ds="Linea de Descripcion de prueba (umed=0)", id=str(id),
                            #    )},           
                            {'Item': dict(codigo="A123", qty=2, umed=1, 
                                u_mtx=1, cod_mtx="1", 
                                precio=Decimal(tipo_cbte==6 and Decimal("60.50") or Decimal("50.00"))*factor, 
                                imp_total=Decimal(WEBSERVICE=='wsmtx' and Decimal("121.00") or str("100.00"))*factor,
                                ds=ds * (simple and 3 or 30), id=str(id),
                                dato_a='datoa', dato_b='datob',
                                iva_id=5, imp_iva=Decimal("21.00")*factor,
                                obs="ABCD " * (simple and 3 or 1000), 
                                )}] # 30
            if WEBSERVICE in ('wsfev1', 'wsmtx'):
                dic['Ivas'] = [{'Iva': {'iva_id': 5, 'base_imp': Decimal("100.00")*factor, 'importe': Decimal("21.00")*factor}},
                               ]
                base_imp = Decimal("100.00")*factor
                ##if WEBSERVICE == 'wsfev1':
                ##    dic['Ivas'].append({'Iva': {'iva_id': 3, 'base_imp': Decimal("10.00"), 'importe': Decimal("0.00")}})
                ##    base_imp += Decimal("10")
                for iva in dic['Ivas']:
                    i = iva['Iva']
                    impto_liq += i['importe']
                    imp_neto += i['base_imp']
                tributos = [('Per.IIBB', Decimal("1.25")), ('Per.IVA', Decimal("5.0"))]
                dic['Tributos'] = []
                for ds, alic in tributos:
                    imp = base_imp*alic/Decimal("100.0")
                    imp_trib += imp
                    imp_total += imp
                    dic['Tributos'].append({'Tributo': {'tributo_id': 2, DESC: ds, 'base_imp': base_imp, 'alic': alic, 'importe': imp}})
                    
            if False: ###for i in range(1, simple and 3 or 76):
                qty = random.randint(1,10)
                precio = round(random.random()*100, IMPTE[1])
                imp_total += Decimal('%%.%df' % IMPTE[1] % (qty * precio))
                codigo = "%s%s%02d" % (chr(random.randint(65,90)), chr(random.randint(65,90)),i)
                dic['Items'].append(
                    {'Item': dict(codigo=codigo, umed=7,
                                  qty=qty, precio=str(precio), 
                                  imp_total=str(qty*precio),
                                  ds="%s: %s" % (i,ds), 
                                  id=str(id))})
            # actualizo el importe total
            imp_total = imp_neto + impto_liq + imp_trib + imp_op_ex + imp_tot_conc
            dic['imp_total'] = imp_total
            dic['imp_trib'] = imp_trib
            dic['imp_op_ex'] = imp_op_ex
            dic['imp_tot_conc'] = imp_tot_conc
            dic['imp_neto'] =  dic['imp_subtotal'] = Decimal("%.2f" % ((imp_total-imp_trib)/Decimal('1.21')))
            dic['impto_liq'] = Decimal("%.2f" % ((imp_total-imp_trib) - (imp_total-imp_trib)/Decimal('1.21')))
            if tipo_cbte in (20, 21):
                dic['Cmps_asoc'] = [{'Cmp_asoc': {'cbte_tipo': 19, 'cbte_punto_vta': 1, 'cbte_nro': 2}}]
            if 'permiso_existente' in dic and dic['permiso_existente']=='S':
                dic['Permisos'] = [{'Permiso': {'id_permiso': '99999AAXX999999A', 'dst_merc': '230'}},
                {'Permiso': {'id_permiso': '09052EC01006154G', 'dst_merc': '203'}},]
            if not simple:
                dic['obs']="Ius id vidit volumus mandamus, vide veritus democritum te nec. " * 15
                dic['obs_comerciales']="Blandit incorrupte quaerendum in quo, nibh impedit id vis. " * 33
            if informar_caea:
                dic['cae'] = '24463649615277'
                dic['fecha_vto'] = '20141130'
            escribir_facturas([dic], cnn)

        if '--test' in sys.argv:
            dic =  {'array_packlist_id': None, 'cbte_nro': 2, 'invoice_id': u'B0054-00000002D', 'incoterms_ds': u'FOB', 
                'imp_op_ex': None, 'cust_order_id': None, 'imp_trib': Decimal("12.59"), 
                'reproceso': u'', 'fecha_serv_desde': u'20110719', 'motivo': u'', 
                'descripcion_iva': u'Sujeto no Categorizado', 'permiso_existente': u'', 
                'id': 119578L, 'tipo_cbte': 7, 'impto_liq': Decimal("16.49"), 
                'id_impositivo': None, 
                'Tributos': [
                    {'Tributo': {'tipo_reg': 5, 'alic': Decimal("2.75"), 'ds': 'Retención Ingresos Brutos', 'base_imp': Decimal("95.02"), 'tributo_id': 2, 'id': 119578, 'importe': Decimal("2.61")}}, 
                    {'Tributo': {'tipo_reg': 5, 'alic': Decimal("60.50"), 'ds': 'Percep. IVA RG 212', 'base_imp': Decimal("16.49"), 'tributo_id': 1, 'id': 119578, 'importe': Decimal("9.98")}}], 
                'punto_vta': 54, 
                'err_msg': u"'ascii' codec can't decode byte 0xe1 in position 15: ordinal not in range(128)", 
                'dato_adicional7': None, 'impto_perc_mun': None, 'error': None, 'obs_comerciales': None, 
                'impto_liq_rni': Decimal("0.00"), 'dato_adicional3': None, 
                'dst_cmp': 200, 'pk': 119574, 'dato_adicional5': None, 'email': None, 
                'fecha_serv_hasta': u'20110719', 'fecha_venc_pago': u'20110719', 'formato_id': None, 
                'moneda_ctz': Decimal("1.00000000"), 
                'Ivas': [{'Iva': {'iva_id': 5, 'base_imp': Decimal("78.53"), 'importe': Decimal("16.49"), 'id': 119578, 'tipo_reg': 4}}], 
                'fecha_cbte': u'20110719', 'telefono_cliente': u'0381-4340387', 
                'Items': [{'Item': {'imp_total': Decimal("78.53"), 'bonif': None, 'tipo_reg': 2, 'iva_id': 5, 'precio': Decimal("78.530000"), 'ds': u'Gastos Administrativos (Tarjeta Credito)', 'qty': Decimal("1.00"), 'sec': None, 'ncm': None, 'umed': 7, 'codigo': None, 'id': 119578L}}], 
                'impto_liq_nri': None, 'imp_iibb': Decimal("2.61"), 'zona': None, 
                'nombre_cliente': u'MANFREDO VANESA FABIANA', 'idioma_cbte': u'1', 'provincia_cliente': u'024', 'localidad_cliente': u'SAN MIGUEL DE TUCUMAN', 'dato_adicional2': None, 
                'presta_serv': 2, 'moneda_id': u'PES', 'dato_adicional6': None, 'array_nro_remito': None, 'dato_adicional4': None, 'tipo_reg': 1, 'imp_total': Decimal("107.61"), 'incoterms': u'FOB', 
                'resultado': None, 'forma_pago': u'VTO CONTADO', 
                'webservice': u'wsfev1', 'nro_doc': 23000000000L, 'domicilio_cliente': u'PATRICIAS ARGENTINAS 1 PS PB DP -', 'impto_perc': Decimal("9.98"), 'imp_internos': None, 'tipo_doc': 80, 'dato_adicional1': None, 'lista_id': None, 'tipo_expo': 1, 'cae': 0L, 'imp_neto': Decimal("78.53"), 'pdf': None, 'fecha_vto': u'', 
            'obs': None, 'imp_tot_conc': None, 'err_code': 0}
            escribir_facturas([dic], cnn)


        if '--cargar' in sys.argv:
            # carga el archivo de texto entrada a la base de datos
            facts = cargar_archivo(entrada)
            dic = facts[0]
            if not 'id' in dic:
                raise RuntimeError("El formato de archivo de entrada es incorrecto")
            if DEBUG: print "Cargando ID ", dic['id']
            for k, v in dic.items():
                if DEBUG: print "%s: %s" % (k, v)
            escribir_facturas(facts, cnn)


        if '--ult' in sys.argv:
            print "Consultar ultimo numero:"
            i = sys.argv.index("--ult")
            if len(sys.argv)>i+2:
                tipo_cbte = int(sys.argv[i+1])
                punto_vta = int(sys.argv[i+2])
            else:
                tipo_cbte = int(raw_input("Tipo de comprobante: "))
                punto_vta = int(raw_input("Punto de venta: "))
            if WEBSERVICE=='wsfe':
                ult_cbte = wsfe.recuperar_last_cmp(client, token, sign, cuit, punto_vta, tipo_cbte)
            elif WEBSERVICE=='wsfev1':
                ult_cbte = client.CompUltimoAutorizado(tipo_cbte, punto_vta)
                fecha = client.FechaCbte
                print "Fecha: ", fecha
                if client.ErrMsg:
                    print client.ErrMsg
            elif WEBSERVICE=='wsfex':
                ult_cbte, fecha, events = wsfex.get_last_cmp(client, token, sign, cuit, tipo_cbte, punto_vta)
                print "Fecha: ", fecha
            elif WEBSERVICE=='wsfexv1':
                ult_cbte = client.GetLastCMP(tipo_cbte, punto_vta)
                fecha = client.FechaCbte
                print "Fecha: ", fecha
                if client.ErrMsg:
                    print client.ErrMsg
            elif WEBSERVICE=='wsmtx':
                ult_cbte = client.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
                fecha = client.FechaCbte
                print "Fecha: ", fecha
                if client.ErrMsg:
                    print client.ErrMsg
            print "Ultimo numero: ", ult_cbte
            depurar_xml(client)
            sys.exit(0)

        if '--id' in sys.argv:
            if WEBSERVICE=='wsfe':
                ult_id = wsfe.ultnro(client, token, sign, cuit)
            elif WEBSERVICE=='wsfex':
                ult_id, events = wsfex.get_last_id(client, token, sign, cuit)
            elif WEBSERVICE=='wsfexv1':
                ult_id = client.GetLastID()
                if client.ErrMsg:
                    print client.ErrMsg
            print u"Ultimo numero (ID) de transacción: ", ult_id
            depurar_xml(client)
            sys.exit(0)

        if '--get' in sys.argv:
            print "Recuperar comprobante:"
            tipo_cbte = int(raw_input("Tipo de comprobante: "))
            punto_vta = int(raw_input("Punto de venta: "))
            cbte_nro = int(raw_input("Numero de comprobante: "))
            if WEBSERVICE=='wsfex':
                cbt, events = wsfex.get_cmp(client, token, sign, cuit, tipo_cbte, punto_vta, cbte_nro)
            elif WEBSERVICE=='wsfev1':
                cae = "%s (wsfev1)" % client.CompConsultar(tipo_cbte, punto_vta, cbte_nro)
                cbt = {'CAE': client.CAE,
                        'FechaCbte': client.FechaCbte,
                        'PuntoVenta': client.PuntoVenta,
                        'CbteNro': client.CbteNro,
                        'ImpTotal': client.ImpTotal,
                        'ImpNeto': client.ImpNeto,
                        'ImptoLiq': client.ImptoLiq,
                        'EmisionTipo': client.EmisionTipo,
                        'Excepcion': client.Excepcion,
                        'ErrMsg': client.ErrMsg,
                        }
            elif WEBSERVICE=='wsmtx':
                cae = "%s (wsfev1)" % client.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
                cbt = {'CAE': client.CAE,
                        'FechaCbte': client.FechaCbte,
                        'PuntoVenta': client.PuntoVenta,
                        'CbteNro': client.CbteNro,
                        'ImpTotal': client.ImpTotal,
                        'EmisionTipo': client.EmisionTipo,
                        'Excepcion': client.Excepcion,
                        'ErrMsg': client.ErrMsg,
                        }
            else:
                raise RuntimeError("%s no soporta recuperar un comprobante" % WEBSERVICE)
            for k,v in cbt.items():
                print "%s = %s" % (k, v)
            depurar_xml(client)
            sys.exit(0)
            
        ids = [int(id) for id in sys.argv[2:] if not id.startswith("--")]
        for fact in leer_facturas(cnn, ids):
            if DEBUG: print "Leyendo Factura id=%s: " % fact['id'], fact
            if '--aut' in sys.argv:
                try:
                    fact_id = fact['id']
                    fact['err_code'] = fact['err_msg'] = ''
                    autorizar(client, token, sign, cuit, fact, informar_caea)
                except Exception, e:
                    s = unicode(e).encode("ascii", 'ignore')# e.code, e.msg.encode("ascii","ignore")
                    fact['err_code'] = "" #str(e.code)
                    fact['err_msg'] = s
                    raise
                finally:
                    actualizar_factura(fact, cnn)
                    if '--grabar' in sys.argv:
                        # grabar el archivo de texto salida
                        if DEBUG: print "Grabando ID ", fact['id']
                        grabar_archivo(fact, salida)

                print "Factura: %2d %04d-%08d" % (fact['tipo_cbte'], fact['punto_vta'], fact['cbte_nro']),"Resultado:", fact['resultado']
                print "ID:", fact['id'], "CAE:",fact['cae'],"Obs:",fact['motivo'],"Reproceso:", fact['reproceso'], "ErrMsg:", fact['err_msg']

                if fact['resultado']=="R":
                    print "Saliendo por rechazo"
                    break

            archivo = None
            if '--pdf' in sys.argv:
                if True or fact['cae'] and str(fact['cae']).lower() != 'null' and str(fact['cae']) != '0':
                    archivo = generar_pdf(fact, cnn)
                    if DEBUG: print "generado", archivo
                    if '--mostrar' in sys.argv or '--imprimir' in sys.argv:
                        if sys.platform=="linux2":
                            os.system('evince "%s"' % archivo)
                        else:
                            operation = '--imprimir' in sys.argv and "print" or ""
                            if DEBUG: 
                                print "StartFile", archivo, operation
                            os.startfile(archivo, operation)
                    if '--guardar' in sys.argv:
                        if DEBUG: print "guardando %s para %s" % (archivo, fact['id'])
                        cur = cnn.cursor()
                        sql = 'UPDATE %(encabezado)s SET pdf=? WHERE id=?' % SCHEMA
                        execute(cur, sql, [pyodbc.Binary(open(archivo).read()), fact['id']]) 
                        cnn.commit()
                else:
                    raise RuntimeError("ERROR: no se genera PDF porque la factura no tiene CAE") 
            if '--email' in sys.argv:
                if archivo is None:
                    archivo = fact['pdf']
                if DEBUG: print "enviando %s" % archivo
                enviar_mail(fact,archivo)

        sys.exit(0)

    except SoapFault,e:
        print u"Excepción SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        print >> sys.stderr, "%s\n%s\n" % (e.faultcode,e.faultstring.encode("ascii","replace"))
        sys.exit(3)
    except (wsfex.FEXError, wsfe.WSFEError), e:
        print u"Excepción AFIP:", e.code, e.msg.encode("ascii","ignore")
        print >> sys.stderr, "%s\n%s\n" % (e.code, e.msg.encode("ascii","replace"))
        sys.exit(4)
    except Exception, e:
        print u"\n\nEXCEPCION:", e #.encode("ascii","ignore")
        if DEBUG:
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            raise
        sys.exit(-2)
    finally:
        if XML and client:
            depurar_xml(client, cnn, fact_id)
        if cnn:
            cnn.close()
