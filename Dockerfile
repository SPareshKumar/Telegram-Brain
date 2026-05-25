# 1. Use an official, lightweight Python 3.11 image
FROM python:3.11-slim

# 2. Prevent Python from buffering stdout/stderr (keeps logs real-time)
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy your requirements file first (optimizes Docker caching)
COPY requirements.txt .

# 5. Install the exact dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your application code
COPY . .

# 7. Expose the port FastAPI will run on
EXPOSE 8000

# 8. Command to run the application
# We use 0.0.0.0 so the cloud server can route external traffic to it
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]