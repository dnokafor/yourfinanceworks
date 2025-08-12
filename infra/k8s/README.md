### k8s files were not verified yet for now!

Kubernetes manifests for invoice-app

Prerequisites

- A Kubernetes cluster with an Ingress controller (e.g., NGINX Ingress)
- Container registry to push images (or use a local cluster like kind/minikube and load images locally)

Images to build

- `invoice-app-api:latest` built from `./api/Dockerfile`
- `invoice-app-ui:latest` built from `./ui/Dockerfile`
- `invoice-app-ocr:latest` built from `./api/Dockerfile` (same image as API, different command)

Build examples

```bash
# From repo root
docker build -t invoice-app-api:latest ./api
docker build -t invoice-app-ui:latest ./ui
docker build -t invoice-app-ocr:latest ./api

# If using a remote registry
docker tag invoice-app-api:latest <REGISTRY>/invoice-app-api:latest
docker tag invoice-app-ui:latest <REGISTRY>/invoice-app-ui:latest
docker tag invoice-app-ocr:latest <REGISTRY>/invoice-app-ocr:latest
docker push <REGISTRY>/invoice-app-api:latest
docker push <REGISTRY>/invoice-app-ui:latest
docker push <REGISTRY>/invoice-app-ocr:latest
```

Apply manifests

```bash
kubectl apply -k infra/k8s
```

Notes

- Default credentials are for local/dev only. Update `postgres-secret` and `api-secret` before production.
- Ingress assumes an `nginx` IngressClass. Adjust `ingressClassName` or annotations as needed.
- The API runs DB init and Alembic setup on startup, similar to docker-compose. Consider a proper Job/migration flow for production.
- Kafka is a single-node KRaft setup for development. Replace with a managed Kafka or a proper HA deployment for production.

