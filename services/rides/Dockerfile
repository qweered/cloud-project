FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY rides/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common module first
COPY common ./common

# Copy service files
COPY rides .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 