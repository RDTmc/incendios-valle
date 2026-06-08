FROM python:3.11-slim

RUN useradd -m app
WORKDIR /app

RUN pip install --no-cache-dir --only-binary :all: \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    boto3==1.34.0 \
    PyJWT==2.8.0 \
    bcrypt==4.1.0 \
    pydantic==2.5.2 \
    python-multipart==0.0.6 \
    httpx==0.26.0

COPY ec2/api/ .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

USER app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]