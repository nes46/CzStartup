# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev

# Install Python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Add a script to wait for the database to be ready before starting the application
COPY ./wait-for-it.sh /usr/src/app/wait-for-it.sh
RUN chmod +x /usr/src/app/wait-for-it.sh

# Command to run the application
CMD ["./wait-for-it.sh", "db:5432", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]