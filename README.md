# FastAPI on Google Cloud Kubernetes (GKE) - Learning Starter Kit

A production-ready sample **FastAPI** application designed specifically for learning and experimenting with **Kubernetes on Google Cloud Platform (GKE)**.

---

## 📁 Project Structure

```text
kubernetes/
├── app/
│   ├── __init__.py
│   └── main.py             # FastAPI app with GET, POST, DELETE, Health & Stress endpoints
├── k8s/
│   ├── configmap.yaml      # Environment variable configurations
│   ├── deployment.yaml     # 3-replica Deployment with liveness/readiness probes & resource limits
│   ├── service.yaml        # LoadBalancer Service exposing FastAPI to the internet
│   └── hpa.yaml            # Horizontal Pod Autoscaler (scales on CPU utilization)
├── .dockerignore
├── Dockerfile              # Lightweight Python 3.11 container image
├── requirements.txt        # Dependencies (FastAPI, Uvicorn, Pydantic)
└── README.md
```

---

## 🚀 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root status with pod name, environment, and timestamp |
| `GET` | `/healthz` | Kubernetes **Liveness Probe** |
| `GET` | `/ready` | Kubernetes **Readiness Probe** |
| `GET` | `/info` | Pod metadata (Pod name, Pod IP, app version) |
| `GET` | `/api/v1/items` | List items with optional pagination & search |
| `GET` | `/api/v1/items/{id}` | Get single item by ID |
| `POST` | `/api/v1/items` | Create new item |
| `DELETE`| `/api/v1/items/{id}` | Delete item |
| `POST` | `/api/v1/stress` | Generates CPU load to test Kubernetes HPA Autoscaling |
| `GET` | `/docs` | Interactive Swagger UI documentation |

---

## 🧪 Phase 1: Local Development & Testing

### 1. Run with Python directly

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---

### 2. Run with Docker locally

```powershell
# Build Docker image
docker build -t fastapi-gke-demo:v1.0.0 .

# Run container
docker run -d -p 8000:8000 --name fastapi-app fastapi-gke-demo:v1.0.0

# Verify container
curl http://localhost:8000/

# Stop & remove container
docker stop fastapi-app
docker rm fastapi-app
```

---

## ☁️ Phase 2: Deploying to Google Kubernetes Engine (GKE)

### Step 1: Set GCP Variables & Authenticate

```powershell
# Set your GCP Project ID and Region
$PROJECT_ID = "genai-499112"
$REGION = "us-central1"
$CLUSTER_NAME = "fastapi-cluster"
$REPO_NAME = "fastapi-repo"

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID
```

---

### Step 2: Push Image to Google Artifact Registry

```powershell
# 1. Enable Artifact Registry and Kubernetes Engine APIs
gcloud services enable artifactregistry.googleapis.com container.googleapis.com

# 2. Create an Artifact Registry repository
gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$REGION `
    --description="FastAPI Docker repository"

# 3. Configure Docker authentication for GCP Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# 4. Build and tag the Docker image for GCP
$IMAGE_URI = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/fastapi-gke-demo:v1.0.0"
docker build -t $IMAGE_URI .

# 5. Push the image to GCP
docker push $IMAGE_URI
```

---

### Step 3: Create a GKE Cluster

```powershell
# Create an Autopilot cluster (Recommended for beginners - Google manages node provisioning)
gcloud container clusters create-auto $CLUSTER_NAME `
    --location=$REGION

# OR create a Standard GKE cluster:
# gcloud container clusters create $CLUSTER_NAME `
#     --num-nodes=2 `
#     --zone=${REGION}-a `
#     --machine-type=e2-medium

# Connect kubectl to your new GKE cluster
gcloud container clusters get-credentials $CLUSTER_NAME --location=$REGION
```

---

### Step 4: Update Manifest and Deploy

1. Open `k8s/deployment.yaml` and update the `image:` field with your image URI:
   ```yaml
   image: us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/fastapi-repo/fastapi-gke-demo:v1.0.0
   ```

2. Apply the Kubernetes resources:
   ```powershell
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/hpa.yaml
   ```

---

### Step 5: Verify Deployment & Access the Service

```powershell
# Check Pod status (you will see 3 replicas running)
kubectl get pods -o wide

# Check Service to get the EXTERNAL-IP provided by GCP Cloud Load Balancer
kubectl get services --watch
```

Once `EXTERNAL-IP` changes from `<pending>` to a public IP (e.g. `34.120.x.x`):
- Open `http://<EXTERNAL-IP>/docs` in your browser.
- Refresh `http://<EXTERNAL-IP>/` multiple times to watch the `pod_name` change — this demonstrates Kubernetes round-robin load balancing!

---

## 🔍 Phase 3: Learning Kubernetes Concepts with this App

### 1. Test POST & GET Endpoints
```powershell
# Create an item (POST)
curl -X POST "http://<EXTERNAL-IP>/api/v1/items" `
     -H "Content-Type: application/json" `
     -d '{"name": "GKE Demo Item", "description": "Created on Kubernetes", "price": 99.99}'

# Fetch items (GET)
curl "http://<EXTERNAL-IP>/api/v1/items"
```

### 2. Inspect Logs & Pod Details
```powershell
# View logs from all replicas
kubectl logs -l app=fastapi-gke-demo --tail=50 -f

# Describe a specific pod
kubectl describe pod <POD_NAME>
```

### 3. Test Self-Healing (Pod Restart)
```powershell
# Delete a pod and watch Kubernetes automatically spawn a new one to maintain 3 replicas
kubectl delete pod <POD_NAME>
kubectl get pods -w
```

### 4. Test Horizontal Pod Autoscaling (HPA)
```powershell
# Watch HPA status in a terminal window
kubectl get hpa -w

# Trigger CPU stress endpoint
curl -X POST "http://<EXTERNAL-IP>/api/v1/stress?duration_seconds=15"

# Watch Kubernetes automatically scale the deployment from 3 pods up to 8 pods!
```

---

## 🧹 Phase 4: Clean Up (Avoid Unwanted GCP Costs)

When you're done experimenting, delete the resources:

```powershell
# 1. Delete Kubernetes resources
kubectl delete -f k8s/

# 2. Delete the GKE cluster
gcloud container clusters delete $CLUSTER_NAME --location=$REGION --quiet

# 3. (Optional) Delete Artifact Registry repository
gcloud artifacts repositories delete $REPO_NAME --location=$REGION --quiet
```
