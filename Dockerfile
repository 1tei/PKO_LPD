# syntax=docker/dockerfile:1

# Stage 1: Dependency Resolution
FROM python:3.10 AS dependencies
LABEL stage="dependencies"
WORKDIR /app

# Install necessary dependencies for Python and Java
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (including uvicorn)
COPY setup.py .
RUN pip install --no-cache-dir .

################################################################################

# Stage 2: Build Application
FROM dependencies AS builder
LABEL stage="build"
WORKDIR /app

# Copy source code and prepare the application
COPY . .

################################################################################

# Stage 3: Runtime
FROM python:3.10 AS runtime
LABEL stage="runtime"
WORKDIR /app

# Copy runtime artifacts from the builder stage
COPY --from=builder /app /app

# Add Java runtime (OpenJDK 17)
RUN find /usr -name "java-17-openjdk*" -exec cp -r {} /usr/lib/jvm/ \;

# Set JAVA_HOME and PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install Uvicorn explicitly
RUN pip install uvicorn

# Expose necessary ports
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
