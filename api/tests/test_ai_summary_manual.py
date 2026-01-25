
import asyncio
import os
import sys

# Ensure we can import from api
sys.path.append(os.path.abspath("/Users/hao/dev/github/machine_learning/hao_projects/invoice_app/api"))

from commercial.ai.router import summarize_client_notes
from core.models.models_per_tenant import ClientNote, Client, User, AIConfig
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

async def test_summarize_client_notes():
    print("Testing summarize_client_notes...")

    # Mock DB Session
    mock_db = MagicMock()
    
    # Mock Current User
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"

    # Mock Notes
    mock_notes = [
        ClientNote(id=1, client_id=1, note="Client is interested in the premium plan.", created_at=datetime.now(timezone.utc)),
        ClientNote(id=2, client_id=1, note="Follow up next week regarding the proposal.", created_at=datetime.now(timezone.utc))
    ]
    
    # Mock DB Query for Notes
    # The chain is db.query(ClientNote).filter(...).all()
    # We mock the return of filter(...) to have an .all() method that returns our list
    mock_query_notes = MagicMock()
    mock_query_notes.all.return_value = mock_notes
    
    # We need to handle multiple queries. 
    # First query is for ClientNote, second is for AIConfig, third (fallback) is for active AIConfig
    def query_side_effect(model):
        if model == ClientNote:
            mock_filter = MagicMock()
            mock_filter.filter.return_value = mock_query_notes
            return mock_filter
        if model == AIConfig:
            mock_filter_config = MagicMock()
            # Mocking no default config in DB, forcing env var fallback or fallback to active
            mock_filter_config.filter.return_value.first.return_value = None 
            mock_filter_config.filter.return_value.all.return_value = []
            return mock_filter_config
        return MagicMock()

    mock_db.query.side_effect = query_side_effect

    # Mock AI Config Service (Environment Variable Fallback)
    with patch("commercial.ai.services.ai_config_service.AIConfigService.get_ai_config") as mock_get_env:
        # Simulate environment config
        mock_get_env.return_value = {
            "provider_name": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "sk-test",
            "provider_url": None
        }

        # Mock HTTPX Client to avoid real API Calls
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {"message": {"content": "Summary: Client interested in premium, follow up next week."}}
                ]
            }
            mock_post.return_value = mock_response

            # Run the function
            result = await summarize_client_notes(client_id=1, db=mock_db, current_user=mock_user)
            
            print("Result:", result)
            
            if result["success"] and "Summary: Client interested" in result["data"]["summary"]:
                print("SUCCESS: Summary generated correctly.")
            else:
                print("FAILURE: Unexpected result.")

if __name__ == "__main__":
    asyncio.run(test_summarize_client_notes())
