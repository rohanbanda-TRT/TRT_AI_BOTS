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
        async with httpx.AsyncClient(timeout=None) as client:
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


# # from fastapi import APIRouter, HTTPException, BackgroundTasks
# # from fastapi.responses import JSONResponse
# # from pydantic import BaseModel, HttpUrl
# # import httpx
# # import asyncio
# # from typing import Optional
# # import os
# # import logging

# # # Set up logging
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # router = APIRouter()

# # # Pydantic models for request/response
# # class AmazonProductRequest(BaseModel):
# #     product_url: HttpUrl
# #     user_id: Optional[str] = None
# #     callback_url: Optional[HttpUrl] = None

# # class WorkflowResponse(BaseModel):
# #     status: str
# #     message: str
# #     workflow_id: Optional[str] = None
# #     execution_id: Optional[str] = None

# # # Store your n8n webhook URL - you'll get this from n8n after setting up webhook
# # N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/amazon-product")

# # @router.post("/trigger-amazon-workflow", response_model=WorkflowResponse)
# # async def trigger_amazon_workflow(request: AmazonProductRequest):
# #     """
# #     Trigger the n8n workflow for Amazon product processing
# #     """
# #     try:
# #         # Prepare payload for n8n webhook
# #         webhook_payload = {
# #             "product_url": str(request.product_url),
# #             "user_id": request.user_id,
# #             "callback_url": str(request.callback_url) if request.callback_url else None,
# #             "timestamp": asyncio.get_event_loop().time()
# #         }
        
# #         logger.info(f"Sending webhook to: {N8N_WEBHOOK_URL}")
# #         logger.info(f"Payload: {webhook_payload}")
        
# #         # Send request to n8n webhook
# #         async with httpx.AsyncClient(timeout=30.0) as client:
# #             response = await client.post(
# #                 N8N_WEBHOOK_URL,
# #                 json=webhook_payload,
# #                 headers={"Content-Type": "application/json"}
# #             )
            
# #             logger.info(f"Response status: {response.status_code}")
# #             logger.info(f"Response headers: {response.headers}")
# #             logger.info(f"Response text: {response.text}")
            
# #             if response.status_code == 200:
# #                 # Handle different response types
# #                 try:
# #                     # Try to parse as JSON
# #                     if response.headers.get("content-type", "").startswith("application/json"):
# #                         result = response.json()
# #                     else:
# #                         # Handle non-JSON response
# #                         result = {"message": response.text or "Workflow completed"}
# #                 except Exception as json_error:
# #                     # If JSON parsing fails, treat as text response
# #                     logger.warning(f"JSON parsing failed: {json_error}")
# #                     result = {"message": response.text or "Workflow completed"}
                
# #                 return WorkflowResponse(
# #                     status="success",
# #                     message="Workflow triggered successfully",
# #                     workflow_id=result.get("workflowId"),
# #                     execution_id=result.get("executionId")
# #                 )
# #             else:
# #                 raise HTTPException(
# #                     status_code=response.status_code,
# #                     detail=f"N8N webhook failed: {response.text}"
# #                 )
                
# #     except httpx.TimeoutException:
# #         logger.error("Timeout while calling n8n webhook")
# #         raise HTTPException(
# #             status_code=408,
# #             detail="Request timeout while triggering workflow"
# #         )
# #     except httpx.RequestError as e:
# #         logger.error(f"Request error: {e}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Error connecting to n8n: {str(e)}"
# #         )
# #     except Exception as e:
# #         logger.error(f"Unexpected error: {e}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Unexpected error: {str(e)}"
# #         )

# # @router.get("/workflow-status/{execution_id}")
# # async def get_workflow_status(execution_id: str):
# #     """
# #     Check the status of a workflow execution
# #     """
# #     try:
# #         # You'll need to implement this based on your n8n API
# #         # This is a placeholder for checking execution status
# #         n8n_api_url = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
        
# #         async with httpx.AsyncClient() as client:
# #             response = await client.get(
# #                 f"{n8n_api_url}/executions/{execution_id}",
# #                 headers={"Authorization": f"Bearer {os.getenv('N8N_API_KEY')}"}
# #             )
            
# #             if response.status_code == 200:
# #                 return response.json()
# #             else:
# #                 raise HTTPException(
# #                     status_code=response.status_code,
# #                     detail="Failed to get workflow status"
# #                 )
                
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Error checking workflow status: {str(e)}"
# #         )

# # @router.get("/test-webhook")
# # async def test_webhook():
# #     """
# #     Test endpoint to verify webhook connectivity
# #     """
# #     try:
# #         test_payload = {
# #             "product_url": "https://amazon.com/test",
# #             "user_id": "test_user",
# #             "test": True
# #         }
        
# #         logger.info(f"Testing webhook: {N8N_WEBHOOK_URL}")
        
# #         async with httpx.AsyncClient(timeout=10.0) as client:
# #             response = await client.post(
# #                 N8N_WEBHOOK_URL,
# #                 json=test_payload,
# #                 headers={"Content-Type": "application/json"}
# #             )
            
# #             return {
# #                 "webhook_url": N8N_WEBHOOK_URL,
# #                 "status_code": response.status_code,
# #                 "response_headers": dict(response.headers),
# #                 "response_text": response.text,
# #                 "content_type": response.headers.get("content-type", "")
# #             }
            
# #     except Exception as e:
# #         return {
# #             "webhook_url": N8N_WEBHOOK_URL,
# #             "error": str(e)
# #         }

# # @router.post("/test-webhook")
# # async def test_webhook_post():
# #     """
# #     Test POST endpoint to verify webhook connectivity
# #     """
# #     return await test_webhook()

# # @router.post("/webhook/amazon-result")
# # async def receive_workflow_result(result_data: dict):
# #     """
# #     Endpoint to receive results from n8n workflow
# #     This endpoint will be called by n8n when the workflow completes
# #     """
# #     try:
# #         # Process the result from n8n
# #         # You can store it in database, send notifications, etc.
        
# #         print(f"Received workflow result: {result_data}")
        
# #         # If there's a callback URL, send the result there
# #         if result_data.get("callback_url"):
# #             async with httpx.AsyncClient() as client:
# #                 await client.post(
# #                     result_data["callback_url"],
# #                     json=result_data
# #                 )
        
# #         return {"status": "success", "message": "Result received"}
        
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Error processing workflow result: {str(e)}"
# #         )



# from fastapi import APIRouter, HTTPException, BackgroundTasks
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel, HttpUrl
# import httpx
# import asyncio
# from typing import Optional
# import os
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter()

# # Pydantic models for request/response
# class AmazonProductRequest(BaseModel):
#     product_url: HttpUrl
#     user_id: Optional[str] = None
#     callback_url: Optional[HttpUrl] = None

# class WorkflowResponse(BaseModel):
#     status: str
#     message: str
#     workflow_id: Optional[str] = None
#     execution_id: Optional[str] = None

# # Store your n8n webhook URL - you'll get this from n8n after setting up webhook
# N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/amazon-product")

# @router.post("/trigger-amazon-workflow", response_model=WorkflowResponse)
# async def trigger_amazon_workflow(request: AmazonProductRequest):
#     """
#     Trigger the n8n workflow for Amazon product processing
#     """
#     try:
#         # Prepare payload for n8n webhook
#         webhook_payload = {
#             "product_url": str(request.product_url),
#             "user_id": request.user_id,
#             "callback_url": str(request.callback_url) if request.callback_url else None,
#             "timestamp": asyncio.get_event_loop().time()
#         }
        
#         logger.info(f"Sending webhook to: {N8N_WEBHOOK_URL}")
#         logger.info(f"Payload: {webhook_payload}")
        
#         # Send request to n8n webhook
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.post(
#                 N8N_WEBHOOK_URL,
#                 json=webhook_payload,
#                 headers={"Content-Type": "application/json"}
#             )
            
#             logger.info(f"Response status: {response.status_code}")
#             logger.info(f"Response headers: {response.headers}")
#             logger.info(f"Response text: {response.text}")
            
#             if response.status_code == 200:
#                 # Handle different response types
#                 result = {}
#                 try:
#                     # Try to parse as JSON
#                     if response.text.strip():  # Check if response has content
#                         if response.headers.get("content-type", "").startswith("application/json"):
#                             result = response.json()
#                         else:
#                             result = {"message": response.text}
#                     else:
#                         # Empty response is considered success for n8n workflows
#                         result = {"message": "Workflow completed successfully"}
#                 except Exception as json_error:
#                     # If JSON parsing fails, treat as text response
#                     logger.warning(f"JSON parsing failed: {json_error}")
#                     result = {"message": response.text or "Workflow completed successfully"}
                
#                 return WorkflowResponse(
#                     status="success",
#                     message="Workflow triggered and completed successfully",
#                     workflow_id=result.get("workflowId"),
#                     execution_id=result.get("executionId")
#                 )
#             else:
#                 raise HTTPException(
#                     status_code=response.status_code,
#                     detail=f"N8N webhook failed: {response.text}"
#                 )
                
#     except httpx.TimeoutException:
#         logger.error("Timeout while calling n8n webhook")
#         raise HTTPException(
#             status_code=408,
#             detail="Request timeout while triggering workflow"
#         )
#     except httpx.RequestError as e:
#         logger.error(f"Request error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error connecting to n8n: {str(e)}"
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Unexpected error: {str(e)}"
#         )

# @router.get("/workflow-status/{execution_id}")
# async def get_workflow_status(execution_id: str):
#     """
#     Check the status of a workflow execution
#     """
#     try:
#         # You'll need to implement this based on your n8n API
#         # This is a placeholder for checking execution status
#         n8n_api_url = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{n8n_api_url}/executions/{execution_id}",
#                 headers={"Authorization": f"Bearer {os.getenv('N8N_API_KEY')}"}
#             )
            
#             if response.status_code == 200:
#                 return response.json()
#             else:
#                 raise HTTPException(
#                     status_code=response.status_code,
#                     detail="Failed to get workflow status"
#                 )
                
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error checking workflow status: {str(e)}"
#         )

# @router.get("/test-webhook")
# async def test_webhook():
#     """
#     Test endpoint to verify webhook connectivity
#     """
#     try:
#         test_payload = {
#             "product_url": "https://amazon.com/test",
#             "user_id": "test_user",
#             "test": True
#         }
        
#         logger.info(f"Testing webhook: {N8N_WEBHOOK_URL}")
        
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             response = await client.post(
#                 N8N_WEBHOOK_URL,
#                 json=test_payload,
#                 headers={"Content-Type": "application/json"}
#             )
            
#             return {
#                 "webhook_url": N8N_WEBHOOK_URL,
#                 "status_code": response.status_code,
#                 "response_headers": dict(response.headers),
#                 "response_text": response.text,
#                 "content_type": response.headers.get("content-type", "")
#             }
            
#     except Exception as e:
#         return {
#             "webhook_url": N8N_WEBHOOK_URL,
#             "error": str(e)
#         }

# @router.post("/test-webhook")
# async def test_webhook_post():
#     """
#     Test POST endpoint to verify webhook connectivity
#     """
#     return await test_webhook()

# @router.post("/webhook/amazon-result")
# async def receive_workflow_result(result_data: dict):
#     """
#     Endpoint to receive results from n8n workflow
#     This endpoint will be called by n8n when the workflow completes
#     """
#     try:
#         # Process the result from n8n
#         # You can store it in database, send notifications, etc.
        
#         print(f"Received workflow result: {result_data}")
        
#         # If there's a callback URL, send the result there
#         if result_data.get("callback_url"):
#             async with httpx.AsyncClient() as client:
#                 await client.post(
#                     result_data["callback_url"],
#                     json=result_data
#                 )
        
#         return {"status": "success", "message": "Result received"}
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing workflow result: {str(e)}"
#         )



# from fastapi import APIRouter, HTTPException, BackgroundTasks
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel, HttpUrl
# import httpx
# import asyncio
# from typing import Optional, Dict, Any
# import os
# import logging
# import json

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter()

# # Pydantic models for request/response
# class AmazonProductRequest(BaseModel):
#     product_url: HttpUrl
#     user_id: Optional[str] = None
#     callback_url: Optional[HttpUrl] = None

# class WorkflowResponse(BaseModel):
#     status: str
#     message: str
#     workflow_id: Optional[str] = None
#     execution_id: Optional[str] = None
#     n8n_response: Optional[Dict[str, Any]] = None

# # Store your n8n webhook URL
# N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://automations.demotrt.com/webhook/amazon-product")

# @router.post("/amazon-product", response_model=WorkflowResponse)
# async def trigger_amazon_workflow(request: AmazonProductRequest):
#     """
#     Trigger the n8n workflow for Amazon product processing
#     """
#     try:
#         # Prepare payload for n8n webhook
#         webhook_payload = {
#             "product_url": str(request.product_url),
#             "user_id": request.user_id or "anonymous",
#             "callback_url": str(request.callback_url) if request.callback_url else None,
#             "timestamp": asyncio.get_event_loop().time(),
#             "source": "fastapi"
#         }
        
#         logger.info(f"Sending webhook to: {N8N_WEBHOOK_URL}")
#         logger.info(f"Payload: {webhook_payload}")
        
#         # Send request to n8n webhook
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.post(
#                 N8N_WEBHOOK_URL,
#                 json=webhook_payload,
#                 headers={
#                     "Content-Type": "application/json",
#                     "User-Agent": "FastAPI-N8N-Client/1.0"
#                 }
#             )
            
#             logger.info(f"Response status: {response.status_code}")
#             logger.info(f"Response headers: {response.headers}")
#             logger.info(f"Response text: '{response.text}'")
            
#             if response.status_code == 200:
#                 # Handle successful response
#                 result = {}
#                 try:
#                     if response.text and response.text.strip():
#                         result = response.json()
#                         logger.info(f"Parsed JSON response: {result}")
#                     else:
#                         result = {"message": "Webhook triggered successfully"}
#                 except Exception as json_error:
#                     logger.warning(f"JSON parsing failed: {json_error}")
#                     result = {"message": response.text or "Webhook triggered successfully"}
                
#                 return WorkflowResponse(
#                     status="success",
#                     message="Workflow triggered successfully",
#                     workflow_id=result.get("workflowId") or result.get("workflow_id"),
#                     execution_id=result.get("executionId") or result.get("execution_id"),
#                     n8n_response=result
#                 )
            
#             elif response.status_code == 500:
#                 # Handle n8n internal errors
#                 try:
#                     error_data = response.json()
#                     error_message = error_data.get("message", "Unknown n8n error")
#                     logger.error(f"N8N workflow error: {error_message}")
                    
#                     # Provide more specific error handling
#                     if "Workflow could not be started" in error_message:
#                         raise HTTPException(
#                             status_code=500,
#                             detail={
#                                 "error": "N8N workflow configuration error",
#                                 "message": "The workflow could not be started. Please check:",
#                                 "suggestions": [
#                                     "Ensure the webhook node is properly configured",
#                                     "Verify the workflow is saved and active",
#                                     "Check that all required nodes are connected",
#                                     "Ensure no syntax errors in expressions"
#                                 ],
#                                 "n8n_error": error_message
#                             }
#                         )
#                     else:
#                         raise HTTPException(
#                             status_code=500,
#                             detail={
#                                 "error": "N8N workflow error",
#                                 "message": error_message,
#                                 "n8n_response": error_data
#                             }
#                         )
#                 except json.JSONDecodeError:
#                     raise HTTPException(
#                         status_code=500,
#                         detail=f"N8N webhook failed with status {response.status_code}: {response.text}"
#                     )
            
#             else:
#                 # Handle other HTTP errors
#                 raise HTTPException(
#                     status_code=response.status_code,
#                     detail=f"N8N webhook failed with status {response.status_code}: {response.text}"
#                 )
                
#     except httpx.TimeoutException:
#         logger.error("Timeout while calling n8n webhook")
#         raise HTTPException(
#             status_code=408,
#             detail="Request timeout while triggering workflow"
#         )
#     except httpx.RequestError as e:
#         logger.error(f"Request error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error connecting to n8n: {str(e)}"
#         )
#     except HTTPException:
#         # Re-raise HTTPExceptions as-is
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Unexpected error: {str(e)}"
#         )

# @router.get("/test-webhook-connection")
# async def test_webhook_connection():
#     """
#     Test the webhook connection and n8n availability
#     """
#     try:
#         # First, test if n8n is reachable
#         test_payload = {
#             "test": True,
#             "product_url": "https://amazon.com/test",
#             "user_id": "test_user",
#             "timestamp": asyncio.get_event_loop().time()
#         }
        
#         logger.info(f"Testing webhook connection to: {N8N_WEBHOOK_URL}")
        
#         async with httpx.AsyncClient(timeout=15.0) as client:
#             response = await client.post(
#                 N8N_WEBHOOK_URL,
#                 json=test_payload,
#                 headers={"Content-Type": "application/json"}
#             )
            
#             result = {
#                 "webhook_url": N8N_WEBHOOK_URL,
#                 "connection_status": "success" if response.status_code == 200 else "failed",
#                 "status_code": response.status_code,
#                 "response_headers": dict(response.headers),
#                 "response_text": response.text,
#                 "response_length": len(response.text) if response.text else 0
#             }
            
#             if response.status_code == 500:
#                 try:
#                     error_data = response.json()
#                     result["error_details"] = error_data
#                 except:
#                     result["error_details"] = {"raw_error": response.text}
            
#             return result
            
#     except Exception as e:
#         logger.error(f"Connection test failed: {e}")
#         return {
#             "webhook_url": N8N_WEBHOOK_URL,
#             "connection_status": "failed",
#             "error": str(e),
#             "error_type": type(e).__name__
#         }

# @router.post("/webhook/amazon-result")
# async def receive_workflow_result(result_data: dict):
#     """
#     Endpoint to receive results from n8n workflow
#     """
#     try:
#         logger.info(f"Received workflow result: {result_data}")
        
#         # Process the result from n8n
#         if result_data.get("callback_url"):
#             async with httpx.AsyncClient() as client:
#                 await client.post(
#                     result_data["callback_url"],
#                     json=result_data
#                 )
        
#         return {"status": "success", "message": "Result received and processed"}
        
#     except Exception as e:
#         logger.error(f"Error processing workflow result: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing workflow result: {str(e)}"
#         )