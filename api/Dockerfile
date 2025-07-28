FROM python:3.13-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    build-base \
    curl \
    bash \
    postgresql-dev \
    postgresql-client \
    libffi-dev

# Install Rust for tiktoken
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 