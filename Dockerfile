FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirement.txt
EXPOSE 8000
CMD ["python", "app.py"]
