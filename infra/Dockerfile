FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -U pip
RUN pip3 install -r /app/requirements.txt --no-cache-dir
COPY ../backend /app
CMD ["/app/entrypoint.sh"]