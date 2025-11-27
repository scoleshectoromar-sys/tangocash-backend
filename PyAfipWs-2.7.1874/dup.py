import csv

# si no encuentro archivo, lo busco en el directorio predeterminado:
entrada = "plantillas/fac_apaisada.csv"
salida = "plantillas/factura_transporte.csv"

sal = open(salida, "w")

for lno, linea in enumerate(open(entrada.encode('latin1')).readlines()):
    args = []
    for i,v in enumerate(linea.split(";")):
        if not v.startswith("'"): 
            v = v.replace(",",".")
        else:
            v = v#.decode('latin1')
        if v.strip()=='':
            v = None
        else:
            v = eval(v.strip())
        args.append(v)
        
    sal.write(";".join(["%s" % repr(a) for a in args]) + "\r\n")
    args[2] = args[2] + 150
    args[4] = args[4] + 150
    sal.write(";".join(["%s" % repr(a) for a in args]) + "\r\n")

sal.close()


    
