# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # customtkinter's themes/fonts and tkinterdnd2's tkdnd binaries are picked up
    # by hook-customtkinter.py (pyinstaller-hooks-contrib) and hook-tkinterdnd2.py
    # (in this folder, see hookspath below).
    datas=[('sd_prompt_reader/resources', 'sd_prompt_reader/resources')],
    hiddenimports=[
        'sd_prompt_reader',
        'sd_prompt_reader.app',
        'sd_prompt_reader.cli',
        'sd_prompt_reader.config',
        'sd_prompt_reader.converter_panel',
        'sd_prompt_reader.file_list',
        'sd_prompt_reader.image_browser',
        'sd_prompt_reader.image_converter',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SD Prompt Reader+',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    windowed=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sd_prompt_reader/resources/icon-gui.ico',
    version='file_version_info.txt',
)
