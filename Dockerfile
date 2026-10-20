FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY src ./src
COPY app ./app

RUN uv pip install --system -e ".[docling]"

EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address", "0.0.0.0"]
