.PHONY: run

run:
	rm -r /tmp/flask
	mkdir -p /tmp/flask
	prometheus_multiproc_dir=/tmp/flask gunicorn main:app --workers=2
