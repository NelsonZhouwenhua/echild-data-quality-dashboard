.PHONY: run test app clean

run:
	python run_pipeline.py --n-children 5000

test:
	python run_pipeline.py --n-children 1500
	pytest -q

app:
	streamlit run app.py

clean:
	rm -f data/raw/*.csv data/internal/*.csv data/processed/*.csv data/processed/*.db
