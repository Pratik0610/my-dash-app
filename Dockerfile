# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy your application
COPY . .

# Expose port
EXPOSE 8000

# Run the web server
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8000"]
