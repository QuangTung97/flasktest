.PHONY: run lint restart

run:
	rm -rf /tmp/flask
	mkdir -p /tmp/flask
	prometheus_multiproc_dir=/tmp/flask gunicorn -k gevent main:app --workers=1

lint:
	mypy .

restart:
	docker restart redis-server
	docker restart redis2