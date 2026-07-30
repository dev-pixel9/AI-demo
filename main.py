import os
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import all project modules
from projects.p01_api_wrapper import APIWrapperEngine, APIRequestPayload
from projects.p02_cost_estimator import TokenCostEstimator
from projects.p03_json_agent import ValidatedJSONAgent, UserProfileSchema, ProductAnalysisSchema
from projects.p04_cited_rag import CitedRAGBot
from projects.p05_hitl_workflow import HITLWorkflowEngine
from projects.p06_streaming_copilot import StreamingCopilotEngine
from projects.p07_eval_harness import EvalHarness
from projects.p08_local_inference import LocalInferenceServer
from projects.p09_traced_pipeline import TracedPipelineEngine
from projects.p10_security_guardrails import SecurityGuardrailMiddleware
from projects.p11_architecture_docs import ArchitectureDocsGenerator

app = FastAPI(
    title="12 GenAI Enterprise Production Suite",
    description="Unified API & Portfolio Server for 12 GenAI Projects",
    version="1.0.0"
)

# Instantiate engine services
p01_gateway = APIWrapperEngine()
p02_cost_engine = TokenCostEstimator()
p03_json_agent = ValidatedJSONAgent()
p04_rag_bot = CitedRAGBot()
p05_hitl_engine = HITLWorkflowEngine()
p06_copilot_engine = StreamingCopilotEngine()
p07_eval_harness = EvalHarness()
p08_local_server = LocalInferenceServer()
p09_tracer = TracedPipelineEngine()
p10_guardrails = SecurityGuardrailMiddleware()

# Static Files Setup
STATIC_DIR = os.path.join(os.path.dirname(__file__), "projects", "p12_portfolio", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_portfolio():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return "<h1>12 GenAI Enterprise Projects Server Running</h1>"


# --- PROJECT 01: API WRAPPER GATEWAY ---
@app.post("/api/p01/execute")
async def execute_p01_request(payload: APIRequestPayload):
    span = p09_tracer.start_trace("APIWrapper_Gateway_Execute", attributes={"client_id": payload.client_id})
    res = await p01_gateway.execute_request(payload)
    status_str = "OK" if res.status == "SUCCESS" else "ERROR"
    p09_tracer.end_trace(span.span_id, status=status_str, cost_usd=0.0005)
    return res


# --- PROJECT 02: TOKEN COST ESTIMATOR ---
class EstimateRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o"
    max_tokens: int = 500
    client_id: str = "demo_client"


@app.post("/api/p02/estimate")
async def estimate_p02_cost(req: EstimateRequest):
    span = p09_tracer.start_trace("CostEstimator_PreGenEstimate")
    est = p02_cost_engine.estimate_cost(req.prompt, req.max_tokens, req.model)
    budget = p02_cost_engine.check_budget(req.client_id, est["total_estimated_cost_usd"])
    
    # Record actual usage simulation
    usage = p02_cost_engine.record_actual_usage(
        req.client_id, "/api/p02/estimate", req.model, req.prompt, "Simulated output generation"
    )
    p09_tracer.end_trace(span.span_id, cost_usd=usage.cost_usd)
    return {
        "estimate": est,
        "budget_status": budget,
        "usage_logged": usage
    }


# --- PROJECT 03: VALIDATED JSON AGENT ---
class JSONAgentRequest(BaseModel):
    prompt: str = "Generate a user profile"
    schema_type: str = "UserProfileSchema"
    simulate_initial_error: bool = False


@app.post("/api/p03/run")
async def run_p03_json_agent(req: JSONAgentRequest):
    span = p09_tracer.start_trace("JSONAgent_ValidateSchema")
    schema = UserProfileSchema if req.schema_type == "UserProfileSchema" else ProductAnalysisSchema
    validated_result, logs = p03_json_agent.run_validated_generation(
        req.prompt, schema, req.simulate_initial_error
    )
    p09_tracer.end_trace(span.span_id, cost_usd=0.001)
    return {
        "validated_json": validated_result.model_dump() if validated_result else None,
        "validation_logs": [log.model_dump() for log in logs]
    }


# --- PROJECT 04: CITED RAG BOT ---
class RAGRequest(BaseModel):
    query: str


@app.post("/api/p04/query")
async def query_p04_rag(req: RAGRequest):
    span = p09_tracer.start_trace("CitedRAG_HybridSearch")
    res = p04_rag_bot.query(req.query)
    p09_tracer.end_trace(span.span_id, cost_usd=0.0008)
    return res


# --- PROJECT 05: HITL APPROVAL WORKFLOW ---
class SubmitTaskRequest(BaseModel):
    action_type: str
    description: str
    estimated_cost_usd: float
    is_high_risk: bool = False
    payload: Dict[str, Any] = {}


class ResolveTaskRequest(BaseModel):
    task_id: str
    approve: bool
    reviewer_id: str = "SecOps_Lead"
    reviewer_note: Optional[str] = None


@app.post("/api/p05/submit")
async def submit_p05_task(req: SubmitTaskRequest):
    span = p09_tracer.start_trace("HITL_SubmitAction")
    task = p05_hitl_engine.submit_action(
        req.action_type, req.description, req.estimated_cost_usd, req.payload, req.is_high_risk
    )
    p09_tracer.end_trace(span.span_id, cost_usd=0.0001)
    return task


@app.get("/api/p05/queue")
async def get_p05_queue():
    return p05_hitl_engine.get_pending_queue()


@app.get("/api/p05/audit")
async def get_p05_audit():
    return p05_hitl_engine.get_audit_trail()


@app.post("/api/p05/resolve")
async def resolve_p05_task(req: ResolveTaskRequest):
    return p05_hitl_engine.resolve_task(req.task_id, req.approve, req.reviewer_id, req.reviewer_note)


# --- PROJECT 06: STREAMING COPILOT ---
@app.get("/api/p06/stream")
async def stream_p06_copilot(prompt: str = "Hello", simulate_latency: bool = False):
    return StreamingResponse(
        p06_copilot_engine.stream_tokens(prompt, simulate_latency),
        media_type="text/event-stream"
    )


# --- PROJECT 07: AUTOMATED EVAL HARNESS ---
@app.post("/api/p07/run")
async def run_p07_eval_suite(simulate_regression: bool = False):
    span = p09_tracer.start_trace("EvalHarness_Run50GoldenCases")
    summary, results = p07_eval_harness.run_eval_suite(simulate_regression=simulate_regression)
    p09_tracer.end_trace(span.span_id, cost_usd=summary.total_estimated_cost_usd)
    return {
        "summary": summary,
        "sample_test_results": [r.model_dump() for r in results[:8]]
    }


# --- PROJECT 08: LOCAL INFERENCE SERVER ---
@app.post("/api/p08/run")
async def run_p08_local_inference(quant_mode: str = "AWQ_INT4"):
    span = p09_tracer.start_trace("LocalInference_vLLM")
    res = p08_local_server.run_inference("Analyze system metrics", quant_mode=quant_mode)
    p09_tracer.end_trace(span.span_id, cost_usd=0.0000)
    return res


# --- PROJECT 09: TRACED PIPELINE METRICS ---
@app.get("/api/p09/metrics", response_class=PlainTextResponse)
async def get_p09_prometheus_metrics():
    return p09_tracer.get_prometheus_metrics()


# --- PROJECT 10: SECURITY GUARDRAILS ---
class GuardrailInspectRequest(BaseModel):
    input_text: str


@app.post("/api/p10/inspect")
async def inspect_p10_guardrails(req: GuardrailInspectRequest):
    span = p09_tracer.start_trace("SecurityGuardrail_InspectInput")
    input_check = p10_guardrails.inspect_and_sanitize_input(req.input_text)
    output_check = p10_guardrails.inspect_output(input_check.sanitized_text)
    p09_tracer.end_trace(span.span_id, cost_usd=0.0001)
    return {
        "input_check": input_check,
        "output_check": output_check
    }


# --- PROJECT 11: ARCHITECTURE DOCS ---
@app.get("/api/p11/docs")
async def get_p11_architecture_docs():
    return {
        "markdown_spec": ArchitectureDocsGenerator.get_system_architecture_markdown()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
