"""
Enterprise MLOps Platform API
FastAPI application for managing models, deployments, and features

Implements:
- ADR-005: Model Registry integration (MLflow)
- ADR-002: Feature Store integration (Feast)
- ADR-010: Governance Framework (approvals, auditing)
- ADR-007: Security & Compliance (authentication, authorization)
"""

from fastapi import FastAPI, HTTPException, Depends, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import logging
import os
import mlflow
from feast import FeatureStore
import boto3
import json

# JWT validation against a configurable OIDC issuer. Imported defensively
# so the module remains importable in unit tests that mock the verifier.
try:  # pragma: no cover - exercised only when JWT lib is installed
    from jose import JWTError, jwt
except ImportError:  # pragma: no cover - fallback for minimal envs
    JWTError = Exception  # type: ignore[assignment]
    jwt = None  # type: ignore[assignment]

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise MLOps Platform API",
    description="API for managing ML models, deployments, and features",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# MLflow client
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlflow.svc.cluster.local"))

# Feast client
feature_store = FeatureStore(repo_path=os.getenv("FEAST_REPO_PATH", "/feast-repo"))

# JWT configuration
JWT_ISSUER = os.getenv("JWT_ISSUER", "https://auth.example.com/")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "mlops-platform")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

# Audit log destination (CloudWatch Logs group). When unset, audit
# entries fall through to structured logging only.
AUDIT_LOG_GROUP = os.getenv("AUDIT_LOG_GROUP", "")
AUDIT_LOG_STREAM = os.getenv("AUDIT_LOG_STREAM", "mlops-platform-api")
audit_client = boto3.client("logs") if AUDIT_LOG_GROUP else None

# In-memory RBAC policy. In production this would be a call out to an
# IAM / Open Policy Agent endpoint, but we keep the policy data co-
# located so the API stays runnable in CI and on a developer laptop.
_RBAC_POLICY: Dict[str, Dict[str, List[str]]] = {
    "platform-admin": {"*": ["*"]},
    "ml-engineer": {
        "model": ["register", "deploy:staging", "predict"],
        "feature": ["create", "read"],
    },
    "data-scientist": {
        "model": ["register", "predict"],
        "feature": ["read"],
    },
    "viewer": {"*": ["read"]},
}


# Prometheus metrics registry. Keep it isolated from the global default
# registry so tests can construct fresh instances.
metrics_registry = CollectorRegistry()
http_requests_total = Counter(
    "platform_api_requests_total",
    "Total HTTP requests against the MLOps platform API",
    ["method", "endpoint", "status"],
    registry=metrics_registry,
)
http_request_duration_seconds = Histogram(
    "platform_api_request_duration_seconds",
    "Latency of MLOps platform API endpoints",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=metrics_registry,
)
model_predictions_total = Counter(
    "platform_api_predictions_total",
    "Total model predictions served by the MLOps platform API",
    ["model_name", "status"],
    registry=metrics_registry,
)

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
approvals_table = dynamodb.Table(os.getenv("APPROVALS_TABLE", "mlops-approvals"))

# ======================
# Models (Pydantic)
# ======================

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ModelStatus(str, Enum):
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ModelMetadata(BaseModel):
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    description: Optional[str] = Field(None, description="Model description")
    risk_level: RiskLevel = Field(..., description="Risk classification")
    owner: str = Field(..., description="Model owner email")
    tags: Optional[Dict[str, str]] = Field(default_factory=dict)

    @validator('owner')
    def validate_owner(cls, v):
        if '@' not in v:
            raise ValueError('Owner must be a valid email address')
        return v

class ModelRegistrationRequest(BaseModel):
    metadata: ModelMetadata
    model_uri: str = Field(..., description="URI to model artifacts (s3://...)")
    training_dataset_uri: Optional[str] = Field(None, description="URI to training data")
    metrics: Optional[Dict[str, float]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ModelDeploymentRequest(BaseModel):
    model_name: str
    model_version: str
    target_stage: ModelStatus = Field(..., description="Target deployment stage")
    replicas: int = Field(default=3, ge=1, le=100)
    resources: Optional[Dict[str, str]] = Field(default_factory=dict)
    environment_vars: Optional[Dict[str, str]] = Field(default_factory=dict)
    justification: str = Field(..., description="Business justification for deployment")

class ApprovalRequest(BaseModel):
    request_id: str
    request_type: str = Field(..., description="Type of request (model_deployment, etc.)")
    requester: str
    approver: str
    status: ApprovalStatus
    comments: Optional[str] = None

class FeatureRetrievalRequest(BaseModel):
    entity_ids: List[str] = Field(..., description="List of entity IDs")
    feature_refs: List[str] = Field(..., description="Feature references (feature_view:feature)")

class ModelPredictionRequest(BaseModel):
    model_name: str
    model_version: Optional[str] = Field(default="latest")
    input_data: Dict[str, Any] = Field(..., description="Input features for prediction")
    return_explanations: bool = Field(default=False)

# ======================
# Dependency Injection
# ======================

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Verify the bearer JWT and return the decoded claims.

    Returns a claims dict with at least ``sub`` (subject / email) and
    ``roles`` (list of strings) so downstream handlers can make
    authorisation decisions.

    In production this validates against the configured Okta / Auth0 /
    Cognito issuer. In dev (no JWT_PUBLIC_KEY configured) the function
    accepts an unsigned token claiming ``sub`` for fast iteration —
    callers can lock this down by setting ``JWT_PUBLIC_KEY``.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    if jwt is None or not JWT_PUBLIC_KEY:
        logger.warning(
            "JWT validation skipped because python-jose / JWT_PUBLIC_KEY "
            "are unset. Decoding token unverified."
        )
        try:
            claims = jwt.get_unverified_claims(token) if jwt is not None else {}
        except Exception:
            claims = {}
        return {
            "sub": claims.get("sub", "user@company.com"),
            "roles": claims.get("roles", ["viewer"]),
        }

    try:
        claims = jwt.decode(
            token,
            JWT_PUBLIC_KEY,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
    except JWTError as exc:
        logger.warning("Token validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    if "sub" not in claims:
        raise HTTPException(status_code=401, detail="Token missing subject claim")
    claims.setdefault("roles", claims.get("groups", []) or ["viewer"])
    return claims


def check_permission(user: Any, action: str, resource: str) -> bool:
    """Return True iff the caller's roles grant ``action`` on ``resource``.

    ``user`` may be either the legacy string subject (for backward
    compatibility) or a dict of decoded JWT claims. Permissions are
    looked up against the in-memory ``_RBAC_POLICY``.
    """
    if isinstance(user, dict):
        subject = user.get("sub", "unknown")
        roles = user.get("roles", []) or []
    else:
        subject = str(user)
        roles = ["viewer"]

    for role in roles:
        scopes = _RBAC_POLICY.get(role, {})
        permitted_actions = set(scopes.get(resource, [])) | set(scopes.get("*", []))
        if "*" in permitted_actions or action in permitted_actions:
            logger.info(
                "permission_granted user=%s role=%s action=%s resource=%s",
                subject,
                role,
                action,
                resource,
            )
            return True

    logger.warning(
        "permission_denied user=%s roles=%s action=%s resource=%s",
        subject,
        roles,
        action,
        resource,
    )
    return False

# ======================
# Health & Monitoring
# ======================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies dependencies"""
    checks = {
        "mlflow": False,
        "feast": False,
        "dynamodb": False
    }

    try:
        # Check MLflow
        mlflow.get_tracking_uri()
        checks["mlflow"] = True
    except Exception as e:
        logger.error(f"MLflow health check failed: {e}")

    try:
        # Check Feast
        feature_store.list_feature_views()
        checks["feast"] = True
    except Exception as e:
        logger.error(f"Feast health check failed: {e}")

    try:
        # Check DynamoDB
        approvals_table.table_status
        checks["dynamodb"] = True
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {e}")

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks},
        status_code=status_code
    )

@app.get("/metrics", tags=["Monitoring"])
async def metrics() -> Response:
    """Expose the Prometheus metrics for scraping."""
    return Response(
        content=generate_latest(metrics_registry),
        media_type=CONTENT_TYPE_LATEST,
    )

# ======================
# Model Management
# ======================

@app.post("/api/v1/models/register", tags=["Models"])
async def register_model(
    request: ModelRegistrationRequest,
    background_tasks: BackgroundTasks,
    user: str = Depends(verify_token)
):
    """
    Register a new model version in MLflow

    Implements:
    - ADR-005: Model Registry
    - ADR-010: Governance Framework (risk classification)
    """
    try:
        # Validate user permissions
        if not check_permission(user, "register_model", request.metadata.name):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Register model in MLflow
        with mlflow.start_run() as run:
            # Log parameters
            if request.parameters:
                mlflow.log_params(request.parameters)

            # Log metrics
            if request.metrics:
                mlflow.log_metrics(request.metrics)

            # Log model
            mlflow.register_model(
                model_uri=request.model_uri,
                name=request.metadata.name,
                tags={
                    **request.metadata.tags,
                    "risk_level": request.metadata.risk_level.value,
                    "owner": request.metadata.owner,
                    "registered_by": user
                }
            )

        # Create audit log entry
        background_tasks.add_task(
            create_audit_log,
            action="model_registered",
            user=user,
            resource=f"{request.metadata.name}:{request.metadata.version}",
            details=request.dict()
        )

        logger.info(f"Model registered: {request.metadata.name}:{request.metadata.version} by {user}")

        return {
            "status": "success",
            "model_name": request.metadata.name,
            "model_version": request.metadata.version,
            "run_id": run.info.run_id,
            "message": "Model registered successfully"
        }

    except Exception as e:
        logger.error(f"Model registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/{model_name}/versions", tags=["Models"])
async def list_model_versions(
    model_name: str,
    user: str = Depends(verify_token)
):
    """List all versions of a model"""
    try:
        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")

        return {
            "model_name": model_name,
            "versions": [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "status": v.status,
                    "created_at": v.creation_timestamp,
                    "tags": v.tags
                }
                for v in versions
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list model versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/deploy", tags=["Models"])
async def deploy_model(
    request: ModelDeploymentRequest,
    background_tasks: BackgroundTasks,
    user: str = Depends(verify_token)
):
    """
    Deploy model to specified stage

    Implements:
    - ADR-010: Governance Framework (approval workflows)
    """
    try:
        # Get model metadata
        client = mlflow.tracking.MlflowClient()
        model_version = client.get_model_version(request.model_name, request.model_version)
        risk_level = model_version.tags.get("risk_level", "medium")

        # Check if approval is required
        requires_approval = (
            (risk_level == "high" and request.target_stage == ModelStatus.PRODUCTION) or
            (risk_level == "medium" and request.target_stage == ModelStatus.PRODUCTION)
        )

        if requires_approval:
            # Create approval request
            approval_id = create_approval_request(
                request_type="model_deployment",
                requester=user,
                resource=f"{request.model_name}:{request.model_version}",
                details=request.dict(),
                risk_level=risk_level
            )

            return {
                "status": "pending_approval",
                "approval_id": approval_id,
                "message": f"Deployment requires approval (risk level: {risk_level})"
            }

        # Auto-approve for low-risk models or non-production deployments
        deployment_id = execute_deployment(request)

        # Create audit log
        background_tasks.add_task(
            create_audit_log,
            action="model_deployed",
            user=user,
            resource=f"{request.model_name}:{request.model_version}",
            details=request.dict()
        )

        return {
            "status": "success",
            "deployment_id": deployment_id,
            "message": "Model deployed successfully"
        }

    except Exception as e:
        logger.error(f"Model deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ======================
# Feature Management
# ======================

@app.post("/api/v1/features/retrieve", tags=["Features"])
async def retrieve_features(
    request: FeatureRetrievalRequest,
    user: str = Depends(verify_token)
):
    """
    Retrieve features from Feast feature store

    Implements: ADR-002 (Feature Store - Feast)
    """
    try:
        # Retrieve features
        feature_vector = feature_store.get_online_features(
            features=request.feature_refs,
            entity_rows=[{"entity_id": eid} for eid in request.entity_ids]
        ).to_dict()

        logger.info(f"Retrieved features for {len(request.entity_ids)} entities by {user}")

        return {
            "status": "success",
            "features": feature_vector,
            "entity_count": len(request.entity_ids)
        }

    except Exception as e:
        logger.error(f"Feature retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/features/views", tags=["Features"])
async def list_feature_views(user: str = Depends(verify_token)):
    """List all available feature views"""
    try:
        feature_views = feature_store.list_feature_views()

        return {
            "feature_views": [
                {
                    "name": fv.name,
                    "entities": [e.name for e in fv.entities],
                    "features": [f.name for f in fv.features],
                    "ttl": str(fv.ttl) if fv.ttl else None
                }
                for fv in feature_views
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list feature views: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ======================
# Model Inference
# ======================

@app.post("/api/v1/predict", tags=["Inference"])
async def predict(
    request: ModelPredictionRequest,
    user: str = Depends(verify_token)
):
    """
    Make prediction using deployed model
    """
    try:
        # Load model from MLflow
        model_uri = f"models:/{request.model_name}/{request.model_version}"
        model = mlflow.pyfunc.load_model(model_uri)

        # Make prediction
        import pandas as pd
        input_df = pd.DataFrame([request.input_data])
        prediction = model.predict(input_df)

        response = {
            "status": "success",
            "model_name": request.model_name,
            "model_version": request.model_version,
            "prediction": prediction.tolist() if hasattr(prediction, 'tolist') else prediction
        }

        # Add explanations if requested. SHAP is heavy to import, so we
        # defer the import until a caller actually asks for explanations.
        if request.return_explanations:
            try:
                import shap

                explainer = shap.Explainer(model.predict, input_df)
                shap_values = explainer(input_df)
                response["explanations"] = {
                    "method": "shap",
                    "feature_names": list(input_df.columns),
                    "shap_values": shap_values.values.tolist(),
                    "base_values": (
                        shap_values.base_values.tolist()
                        if hasattr(shap_values, "base_values")
                        else None
                    ),
                }
            except Exception as exc:
                logger.warning("SHAP explanation failed: %s", exc)
                response["explanations"] = {
                    "method": "shap",
                    "error": "Explanation could not be computed",
                    "detail": str(exc),
                }

        logger.info(f"Prediction made with {request.model_name}:{request.model_version}")

        return response

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ======================
# Helper Functions
# ======================

def create_approval_request(request_type: str, requester: str, resource: str, details: dict, risk_level: str) -> str:
    """Create approval request in DynamoDB"""
    import uuid
    approval_id = str(uuid.uuid4())

    approvals_table.put_item(Item={
        'approval_id': approval_id,
        'request_type': request_type,
        'requester': requester,
        'resource': resource,
        'details': json.dumps(details),
        'risk_level': risk_level,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'ttl': int((datetime.utcnow().timestamp() + 30*24*3600))  # 30 days
    })

    logger.info(f"Created approval request: {approval_id}")
    return approval_id

def execute_deployment(request: ModelDeploymentRequest) -> str:
    """Apply a KServe InferenceService manifest for the requested model.

    The manifest is built from the request payload and applied via the
    Kubernetes Python client. If the cluster is unreachable (CI, local
    dev) the function falls back to logging the manifest it would have
    applied so the caller can still observe the intent.
    """
    import uuid

    deployment_id = str(uuid.uuid4())
    namespace = getattr(request, "namespace", "ml-models")
    service_name = f"{request.model_name.lower().replace('_', '-')}-{deployment_id[:8]}"
    inference_service = {
        "apiVersion": "serving.kserve.io/v1beta1",
        "kind": "InferenceService",
        "metadata": {
            "name": service_name,
            "namespace": namespace,
            "annotations": {
                "platform.mlops/deployment-id": deployment_id,
                "platform.mlops/model-version": request.model_version,
            },
        },
        "spec": {
            "predictor": {
                "serviceAccountName": "kserve-default",
                "minReplicas": getattr(request, "min_replicas", 1),
                "maxReplicas": getattr(request, "max_replicas", 5),
                "containerConcurrency": getattr(request, "concurrency", 0),
                "model": {
                    "modelFormat": {"name": getattr(request, "model_format", "sklearn")},
                    "storageUri": (
                        f"models://{request.model_name}/{request.model_version}"
                    ),
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "1Gi"},
                        "limits": {"cpu": "2", "memory": "4Gi"},
                    },
                },
            }
        },
    }

    try:  # pragma: no cover - depends on cluster availability
        from kubernetes import client as k8s_client
        from kubernetes import config as k8s_config

        try:
            k8s_config.load_incluster_config()
        except Exception:
            k8s_config.load_kube_config()
        custom = k8s_client.CustomObjectsApi()
        custom.create_namespaced_custom_object(
            group="serving.kserve.io",
            version="v1beta1",
            namespace=namespace,
            plural="inferenceservices",
            body=inference_service,
        )
        logger.info(
            "deployment_applied id=%s service=%s namespace=%s",
            deployment_id,
            service_name,
            namespace,
        )
    except Exception as exc:
        logger.warning(
            "Kubernetes apply failed (%s); logging manifest instead.", exc
        )
        logger.info(
            "deployment_manifest id=%s body=%s",
            deployment_id,
            json.dumps(inference_service),
        )
    return deployment_id

async def create_audit_log(action: str, user: str, resource: str, details: dict) -> None:
    """Persist an audit-log entry both to CloudWatch and the local log.

    Auditing is best-effort but never raises — losing an audit entry
    should not break a user-facing request. The serialized entry is
    pushed to CloudWatch when ``AUDIT_LOG_GROUP`` is configured; the
    local structured logger always emits the entry as a JSON line so
    Fluent Bit / Filebeat / etc. can pick it up regardless.
    """
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "user": user,
        "resource": resource,
        "details": details,
    }
    serialized = json.dumps(audit_entry)
    logger.info("audit_log %s", serialized)

    if audit_client is None:
        return

    try:
        audit_client.put_log_events(
            logGroupName=AUDIT_LOG_GROUP,
            logStreamName=AUDIT_LOG_STREAM,
            logEvents=[
                {
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "message": serialized,
                }
            ],
        )
    except Exception as exc:
        logger.error("audit_log_dispatch_failed exception=%s entry=%s", exc, serialized)

# ======================
# Error Handlers
# ======================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )

# ======================
# Startup/Shutdown
# ======================

@app.on_event("startup")
async def startup_event():
    logger.info("MLOps Platform API starting up...")
    logger.info(f"MLflow URI: {mlflow.get_tracking_uri()}")
    logger.info(f"Feast repo: {os.getenv('FEAST_REPO_PATH', '/feast-repo')}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("MLOps Platform API shutting down...")

# ======================
# Run Application
# ======================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
