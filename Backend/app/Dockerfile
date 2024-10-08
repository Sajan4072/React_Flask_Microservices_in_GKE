FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app source code
COPY . .

# Expose port 8080 where gunicorn will run
EXPOSE 8080

# Command to run the app using gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8080", "app:app"]

