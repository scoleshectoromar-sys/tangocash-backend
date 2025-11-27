import datetime

s1= """<tipoComprobante>?</tipoComprobante>
<nroComprobante>?</nroComprobante>
13<puntoVenta>?</puntoVenta>
<!--Optional: -->
<iibbEmisor>?</iibbEmisor>
<codDepositoAcopio>?</codDepositoAcopio>
<fechaLiquidacion>?</fechaLiquidacion>
<tipoCompra>?</tipoCompra>
<variedadTabaco>?</variedadTabaco>
<codProvinciaOrigenTabaco>
</codProvinciaOrigenTabaco>
<!--Optional: -->
<puerta>?</puerta>
<!--Optional: -->
<nroTarjeta>?</nroTarjeta>
<!--Optional: -->
<horas>?</horas>
<!--Optional: -->
<control>?</control>
<!--Optional: -->
<nroInterno>?</nroInterno>"""


s2 = """<!--1 or more repetitions: -->
<condicionVenta>
<codigo>?</codigo>
<!--Optional: -->
<descripcion>?</descripcion>
</condicionVenta>"""


s3 = """<cuit>?</cuit>
<!--Optional: -->
<iibb>?</iibb>
<!--Optional: -->
<nroSocio>?</nroSocio>
<!--Optional: -->
<nroFET>?</nroFET>
"""

s4 = """<nroRomaneo>?</nroRomaneo>
<fechaRomaneo>?</fechaRomaneo>
<!--1 or more repetitions: -->
<fardo>
</fardo>
"""

s5 = """<codTrazabilidad>?</codTrazabilidad>
<claseTabaco>?</claseTabaco>
<peso>?</peso>
"""

s6 = """<claseTabaco>?</claseTabaco>
<precio>?</precio>
"""

s = """codRetencion>?</codRetencion>
<!--Optional: -->
<descripcion>?</descripcion>
<importe>?</importe>"""

s = """<codigoTributo>?</codigoTributo>
<!--Optional: -->
<descripcion>?</descripcion>
<baseImponible>?</baseImponible>
<alicuota>?</alicuota>
<importe>?</importe>
"""


tag = 0

params = []

for c in s:
    if c == "<":
        tag = 1
        params.append("")
    elif c in ("/", "!") and tag:
        tag = 2
    elif c == ">":
        tag = 0
    else:
        if tag == 1:
            params[-1] += c

print

def underscore(n):
    r = ""
    for c in n:
        if c.isupper():
            r += "_" + c.lower()
        else:
            r += c
    return r

for p in params:
    if p:
        print "%s=None," % (underscore(p)),

print
print "-" * 70
print

for p in params:
    if p:
        print "%s=%s," % (p, (underscore(p))), 

print 


d = {'cabecera': {'cae': 85523002502850L,
              'codDepositoAcopio': 1,
              'domicilioDepositoAcopio': u'av dep acopio 2233',
              'domicilioPuntoVenta': u'pto vta al 3500',
              'fechaLiquidacion': datetime.date(2016, 1, 1),
              'nroComprobante': 31,
              'puntoVenta': 2002,
              'tipoComprobante': u'150'},
 'datosOperacion': {'codProvinciaOrigenTabaco': 1,
                    'condicionVenta': [{'codigo': 1}],
                    'control': u'FFAA',
                    'horas': u'12',
                    'nroInterno': u'77888',
                    'nroTarjeta': u'6569866',
                    'puerta': u'22',
                    'tipoCompra': u'CPS',
                    'variedadTabaco': u'BR'},
 'detalleOperacion': {'cantidadTotalFardos': 1,
                      'pesoTotalFardosKg': 900,
                      'romaneo': [{'detalleClase': [{'cantidadFardos': 1,
                                                     'codClase': 4,
                                                     'importe': 171000.0,
                                                     'pesoFardosKg': 900,
                                                     'precioXKgFardo': 190.0}],
                                   'fechaRomaneo': datetime.date(2015, 12, 10),
                                   'nroRomaneo': 321L}]},
 'emisor': {'cuit': 30000000007L,
            'domicilio': u'Peru 100',
            'fechaInicioActividad': datetime.date(2010, 1, 1),
            'razonSocial': u'JOCKER',
            'situacionIVA': u'IVA Responsable Inscripto'},
 'pdf': '',
 'receptor': {'cuit': 20111111112L,
              'domicilio': u'Calle 1',
              'iibb': 123456L,
              'nroFET': u'22',
              'nroSocio': u'11223',
              'razonSocial': u'CUIT PF de Prueba gen\xe9rica',
              'situacionIVA': u'IVA Responsable Inscripto'},
 'retencion': [{'codigo': u'14', 'importe': 12.0},
               {'codigo': u'12', 'importe': 12.0}],
 'totalesOperacion': {'alicuotaIVA': 21.0,
                      'importeIVA': 35910.0,
                      'importeNeto': 171000.0,
                      'subtotal': 206910.0,
                      'total': 205685.46,
                      'totalRetenciones': 24.0,
                      'totalTributos': 1200.54},
 'tributo': [{'alicuota': 8.0,
              'baseImponible': 15000.0,
              'codigo': u'2',
              'descripcion': u'Ganancias',
              'importe': 1200.54}]}

for k1, d2 in d.items():
    if isinstance(d2, list): d2= d2[0]
    if isinstance(d2, dict):
        for k2, v in d2.items():
            print "%s_%s=liq['%s']['%s']," % (underscore(k1), underscore(k2), k1, k2)
    else:
        print "%s=liq['%s']," % ((underscore(k1), k1)) 

