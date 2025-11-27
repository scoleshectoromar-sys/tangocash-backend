# -*- coding: utf-8 -*-

PROVINCIAS = {0: 'CIUDAD DE BUENOS AIRES', 1: 'BUENOS AIRES', 2: 'CATAMARCA', 3: 'CORDOBA', 4: 'CORRIENTES', 5: 'ENTRE RIOS', 6: 'JUJUY', 7: 'MENDOZA', 8: 'LA RIOJA', 9: 'SALTA', 10: 'SAN JUAN', 11: 'SAN LUIS', 12: 'SANTA FE', 13: 'SANTIAGO DEL ESTERO', 14: 'TUCUMAN', 16: 'CHACO', 17: 'CHUBUT', 18: 'FORMOSA', 19: 'MISIONES', 20: 'NEUQUEN', 21: 'LA PAMPA', 22: 'RIO NEGRO', 23: 'SANTA CRUZ', 24: 'TIERRA DEL FUEGO'}

import unicodedata
import json

client = None

def normalizar(txt):
    return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore')

def buscar_cuit(cat_iva=1, tipo_doc=80, nro_doc=0, passphrase=""):
    global client
    import os, sys, traceback
    from gluon.contrib.pysimplesoap.simplexml import SimpleXMLElement

    import ssl
    from functools import partial

    ssl.wrap_socket = partial(ssl.wrap_socket, ssl_version=ssl.PROTOCOL_TLSv1)

    serialized = 'a4cfc0885dfee1277411d180f29dcd204741b3d8da08c87d6ed17916b6b3e51c|248df1d485205b84cd5b0ef915fc7720f12bc93fb39fbb42487f8c949e206299|8e12a010c4688ba48c294740e1c2113d08b1f43352fa4c35e62fe0f2d8e2fa93b391abaa34324917229dd85fb52f775c87824ea2046f83514a71f8ee603beaac83cca0a57f0392c663a90eb51c1ee833'

    import m2secret
    # Decrypt
    secret = m2secret.Secret()
    secret.deserialize(serialized)
    password = secret.decrypt(passphrase)

    from pyafipws.utils import WebClient, HTMLFormParser

    if client is None:
        client = WebClient(location="https://auth.afip.gov.ar/contribuyente/", 
                           enctype="application/x-www-form-urlencoded",
                           trace=True)
        response = client(user="20267565393", password=password, 
                          action="AUTH")

        parser = HTMLFormParser()

        parser.feed(response)

        for form in parser.forms.values():
            if form['system'] == 'rcel':
                break
        else:
            raise RuntimeError("rcel no encontrado")

        response = client(**form)

        parser = HTMLFormParser()
        parser.feed(response)

        myform = parser.forms['myform']
        client.location = "https://serviciosjava.afip.gob.ar/rcel/jsp/index.jsp"
        client.referer = "https://auth.afip.gov.ar/contribuyente/"
        response = client(**myform)

    client.location = "https://serviciosjava.afip.gob.ar/rcel/jsp/ajax.do"
    client.method = "GET"
    response = client(f="datosreceptor", ivareceptor=cat_iva, idtipodoc=tipo_doc, nrodoc=nro_doc)
    return response

def buscar_cuit_json(cat_iva=1, tipo_doc=80, nro_doc=0, passphrase=""):
    from pyafipws.utils import WebClient
    try:
        url = "https://soa.afip.gob.ar/sr-padron/v2/persona/%s" % nro_doc
        client = WebClient(location=url, trace=True)
        client.method = "GET"
        f = client()
        return json.loads(f)
    except Exception as e:
        return {"success": False, "error": { "tipoError": "app", "mensaje": str(e)}}

def index():
    response.view = "generic.html"
    form = SQLFORM.factory(
        Field("cat_iva", "integer", default=1, requires=IS_IN_SET({1: "Resp.Inscripto", 4: "Exento", 5: "Consumidor Final", 6: "Monotributo"})),
        Field("tipo_doc", "integer", default=80, requires=IS_IN_SET({80: "CUIT", 96: "DNI"})),
        Field("nro_doc", "string", default=30500858628),
        Field("clave", "password"),
        )
    if form.accepts(request.vars, session):
        import time
        time.sleep(1)
        res = buscar(form.vars.cat_iva, form.vars.tipo_doc, form.vars.nro_doc, form.vars.clave)
        return res
    else:
        return {'form': form}

def buscar(cat_iva, tipo_doc, nro_doc, clave, usuario=None):
    #q  = db.consultas.cat_iva == cat_iva
    q = db.consultas.tipo_doc == tipo_doc
    q &= db.consultas.nro_doc == nro_doc
    row = db(q).select(limitby=(0, 1)).last()
    sufijo = clave[6:]
    if False and (not clave or (row and row.respuesta.startswith("OK"))):
        res = row.respuesta
        cat_iva = row.cat_iva
    else:
        # si la categoría de iva no es dada, pruebo las más comunes:
        for i in [1, 6, 4, 5]:
            try:
                res = buscar_cuit_json(cat_iva=i,
                                  tipo_doc=tipo_doc,
                                  nro_doc=nro_doc,
                                  passphrase=clave[:6])
            except Exception, e:
                res = "ERR#%%#%s" % e
            if res: # .startswith("OK#")
                cat_iva = i
                break
        db.consultas.insert(cat_iva=cat_iva,
                            tipo_doc=tipo_doc,
                            nro_doc=nro_doc,
                            sufijo=sufijo,
                            respuesta=json.dumps(res),
                            usuario=usuario)
    #res = normalizar(res.decode("utf8", "ignore")).upper().split("#%#")

    from pyafipws.padron import PadronAFIP
    padron = PadronAFIP()
    padron.Buscar(nro_doc, tipo_doc)

    #res = json.loads(res)
    if res["success"]:
        denominacion = normalizar(res["data"]["nombre"])
        if res["data"]["estadoClave"] == "ACTIVO":
            direccion = normalizar(res["data"]["domicilioFiscal"]["direccion"])
            localidad = normalizar(res["data"]["domicilioFiscal"].get("localidad", ""))
            provincia = PROVINCIAS.get(res["data"]["domicilioFiscal"]["idProvincia"], "")
        else:
            direccion = localidad = provincia = "CUIT NO ACTIVO"
        #direccion = domicilio.split(" - ")[0]
        #localidad = domicilio.split(" - ")[1].split(", ")[0]
        #provincia = domicilio.split(" - ")[1].split(", ")[1]
        # cat_iva=6, tipo_doc=80, nro_doc=20376153321
        # domicilio=  'B CAMPO PAPPA SECTOR 11 C 68 - 0 - GODOY CRUZ, MENDOZA'
        #direccion = domicilio[:domicilio.rfind(" - ")]
        #localidad = domicilio[domicilio.rfind(" - ")+3:].split(", ")[0]
        #provincia = domicilio[domicilio.rfind(" - ")+3:].split(", ")[1]
    else:
        denominacion = padron.denominacion
        domicilio = direccion = localidad = provincia = ""
        response.flash = "Error al procesar la solicitud. Revise los datos. %s" % res["error"]["mensaje"]

    reg = dict(
        denominacion=denominacion,
        direccion=direccion,
        localidad=localidad,
        provincia=provincia,
        imp_ganancias=padron.imp_ganancias,
        imp_iva=padron.imp_iva,
        monotributo=padron.monotributo,
        integrante_soc=padron.integrante_soc,
        empleador=padron.empleador,
        actividad_monotributo=padron.actividad_monotributo,
        tipo_doc=tipo_doc,
        nro_doc=nro_doc,
        cat_iva=cat_iva,
        email=padron.email,
        )

    db.padron.insert(**reg)

    return reg

response.namespace = "http://vm5.sistemasagiles.com.ar/padron/consulta/call/soap"
service = Service()
@service.soap('BuscarSOAP',
              returns={'resultado': dict(
                           denominacion=str,
                           direccion=str,
                           localidad=str,
                           provincia=str,
                           imp_ganancias=str,
                           imp_iva=str,
                           monotributo=str,
                           integrante_soc=str,
                           empleador=str,
                           actividad_monotributo=str,
                           tipo_doc=str,
                           nro_doc=str,
                           cat_iva=str,
                           email=str),
                    },
              args={'cat_iva': str,
                    'tipo_doc': str,
                    'nro_doc': str,
                    #'clave': str,
                    })
def buscar_soap(cat_iva, tipo_doc, nro_doc): #, clave=""):
    from gluon.contrib.pysimplesoap.simplexml import SimpleXMLElement
    xml = SimpleXMLElement(request.xml, namespace=response.namespace)
    soap = "http://schemas.xmlsoap.org/soap/envelope/"
    wsse = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
    usuario = str(xml("Header", ns=soap)("Security", ns=wsse)("Username", ns=wsse))
    clave = str(xml("Header", ns=soap)("Security", ns=wsse)("Password", ns=wsse))
    if usuario not in ("monsanto", "adc"):
        raise RuntimeError("Usuario incorrecto!")
    return buscar(int(cat_iva), int(tipo_doc), int(nro_doc), clave, usuario)

def muestra():
    clave = request.vars['clave']
    usuario = "mariano"

    import time
    
    t0 = time.time()
    ret = []

    from pyafipws.padron import PadronAFIP
    padron = PadronAFIP()
    padron.cursor.execute("SELECT * FROM padron ORDER BY RANDOM() LIMIT 250")
    for row in padron.cursor:
        if row['imp_iva'] == "AC":
            cat_iva = 1
        elif row['imp_iva'] == "EX":
            cat_iva = 4
        elif row['monotributo'] != "NI":
            cat_iva = 6
        ok = buscar(cat_iva, 80, row['nro_doc'], clave, usuario)
        ret.append(ok)
    response.view = "generic.html"
    t1 = time.time()
    return {'ret': ret, 'q': len(ret), 't': t1-t0}
    
def call():
    return service()

