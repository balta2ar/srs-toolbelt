#!/bin/bash

# alias urldecode='sed "s@+@ @g;s@%@\\\\x@g" | xargs -0 printf "%b"'

shorten() {
    sed 's|\(^.\{100\}\).*|\1|'
}

urldecode() {
    #sed "s@+@ @g;s@%@\\\\x@g" | xargs -d '\n' -n10000 printf "%b\n"
    #sed "s@+@ @g;s@%@\\\\x@g" | xargs -0 printf "%b"
    #python3 -c "import urllib.parse, sys; print(urllib.parse.unquote(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()[0:-1]))"
    python2 -c "import urllib, sys; print(urllib.unquote(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()[0:-1]))"
}

urldecode_plus() {
    python2 -c "import urllib, sys; print(urllib.unquote_plus(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()[0:-1]))"
}

#alias urldecode='python -c "import urllib, sys; print urllib.unquote(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()[0:-1])"'

uniq_keep_order() {
    cat -n | sort -k2 -k1n  | uniq -f1 | sort -nk1,1 | cut -f2-
}

filter_lingvolive() {
    \grep 'lingvolive\.com.*/translate/' \
    | sed "s|.*www\.lingvolive\.com.*/translate/.\{5\}/||" \
    | sed "s|\?.*||"
}

filter_krdict() {
    # Filters words from this online dictionary:
    # https://krdict.korean.go.kr/eng/dicSearch/search?nation=eng&nationCode=6&ParaWordNo=&mainSearchWord=%EC%9A%B0%EB%93%B1
    \grep 'krdict\.korean\.go\.kr' \
    | sed "s|.*mainSearchWord=||" \
    | sed "s|[#&].*||"
}

filter_babla_english() {
    \grep -E '.*bab\.la/dictionary/(russian-english|english-russian)' \
        | sed "s|^.*/||" \
        | sed "s|#||g"
    #http://en.bab.la/dictionary/english-korean/%EB%94%94%EB%94%94%EB%8B%A4
}

filter_babla_korean() {
    \grep -E '.*bab\.la/dictionary/(korean-english|english-korean)' \
        | sed "s|^.*/||" \
        | sed "s|#||g"
    #http://en.bab.la/dictionary/english-korean/%EB%94%94%EB%94%94%EB%8B%A4
}

# e.g. huske_3 => huske
remove_trailing_numbers() {
    sed 's|_[0-9]\+$||'
}

# https://enno.dict.cc/?s=gave
filter_norwegian_enno_dict() {
    \grep 'enno.dict.cc' \
        | $HOME/.local/bin/srst-parse-url-query "param" "s"
}

# https://naob.no/ordbok/gave
filter_norwegian_naob() {
    \grep 'naob.no/ordbok' \
        | $HOME/.local/bin/srst-parse-url-query "query_basename"
}

# https://ordbok.uib.no/perl/ordbok.cgi?OPP=gave&ant_bokmaal=5&ant_nynorsk=5&bokmaal=+&ordbok=bokmaal
filter_norwegian_ordbok_uib() {
    \grep 'ordbok.uib.no' \
        | $HOME/.local/bin/srst-parse-url-query "param" "OPP"
}

BHIST_BIN=$HOME/.local/bin/srst-show-browser-history.sh
if [ "$1" == "lingvolive" ]; then
    $BHIST_BIN | urldecode | filter_lingvolive | uniq_keep_order
elif [ "$1" == "krdict" ]; then
    $BHIST_BIN | urldecode | filter_krdict | uniq_keep_order
elif [ "$1" == "babla_english" ]; then
    $BHIST_BIN | urldecode | filter_babla_english | uniq_keep_order
elif [ "$1" == "babla_korean" ]; then
    $BHIST_BIN | urldecode | filter_babla_korean | uniq_keep_order
elif [ "$1" == "norwegian" ]; then
    (
        $BHIST_BIN | urldecode | filter_norwegian_enno_dict;
        $BHIST_BIN | urldecode | filter_norwegian_naob;
        $BHIST_BIN | urldecode | filter_norwegian_ordbok_uib;
    ) | remove_trailing_numbers | uniq_keep_order
else
    echo "Unknown source: \"$1\""
    echo "Pick one: $0 <norwegian | lingvolive | krdict | babla_english | babla_korean>"
    exit 1
fi

#bhist | urldecode | filter_babla_korean | uniq_keep_order
#bhist | urldecode | filter_babla_english | uniq_keep_order
#http://en.bab.la/dictionary/english-russian/scathing
