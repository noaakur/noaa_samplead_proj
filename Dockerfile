# Use official PostgreSQL image as base
FROM postgres:15-alpine

# Set environment variables for database configuration
ENV POSTGRES_DB=samplead_db
ENV POSTGRES_USER=dbuser
ENV POSTGRES_PASSWORD=dbpassword
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Copy initialization scripts
# Scripts in /docker-entrypoint-initdb.d/ run automatically on first startup
COPY ./init-scripts/ /docker-entrypoint-initdb.d/

# Expose PostgreSQL default port
EXPOSE 5432

# Optional: Configure PostgreSQL settings
# Uncomment and modify as needed
# CMD ["postgres", "-c", "max_connections=100", "-c", "shared_buffers=256MB"]


