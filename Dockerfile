# Aplicación demostrativa (R5) en una sola imagen.
# Etapa 1: compilar el frontend (React + Vite) -> web/dist
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Etapa 2: el backend FastAPI sirve la API, las figuras y web/dist
FROM python:3.11-slim
WORKDIR /app
# Solo lo que importa la API (quindio.red usa pyproj); osmnx y compañía no hacen falta aquí
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pyproj
COPY src/ src/
COPY api/ api/
COPY data/catalogo.csv data/catalogo.csv
COPY data/processed/ data/processed/
COPY resultados/ resultados/
COPY --from=web /web/dist web/dist
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
