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

"""Módulo para obtener código de autorización de impresión o 
electrónico del web service WSFEXv1 de AFIP (Factura Electrónica Exportación V1)
"""

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

import sys
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper, __version__
print __version__


WSDLs=[
    "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl",
    "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl",
    "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
    "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
    "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl",
    "https://serviciosjava.afip.gob.ar/wsmtxca/services/MTXCAService?wsdl",
    "https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL",
    "https://servicios1.afip.gov.ar/wsfexv1/service.asmx?WSDL",
    "https://wswhomo.afip.gov.ar/wsbfev1/service.asmx?WSDL",
    "https://servicios1.afip.gov.ar/wsbfev1/service.asmx?WSDL",
    "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL",
    "https://servicios1.afip.gov.ar/WSCDC/service.asmx?WSDL",
    "https://fwshomo.afip.gov.ar/wscoc/COCService?wsdl",
    "https://serviciosjava.afip.gob.ar/wscoc2/COCService?wsdl",
    "https://fwshomo.afip.gov.ar/wsctg/services/CTGService_v3.0?wsdl",
    "https://serviciosjava.afip.gov.ar/wsctg/services/CTGService_v3.0?wsdl",
    "https://fwshomo.afip.gov.ar/wslpg/LpgService?wsdl",
    "https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl",
    "https://fwshomo.afip.gov.ar/wsltv/LtvService?wsdl",
    "https://serviciosjava.afip.gob.ar/wsltv/LtvService?wsdl",
    "https://fwshomo.afip.gov.ar/wsltv/LtvService?wsdl",
    "https://serviciosjava.afip.gob.ar/wsltv/LtvService?wsdl",
    "https://servicios.pami.org.ar/trazamed.WebService?wsdl",
    "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl",
    "https://servicios.pami.org.ar/trazaenagr.WebService?wsdl",     # fito
    "https://servicios.pami.org.ar/trazaagr.WebService?wsdl",       # fito prod
    "https://servicios.pami.org.ar/trazaenvet.WebService?wsdl",     # vet
    "https://servicios.pami.org.ar/trazavet.WebService?wsdl",       # vet prod
    ]

wrapper = None
cache = "./cache"
proxy_dict = None
cacert = None

for wsdl in WSDLs:
    if wrapper:
        Http = set_http_wrapper(wrapper)
        print Http._wrapper_version
    print "Conectando a wsdl=%s " % (wsdl, )
    try:
        client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            cacert = cacert,
            soap_server="jetty" if 'pami' in wsdl else None,
            trace = "--trace" in sys.argv)
    except:
        pass
