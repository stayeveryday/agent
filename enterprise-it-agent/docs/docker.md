# Docker Deployment

## Build

```powershell
docker compose build
```

If Docker Desktop is not running, start Docker Desktop first. Otherwise the Docker CLI may fail to connect to the Linux engine.

## Run

```powershell
docker compose up
```

Health check:

```text
http://127.0.0.1:8000/health
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Notes

- The compose file defaults `EMBEDDING_DEVICE=cpu` so it can run without NVIDIA Docker support.
- Local 3080 Ti CUDA embedding is still best for your Windows virtual environment.
- To use GPU in Docker later, add NVIDIA Container Toolkit and configure the compose service with GPU access.
- `./data` is mounted into the container so the FAISS index and knowledge base are available at runtime.
- Current local validation: `docker compose config` passed, but `docker compose build` requires Docker Desktop Linux engine to be running.
