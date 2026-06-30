# Docker Setup

This project is containerized using Docker and includes both the **React frontend** and **FastAPI backend** in a single image.

---

# Pull the Docker Image

```bash
docker pull amoghkashyapsn/redrobproj:latest
```

---

# Run the Docker Container

```bash
docker run --rm -p 8000:8000 --name redrob amoghkashyapsn/redrobproj:latest
```

The application will be available at:

```
http://localhost:8000
```

---

# Build the Docker Image Locally

Clone the repository:

```bash
git clone <your-github-repository-url>
cd RedRobProj
```

Build the Docker image:

```bash
docker build -t redrobproj:latest .
```

Run the image:

```bash
docker run --rm -p 8000:8000 --name redrob redrobproj:latest
```

---

# Push the Image to Docker Hub

Login to Docker Hub:

```bash
docker login
```

Tag the image:

```bash
docker tag redrobproj:latest amoghkashyapsn/redrobproj:latest
```

Push the image:

```bash
docker push amoghkashyapsn/redrobproj:latest
```

---

# Verify the Published Image

Pull the image:

```bash
docker pull amoghkashyapsn/redrobproj:latest
```

Run it:

```bash
docker run --rm -p 8000:8000 amoghkashyapsn/redrobproj:latest
```

---

# Docker Image

```text
docker.io/amoghkashyapsn/redrobproj:latest
```

---

# Useful Docker Commands

List local images:

```bash
docker images
```

List running containers:

```bash
docker ps
```

List all containers:

```bash
docker ps -a
```

Stop a running container:

```bash
docker stop redrob
```

Remove a container:

```bash
docker rm redrob
```

Remove the Docker image:

```bash
docker rmi amoghkashyapsn/redrobproj:latest
```

---

# Notes

- The Docker image contains both the **React frontend** and **FastAPI backend**.
- The application is exposed on **port 8000**.
- The image uses the **CPU-only PyTorch** build to reduce image size and improve compatibility.
- Ensure port **8000** is available before starting the container.
- The application downloads and loads the required ML model during startup if it is not already available.
- For large candidate datasets, running on a system with **16 GB RAM or more** is recommended for the best performance.