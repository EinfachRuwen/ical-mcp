FROM python:3.12-slim

WORKDIR /app

# Copy the project files
COPY . .

# Install the project and its dependencies
RUN pip install --no-cache-dir .

# Expose the default HTTP port
EXPOSE 8093

# Run the MCP server on 0.0.0.0 so it's accessible from outside the container
CMD ["ical-mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8093"]
