.PHONY: run lint

run:
	rm -rf /tmp/flask
	mkdir -p /tmp/flask
	prometheus_multiproc_dir=/tmp/flask gunicorn -k gevent main:app --workers=2

lint:
	mypy .