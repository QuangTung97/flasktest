.PHONY: run

run:
	mkdir -p /tmp/flask
	rm /tmp/flask/*
	PROMETHEUS_MULTIPROC_DIR=/tmp/flask gunicorn main:app --workers=2 --timeout=90
