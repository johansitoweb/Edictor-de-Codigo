FROM python:3.11
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir tk
RUN pip install --no-cache-dir .
CMD ["python", "app.py"] 