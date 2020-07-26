#!/bin/bash

TITLE=
SELECT="url"

while getopts ":t" opt; do
  case $opt in
    t)
      # echo "-t was triggered, Parameter: $OPTARG" >&2
      TITLE=1
      SELECT="title,url"
      ;;
  esac
done
shift $((OPTIND -1))

BROWSER=${1:-}

if [ "$(hostname)" == "oslo" ]; then
    #FIREFOX_DB_LOCKED="$HOME/.mozilla/firefox/94hgpnm9.default/places.sqlite"
    FIREFOX_DB_LOCKED="$HOME/.mozilla/firefox/wi5onyui.default-release/places.sqlite"
    CHROMIUM_DB_LOCKED="$HOME/.config/chromium/Default/History"
elif [ "$(hostname)" == "boltmsi" ]; then
    #FIREFOX_DB_LOCKED="$HOME/.mozilla/firefox/vfgkahge.default/places.sqlite"
    FIREFOX_DB_LOCKED="$HOME/.mozilla/firefox/d97i5z0y.default-release/places.sqlite"
    CHROMIUM_DB_LOCKED="$HOME/.config/chromium/Default/History"
else
    echo "Unknow hostname: $(hostname)"
    exit 1
fi

CHROMIUM_DB="/tmp/chromium.sqlite"
FIREFOX_DB="/tmp/firefox.sqlite"
cp $CHROMIUM_DB_LOCKED $CHROMIUM_DB
cp $FIREFOX_DB_LOCKED $FIREFOX_DB

_show_firefox_history() {
    sqlite3 $FIREFOX_DB "select $SELECT from moz_places order by last_visit_date desc" # \
}

_show_chromium_history() {
    sqlite3 $CHROMIUM_DB "select $SELECT from urls order by last_visit_time desc" #\
}

if [[ "$BROWSER" == "" || "$BROWSER" == "f" ]]; then _show_firefox_history; fi
if [[ "$BROWSER" == "" || "$BROWSER" == "c" ]]; then _show_chromium_history; fi

