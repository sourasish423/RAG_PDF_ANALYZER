FROM python:3.12-slim
# Start with a lightweight Linux image that already has Python 3.12.

WORKDIR /app

COPY requirements.txt .
# Copy your dependency list into /app.

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Copy the rest of your application code into /app.
# Copy your backend project into the image
EXPOSE 8000
# Document that the application uses port 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]