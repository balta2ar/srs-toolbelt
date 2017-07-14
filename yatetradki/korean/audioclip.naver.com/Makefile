
.PHONY: html images run_server

html:
	python -c 'import handler; handler.generate_html("./audioclip-naver-ripped/*description-response.json")'

index:
	python -c 'import handler; handler.generate_index("./audioclip-naver-ripped/*description-response.json")'

run_server:
	sudo mitmdump --host -s "audioclip.py --flowfilter '~u channels/57'"
