
ChemAuto - An Automated Analysis Software for Cluster Chemistry.
==============================================================================

Version 5.1
==============================================================================

Packaging
==============================================================================

using pyinstaller

1. pip install pyinstaller
2. put all the necessary models and files in one folder

3.command:

    pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" main.py

4.open ChemAuto.spec file, add the following content to hiddenimports=[]
                    
                            'pymol.api',
                            'pymol.callback',
                            'pymol.cgo',
                            'pymol.cgobuilder',
                            'pymol.checking',
                            'pymol.cmd',
                            'pymol.colorprinting',
                            'pymol.colorramping',
                            'pymol.commanding',
                            'pymol.completing',
                            'pymol.computing',
                            'pymol.constants',
                            'pymol.constants_palette',
                            'pymol.controlling',
                            'pymol.creating',
                            'pymol.diagnosing',
                            'pymol.editing',
                            'pymol.editor',
                            'pymol.experimenting',
                            'pymol.exporting',
                            'pymol.externing',
                            'pymol.feedingback',
                            'pymol.fitting',
                            'pymol.gui',
                            'pymol.headering',
                            'pymol.helping',
                            'pymol.importing',
                            'pymol.internal',
                            'pymol.invocation',
                            'pymol.keyboard',
                            'pymol.keywords',
                            'pymol.lazyio',
                            'pymol.locking',
                            'pymol.menu',
                            'pymol.monitoring',
                            'pymol.morphing',
                            'pymol.movie',
                            'pymol.moving',
                            'pymol.mpeg_encode',
                            'pymol.parser',
                            'pymol.parsing',
                            'pymol.povray',
                            'pymol.preset',
                            'pymol.pymolhttpd',
                            'pymol.querying',
                            'pymol.rpc',
                            'pymol.save_shortcut',
                            'pymol.selecting',
                            'pymol.selector',
                            'pymol.seqalign',
                            'pymol.setting',
                            'pymol.shortcut',
                            'pymol.shortcut_dict',
                            'pymol.shortcut_manager',
                            'pymol.util',
                            'pymol.vfont',
                            'pymol.viewing',
                            'pymol.wizarding',
                            'pymol.xray',
                            'pymol.xwin',
                            'pymol._gui',
                            'pymol.__init__',
                            'pymol.__main__'

5. pyinstaller ChemAuto.spec

6. copy or move ChemAuto.exe under 'dist' folder to user defined directory(for example: ..\chemauto ) 

7. double click ChemAuto.exe to run it. 'chemauto_config.json' and 'chemauto.log' will be created automatically. 

