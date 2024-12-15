# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY app/ /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Set entry point to Streamlit
CMD ["streamlit", "run", "makeMainDB.py", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
