import os
import socket
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="GCP Kubernetes FastAPI Demo",
    description="Sample FastAPI app with GET & POST endpoints designed for learning GCP Kubernetes (GKE)",
    version="1.0.0",
)

# In-memory storage for learning/demo purposes
items_db: Dict[int, dict] = {
    1: {"id": 1, "name": "Cloud Run Item", "description": "Sample item 1", "price": 19.99, "created_at": datetime.utcnow().isoformat()},
    2: {"id": 2, "name": "GKE Cluster Item", "description": "Sample item 2", "price": 49.99, "created_at": datetime.utcnow().isoformat()},
}


class ItemCreate(BaseModel):
    name: str = Field(..., example="Kubernetes Pod Item", min_length=2, max_length=50)
    description: Optional[str] = Field(None, example="Item deployed via Kubernetes deployment")
    price: float = Field(..., gt=0, example=29.99)


class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    created_at: str
    served_by_pod: str


class PodInfoResponse(BaseModel):
    pod_name: str
    pod_ip: str
    environment: str
    app_version: str
    system_time: str


@app.get("/", summary="Root Endpoint - Pod & Server Status")
def root():
    """
    Returns server details and pod hostname.
    Useful to verify load balancing when refreshing requests across multiple Kubernetes replicas.
    """
    pod_name = os.getenv("HOSTNAME", socket.gethostname())
    environment = os.getenv("APP_ENV", "development")
    return {
        "message": "Welcome to FastAPI on GCP Kubernetes (GKE)!",
        "pod_name": pod_name,
        "environment": environment,
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs",
    }


@app.get("/healthz", summary="Liveness Probe Endpoint")
def healthz():
    """Kubernetes liveness probe to verify the application is running."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/ready", summary="Readiness Probe Endpoint")
def readiness():
    """Kubernetes readiness probe to verify the application is ready to accept traffic."""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@app.get("/info", response_model=PodInfoResponse, summary="Pod & Environment Metadata")
def pod_info():
    """Detailed pod information to inspect Kubernetes pod details and environment variables."""
    pod_name = os.getenv("HOSTNAME", socket.gethostname())
    pod_ip = socket.gethostbyname(socket.gethostname())
    environment = os.getenv("APP_ENV", "development")
    app_version = os.getenv("APP_VERSION", "1.0.0")
    
    return {
        "pod_name": pod_name,
        "pod_ip": pod_ip,
        "environment": environment,
        "app_version": app_version,
        "system_time": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/items", response_model=List[ItemResponse], summary="GET all items")
def get_items(skip: int = 0, limit: int = 10, search: Optional[str] = None):
    """Retrieve a list of items with optional search filter."""
    pod_name = os.getenv("HOSTNAME", socket.gethostname())
    results = list(items_db.values())
    
    if search:
        search_lower = search.lower()
        results = [item for item in results if search_lower in item["name"].lower() or (item["description"] and search_lower in item["description"].lower())]
    
    paginated = results[skip : skip + limit]
    return [{**item, "served_by_pod": pod_name} for item in paginated]


@app.get("/api/v1/items/{item_id}", response_model=ItemResponse, summary="GET item by ID")
def get_item(item_id: int):
    """Retrieve a single item by its ID."""
    pod_name = os.getenv("HOSTNAME", socket.gethostname())
    if item_id not in items_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID {item_id} not found")
    
    item = items_db[item_id]
    return {**item, "served_by_pod": pod_name}


@app.post("/api/v1/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, summary="POST create new item")
def create_item(payload: ItemCreate):
    """Create a new item and store it in memory."""
    pod_name = os.getenv("HOSTNAME", socket.gethostname())
    new_id = max(items_db.keys(), default=0) + 1
    new_item = {
        "id": new_id,
        "name": payload.name,
        "description": payload.description,
        "price": payload.price,
        "created_at": datetime.utcnow().isoformat(),
    }
    items_db[new_id] = new_item
    return {**new_item, "served_by_pod": pod_name}


@app.delete("/api/v1/items/{item_id}", status_code=status.HTTP_200_OK, summary="DELETE item by ID")
def delete_item(item_id: int):
    """Delete an item by its ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID {item_id} not found")
    
    deleted_item = items_db.pop(item_id)
    return {"message": f"Item {item_id} deleted successfully", "deleted_item": deleted_item}


@app.post("/api/v1/stress", summary="Simulate CPU Load (for testing HPA scaling)")
def stress_cpu(duration_seconds: int = 5):
    """
    Simulates CPU activity for `duration_seconds` (capped at 20s).
    Useful to test Kubernetes Horizontal Pod Autoscaler (HPA) triggers.
    """
    duration = min(max(duration_seconds, 1), 20)
    end_time = time.time() + duration
    
    # Run busy loop
    count = 0
    while time.time() < end_time:
        count += 1
        _ = 999999 ** 2
        
    pod_name = os.getenv("HOSTNAME", socket.gethostname())
    return {
        "message": f"Simulated CPU load for {duration} seconds",
        "iterations": count,
        "pod_name": pod_name,
    }
