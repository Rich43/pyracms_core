#!/bin/bash
INIFILE="development_all.ini"
rm pyracms.db
rm -rf whoosh_index
initialize_pyracms_db $INIFILE
initialize_pyracms_gallery_db $INIFILE
initialize_pyracms_forum_db $INIFILE
initialize_pyracms_article_db $INIFILE
initialize_pyracms_pycode_db $INIFILE
initialize_hypernucleus-server_db $INIFILE
