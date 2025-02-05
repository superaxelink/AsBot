# Definir variables
IMAGE_NAME = jsfechatbottest
CONTAINER_NAME = jsfechatbottestc
ENV_FILE = python-service/DownloadFile/.env
#non detached
PORTS = -p 3000:3000 -p 8765:8765 -p 5000:5000
#detached
#PORTS = -p 3000:3000 -p 8765:8765 -d

# Construir la imagen de Docker
build:
	docker build -t $(IMAGE_NAME) .

# Ejecutar el contenedor de Docker
run:
	docker run --env-file $(ENV_FILE) $(PORTS) --name $(CONTAINER_NAME) $(IMAGE_NAME)

# Limpiar contenedores e imágenes
clean:
	docker rm -f $(CONTAINER_NAME) || true
	docker rmi -f $(IMAGE_NAME) || true

# Atajo para reconstruir y ejecutar
rebuild-run: clean build run
