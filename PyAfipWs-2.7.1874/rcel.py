from utils import WebClient, HTMLFormParser
import json

def consultar(cat_iva=1, tipo_doc=80, nro_doc=None):
    client = WebClient(location="https://auth.afip.gov.ar/contribuyente/", 
                       enctype="application/x-www-form-urlencoded",
                       trace=True)
    response = client(user="20267565393", password="1686afip", 
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
    

provincias = [{"idProvincia":19,"descProvincia":"MISIONES"},{"idProvincia":22,"descProvincia":"RIO NEGRO"},{"idProvincia":17,"descProvincia":"CHUBUT"},{"idProvincia":23,"descProvincia":"SANTA CRUZ"},{"idProvincia":18,"descProvincia":"FORMOSA"},{"idProvincia":24,"descProvincia":"TIERRA DEL FUEGO"},{"idProvincia":16,"descProvincia":"CHACO"},{"idProvincia":13,"descProvincia":"SANTIAGO DEL ESTERO"},{"idProvincia":14,"descProvincia":"TUCUMAN"},{"idProvincia":11,"descProvincia":"SAN LUIS"},{"idProvincia":12,"descProvincia":"SANTA FE"},{"idProvincia":21,"descProvincia":"LA PAMPA"},{"idProvincia":3,"descProvincia":"CORDOBA"},{"idProvincia":20,"descProvincia":"NEUQUEN"},{"idProvincia":2,"descProvincia":"CATAMARCA"},{"idProvincia":1,"descProvincia":"BUENOS AIRES"},{"idProvincia":10,"descProvincia":"SAN JUAN"},{"idProvincia":0,"descProvincia":"CIUDAD AUTONOMA BUENOS AIRES"},{"idProvincia":7,"descProvincia":"MENDOZA"},{"idProvincia":6,"descProvincia":"JUJUY"},{"idProvincia":5,"descProvincia":"ENTRE RIOS"},{"idProvincia":4,"descProvincia":"CORRIENTES"},{"idProvincia":9,"descProvincia":"SALTA"},{"idProvincia":8,"descProvincia":"LA RIOJA"}]
provincias = dict([(e['idProvincia'], e['descProvincia']) for e in provincias])

def consultar_json(nro_doc):
    try:
        url = "https://soa.afip.gob.ar/sr-padron/v2/persona/%s" % nro_doc
        client = WebClient(location=url, trace=True)
        client.method = "GET"
        f = client()
        return json.loads(f)

    except:
        return "#ERR"
                       
print provincias

print consultar_json(nro_doc=27269434894)
