# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

# Running port
ENV PORT 9000

# Setting PYTHONUNBUFFERED to a non-empty value different from 0 ensures that the python output i.e. the stdout and stderr
# streams are sent straight to terminal (e.g. your container log) without being first buffered and that you can see the
# output of your application in real time.
ENV PYTHONUNBUFFERED=1

# Globally defined build args
ARG ENV_REQ=requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code to the working directory
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r $ENV_REQ

# Expose the port on which the application will run
EXPOSE 9000
