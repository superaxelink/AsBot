FROM mysql:8.0.39

COPY low-memory-my.cnf /etc/mysql/my.cnf

# Copy the initialization SQL script into the container
COPY init.sql /docker-entrypoint-initdb.d/

# Set the root password via environment variable
ENV MYSQL_ROOT_PASSWORD=password