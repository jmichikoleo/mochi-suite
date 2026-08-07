FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy app
COPY . .

# Create data directories
RUN mkdir -p data/lab/pdfs data/uni/files data/uploads data/briefings

# Expose port
EXPOSE 5050

# Run with gunicorn (production server)
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "--timeout", "120", "src.app:app"]
