import pysimplesoap.client

print pysimplesoap.client.__file__, pysimplesoap.client.__version__

c = pysimplesoap.client.SoapClient(wsdl="https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL")
print c.FEDummy()

c = pysimplesoap.client.SoapClient(wsdl="https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL")
print c.FEDummy()
