# ---------- Stage 1 : Build React ----------
FROM node:22 AS frontend

WORKDIR /client

COPY client/package*.json ./

RUN npm install

COPY client/ .

RUN npm run build


# ---------- Stage 2 : FastAPI ----------
FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt .

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY server/ .

# Copy React build
COPY --from=frontend /client/dist ./static

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]