# coding: utf8

import csv


def leer_planilla(entrada):
    "Convierte una planilla CSV a una lista de diccionarios [{'col': celda}]"
    
    items = []
    csv_reader = csv.reader(open(entrada), dialect='excel', delimiter=";")
    for row in csv_reader:
        items.append(row)
    if len(items) < 2:
        raise RuntimeError('El archivo no tiene filas vÃ¡lidos')
    if len(items[0]) < 2:
        raise RuntimeError('El archivo no tiene columnas (usar coma de separador)')
    cols = [str(it).strip() for it in items[0]]

    # armar diccionario por cada linea
    items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

    return items


facturas = leer_planilla("/home/reingart/Descargas/20150622.CSV")
detalles = leer_planilla("/home/reingart/Descargas/06000221.CSV")

for factura in facturas:
    for k, v in factura.items():
        if k.startswith("imp"):
            factura[k] = float(v)
        if k in ('cbt_desde', 'cbt_hasta', 'concepto', 'punto_vta', 'tipo_cbte', 'tipo_doc', 'nro_doc'):
            factura[k] = int(v)

alicuotas = {3:0, 4: 10.5, 5: 21., 6: 27}
ivas = {}
imp_iva = 0.00

for det in detalles:
    iva_id = det['iva_id']
    
    if iva_id:
        iva_id = int(iva_id)
        if iva_id not in ivas:
            ivas[iva_id] = {"base_imp": 0, "importe": 0, "iva_id": iva_id}

        importe = round(float(det['importe'].replace(",", ".")), 2)
        neto = round(importe / ((100 + alicuotas[iva_id]) / 100), 2)
        iva = importe - neto
        print "importe", importe, iva
        imp_iva += iva
        ivas[iva_id]['importe'] += iva
        ivas[iva_id]['base_imp'] += neto
        det['imp_iva'] = iva

facturas[0]['detalles'] = detalles
facturas[0]['ivas'] = ivas.values()
facturas[0]['datos'] = []
facturas[0]['tributos'] = []
facturas[0]['imp_iva'] = imp_iva
facturas[0]['cbte_nro'] = facturas[0]['cbt_desde']

if facturas[0]['concepto'] == 1:
    facturas[0]['fecha_venc_pago'] = None

import json
archivo = open("entrada.txt", "w")
json.dump(facturas, archivo, sort_keys=True, indent=4)
archivo = open("factura.txt", "w")
json.dump(facturas, archivo, sort_keys=True, indent=4)


# importe numerico
# 
