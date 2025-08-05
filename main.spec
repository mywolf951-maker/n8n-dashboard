# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

a = Analysis(
    ['main.py'],  # ✅ Punto de entrada correcto
    pathex=[os.path.abspath('.')],  # ✅ Desde la raíz del proyecto
    binaries=[],
    datas=[
        # Asegúrate de que estas rutas coincidan con la ubicación real en tu proyecto
        # y que el destino en el .exe sea el esperado por tu clase Recursos.
        ('recursos/n8n_icon.ico', 'recursos'),      # Incluye 'n8n_icon.ico' en la carpeta 'recursos' dentro del .exe
        ('recursos/n8n_control_logo.png', 'recursos'), # Incluye 'n8n_control_logo.png' en la carpeta 'recursos' dentro del .exe
        ('config/usuario_config.json', 'config'),   # Incluye 'usuario_config.json' en la carpeta 'config' dentro del .exe
        ('idiomas/es.json', 'idiomas'),             # <-- ¡NUEVO! Incluye el archivo de idioma español
        ('idiomas/en.json', 'idiomas'),             # <-- ¡NUEVO! Incluye el archivo de idioma inglés
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Control_n8n',  # ✅ nombre del ejecutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    # Asegúrate de que esta ruta del icono sea correcta en tu proyecto de origen
    icon=os.path.join('recursos', 'n8n_icon.ico') # Ruta al icono para el ejecutable
)
