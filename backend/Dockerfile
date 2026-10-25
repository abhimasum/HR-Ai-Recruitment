FROM python:3.12-slim
WORKDIR /code
COPY requirements.txt .
COPY requirements-huggingface.txt .
ARG EMBEDDING_PROVIDER=vertexai
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && if [ "$EMBEDDING_PROVIDER" = "huggingface" ]; then \
        python -m pip install --no-cache-dir -r requirements-huggingface.txt; \
    fi
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
