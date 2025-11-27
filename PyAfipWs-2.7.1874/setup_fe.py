#!/usr/bin/python
# -*- coding: latin-1 -*-

# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008-2014 Mariano Reingart"

from distutils.core import setup
import glob
import os
import subprocess
import warnings
import sys

try:
    rev = subprocess.check_output(['hg', 'id', '--num']).strip().rstrip("+")
except:
    rev = 0

__version__ = "%s.%s.%s" % (sys.version_info[0:2] + (rev, ))

# modulos a compilar y empaquetar (comentar si no se desea incluir):

import fe_bd

# herramientas opcionales a compilar y empaquetar:
try:
    if 'pyfepdf' in globals() or 'pyrece' in globals():
        import designer     
except ImportError:
    # el script pyfpdf/tools/designer.py no esta disponible:
    print "IMPORTANTE: no se incluye el diseñador de plantillas PDF"

# parametros para setup:
kwargs = {}

long_desc = ("Interfases, herramientas y aplicativos para Servicios Web"  
             "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
             "ANMAT (Trazabilidad de Medicamentos), "
             "RENPRE (Trazabilidad de Precursores Químicos), "
             "ARBA (Remito Electrónico)")

# convert the README and format in restructured text (only when registering)
if os.path.exists("README.md") and sys.platform == "linux2":
    try:
        cmd = ['pandoc', '--from=markdown', '--to=rst', 'README.md']
        long_desc = subprocess.check_output(cmd).decode("utf8")
        print "Long DESC", long_desc
    except Exception as e:
        warnings.warn("Exception when converting the README format: %s" % e)


data_files = [
    (".", ["licencia.txt",]),
    ("conf", ["conf/rece.ini", "conf/geotrust.crt", "conf/afip_ca_info.crt", ]),
    ("cache", glob.glob("cache/*")),
    ]

# incluyo mis certificados para homologación (si existen)
if os.path.exists("reingart.crt"):
    data_files.append(("conf", ["reingart.crt", "reingart.key"]))
    
if sys.version_info > (2, 7):
    # add "Microsoft Visual C++ 2008 Redistributable Package (x86)"
    if os.path.exists(r"c:\Program Files\Mercurial"):
        data_files += [(
            ".", glob.glob(r'c:\Program Files\Mercurial\msvc*.dll') +
                 glob.glob(r'c:\Program Files\Mercurial\Microsoft.VC90.CRT.manifest'),
            )]
    # fix permission denied runtime error on win32com.client.gencache.GenGeneratePath
    # (expects a __init__.py not pyc, also dicts.dat pickled or _LoadDicts/_SaveDicts will fail too)
	# NOTE: on windows 8.1 64 bits, this is stored in C:\Users\REINGART\AppData\\Local\Temp\gen_py\2.7
	from win32com.client import gencache
	gen_py_path = gencache.GetGeneratePath() or "C:\Python27\lib\site-packages\win32com\gen_py"
	data_files += [(
            r"win32com\gen_py", 
            [os.path.join(gen_py_path, "__init__.py"),
             os.path.join(gen_py_path, "dicts.dat")],
            )]
    
    sys.path.insert(0, r"C:\Python27\Lib\site-packages\pythonwin")
    WX_DLL = (
        ".", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\mfc*.*') +
             glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\Microsoft.VC90.MFC.manifest'),
        )
else:
    WX_DLL = (".", [
        "C:\python25\Lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll",
        "C:\python25\MSVCR71.dll",
        "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll",
        ])

HOMO = True

# build a one-click-installer for windows:
import py2exe
from nsis import build_installer, Target

# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils',  'email.mime.text', 'email.mime.application', 'email.mime.multipart']
#includes.extend(["PIL.Image", "PIL.ImageFont", "PIL.ImageDraw"])

# optional modules:
# required modules for shelve support (not detected by py2exe by default):
for mod in ['socks', 'dbhash', 'gdbm', 'dbm', 'dumbdbm', 'anydbm']:
    try:
        __import__(mod)
        includes.append(mod)
    except ImportError:
        pass 

# don't pull in all this MFC stuff used by the makepy UI.
excludes=["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui",
          "Tkconstants","Tkinter","tcl",
          "_imagingtk", "PIL._imagingtk", "ImageTk", "PIL.ImageTk", "FixTk",
         ]

# basic options for py2exe
opts = { 
    'py2exe': {
        'includes': includes,
        'optimize': 0,
        'excludes': excludes,
        'dll_excludes': ["mswsock.dll", "powrprof.dll", "KERNELBASE.dll", 
                     "tcl85.dll", "tk85.dll",
                     # Windows 8.1 DLL:
                     "CRYPT32.dll", "WLDAP32.dll",
                     "api-ms-win-core-delayload-l1-1-1.dll",
                     "api-ms-win-core-errorhandling-l1-1-1.dll",
                     "api-ms-win-core-handle-l1-1-0.dll",
                     "api-ms-win-core-heap-l1-2-0.dll",
                     "api-ms-win-core-heap-obsolete-l1-1-0.dll",
                     "api-ms-win-core-libraryloader-l1-2-0.dll",
                     "api-ms-win-core-localization-obsolete-l1-2-0.dll",
                     "api-ms-win-core-processthreads-l1-1-2.dll",
                     "api-ms-win-core-profile-l1-1-0.dll",
                     "api-ms-win-core-registry-l1-1-0.dll",
                     "api-ms-win-core-string-l1-1-0.dll",
                     "api-ms-win-core-string-obsolete-l1-1-0.dll",
                     "api-ms-win-core-synch-l1-2-0.dll",
                     "api-ms-win-core-sysinfo-l1-2-1.dll",
                     "api-ms-win-security-base-l1-2-0.dll",
                     ],
        'skip_archive': True,
        }
    }

desc = "Instalador PyAfipWs FE.py"
kwargs['com_server'] = []
kwargs['console'] = []
kwargs['windows'] = []

# add 32bit or 64bit tag to the installer name
import platform
__version__ += "-" + platform.architecture()[0]

# legacy webservices & utilities:
if 'fe_bd' in globals():
    kwargs['console'] += ['fe_bd.py', 'wsaa.py', 'correo.py']
    kwargs['windows'] += ['designer.py']

    data_files += [
        WX_DLL, 
        ("plantillas", ["plantillas/logo.png", 
                        "plantillas/factura.csv",
                        "plantillas/recibo.csv"]),
        ]
    __version__ += "+fe_bd_" + fe_bd.__version__
    HOMO &= fe_bd.HOMO

# custom installer:
kwargs['cmdclass'] = {"py2exe": build_installer}

# add certification authorities (newer versions of httplib2)
try:
    import httplib2
    if httplib2.__version__ >= "0.9":
        data_files += [("httplib2", 
            [os.path.join(os.path.dirname(httplib2.__file__), "cacerts.txt")])]
except ImportError:
    pass

# agrego tag de homologación (testing - modo evaluación):
__version__ += "-homo" if HOMO else "-full"



setup(name="PyAfipWs",
      version=__version__,
      description=desc,
      long_description=long_desc,
      author="Mariano Reingart",
      author_email="reingart@gmail.com",
      url="https://code.google.com/p/pyafipws/" if 'register' in sys.argv 
          else "http://www.sistemasagiles.com.ar",
      license="GNU GPL v3",
      options=opts,
      data_files=data_files,
            classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: End Users/Desktop",
            "Intended Audience :: Financial and Insurance Industry",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            #"Programming Language :: Python :: 3.2",
            "Operating System :: OS Independent",
            "Operating System :: Microsoft :: Windows",
            "Natural Language :: Spanish",
            "Topic :: Office/Business :: Financial :: Point-Of-Sale",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Software Development :: Object Brokering",
      ],
      keywords="webservice electronic invoice pdf traceability",
      **kwargs
      )

