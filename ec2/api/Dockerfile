FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    boto3 \
    PyJWT \
    bcrypt \
    pydantic \
    python-multipart

COPY ec2/api/ .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]