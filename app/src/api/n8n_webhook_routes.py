from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import httpx
import asyncio
from typing import Optional
import os

router = APIRouter(prefix="/n8n-webhook", tags=["n8n-webhook"])

# Pydantic models for request/response
class AmazonProductRequest(BaseModel):
    product_url: HttpUrl
    user_id: Optional[str] = None
    callback_url: Optional[HttpUrl] = None

class WorkflowResponse(BaseModel):
    status: str
    message: str
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None



@router.get("/test-webhook-connection")
async def test_webhook_connection():
    """
    Test endpoint to confirm the webhook is active and reachable.
    """
    return JSONResponse(content={"status": "success", "message": "Webhook is active"})


# Store your n8n webhook URL - you'll get this from n8n after setting up webhook
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/amazon-product")

@router.post("/amazon-product", response_model=WorkflowResponse)
async def trigger_amazon_workflow(request: AmazonProductRequest):
    """
    Trigger the n8n workflow for Amazon product processing
    """
    try:
        # Prepare payload for n8n webhook
        webhook_payload = {
            "product_url": str(request.product_url),
            "user_id": request.user_id,
            "callback_url": str(request.callback_url) if request.callback_url else None,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send request to n8n webhook
        async with httpx.AsyncClient(timeout=500.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                if response.text:
                    try:
                        result = response.json()
                        return WorkflowResponse(
                            status="success",
                            message="Workflow triggered successfully",
                            workflow_id=result.get("workflowId"),
                            execution_id=result.get("executionId")
                        )
                    except ValueError:
                        # Handle cases where response is not valid JSON
                        return WorkflowResponse(
                            status="success",
                            message="Workflow triggered successfully, but response was not valid JSON."
                        )
                else:
                    # Handle empty response body
                    return WorkflowResponse(
                        status="success",
                        message="Workflow triggered successfully with an empty response."
                    )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"N8N webhook failed: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=408,
            detail="Request timeout while triggering workflow"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting to n8n: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/workflow-status/{execution_id}")
async def get_workflow_status(execution_id: str):
    """
    Check the status of a workflow execution
    """
    try:
        # You'll need to implement this based on your n8n API
        # This is a placeholder for checking execution status
        n8n_api_url = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{n8n_api_url}/executions/{execution_id}",
                headers={"Authorization": f"Bearer {os.getenv('N8N_API_KEY')}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get workflow status"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking workflow status: {str(e)}"
        )

@router.post("/webhook/amazon-result")
async def receive_workflow_result(result_data: dict):
    """
    Endpoint to receive results from n8n workflow
    This endpoint will be called by n8n when the workflow completes
    """
    try:
        # Process the result from n8n
        # You can store it in database, send notifications, etc.
        
        print(f"Received workflow result: {result_data}")
        
        # If there's a callback URL, send the result there
        if result_data.get("callback_url"):
            async with httpx.AsyncClient() as client:
                await client.post(
                    result_data["callback_url"],
                    json=result_data
                )
        
        return {"status": "success", "message": "Result received"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing workflow result: {str(e)}"
        )
