# Use the official Python image as the base
FROM python:3.10

# Install dependencies for Java (including Java 17)
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy the application code into the container
COPY . .

# Install pip and dependencies from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir .

# Expose the port for the FastAPI app
EXPOSE 8080

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "vehicle_routing.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
