# Docker Setup

## Pull the Docker Image

```bash
docker pull <your-dockerhub-username>/redrobproj:latest
```

## Run the Docker Container

```bash
docker run -p 8000:8000 <your-dockerhub-username>/redrobproj:latest
```

The application will be available at:

```
http://localhost:8000
```

---

# Building the Docker Image

Clone the repository:

```bash
git clone <your-github-repository-url>
cd RedRobProj
```

Build the Docker image:

```bash
docker build -t redrobproj .
```

Run the container:

```bash
docker run -p 8000:8000 redrobproj
```

---

# Push Image to Docker Hub

Login to Docker Hub:

```bash
docker login
```

Tag the image:

```bash
docker tag redrobproj <your-dockerhub-username>/redrobproj:latest
```

Push the image:

```bash
docker push <your-dockerhub-username>/redrobproj:latest
```

---

# Verify the Uploaded Image

```bash
docker pull <your-dockerhub-username>/redrobproj:latest
docker run -p 8000:8000 <your-dockerhub-username>/redrobproj:latest
```

---

# Docker Image

```
docker.io/<your-dockerhub-username>/redrobproj:latest
```

---

# Notes

* The image contains both the React frontend and FastAPI backend.
* The application listens on port **8000**.
* Ensure Docker Desktop has at least **6 GB RAM** allocated for smooth execution due to the ML models used by the project.
