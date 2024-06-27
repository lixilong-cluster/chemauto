
ChemAuto - An Automated Analysis Software for Cluster Chemistry.
==============================================================================

Version 5.3
==============================================================================

Packaging
==============================================================================

using pyinstaller

1. pip install pyinstaller
2. put all the necessary models and files in one folder

3.command:

    standard command:
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" main.py

    add logging:
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" --log-level DEBUG main.py

    exclude unecessary libs:
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" --exclude-module PyQt5 --exclude-module IPython --exclude-module PIL --exclude-module bcrypt --exclude-module cryptography --exclude-module charset_normalizer --exclude-module jedi main.py
        
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" --exclude-module bcrypt --exclude-module cryptography --exclude-module charset_normalizer --exclude-module jedi main.py
        
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" --exclude-module bcrypt --exclude-module cryptography --exclude-module charset_normalizer --exclude-module jedi --log-level DEBUG --debug all main.py
        


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

Error and Solution:
    Error info: 
        43535 INFO: Loading module hook 'hook-PySide6.py' from 'D:\\Program Files\\Python\\Python311\\Lib\\site-packages\\PyInstaller\\hooks'...
        Aborting build process due to attempt to collect multiple Qt bindings packages: attempting to run hook for 'PySide6', while hook for 'PyQt5' has already been run! PyInstaller does not support multiple Qt bindings packages in a frozen application - either ensure that the build environment has only one Qt bindings package installed, or exclude the extraneous bindings packages via the module exclusion mechanism (--exclude command-line option, or excludes list in the spec file).

    Solution:
        add "--exclude-module PyQt5" to pyinstaller command
    
    new command:
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" --exclude-module PySide6 main.py
        
        pyinstaller --onefile --console --name ChemAuto --icon chemauto.ico --add-data "D:\Program Files\Python\Python311\Lib\site-packages\pymol\chempy;.\pymol\chempy" --exclude-module PySide6 --exclude-module PyQt5 main.py
        