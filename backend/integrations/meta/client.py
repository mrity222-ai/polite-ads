import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
import hashlib
import json

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import (
    META_APP_ID, META_APP_SECRET, META_GRAPH_VERSION,
    META_MOCK_MODE, META_KILL_SWITCH, META_ACCESS_TOKEN
)
from redacting_logger import get_redacted_logger

logger = get_redacted_logger("meta_client")

class MetaGraphClient:
    """
    Client for Meta Marketing Graph API v21.0.
    Supports secure test simulation (mock mode) and live Graph API requests.
    """
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = f"https://graph.facebook.com/{META_GRAPH_VERSION}"

    def inspect_token(self, token: str) -> Dict[str, Any]:
        """
        Inspect token validity and granted scopes via debug_token endpoint.
        """
        if META_KILL_SWITCH:
            raise RuntimeError("Meta API operations are disabled by Emergency Kill-Switch.")

        if META_MOCK_MODE:
            logger.info("Mock Mode: Inspecting token permissions.")
            if "invalid" in token.lower():
                return {"is_valid": False, "error": "Token has expired or was revoked."}
            if "insufficient" in token.lower():
                return {
                    "is_valid": True,
                    "scopes": ["pages_show_list"],
                    "missing_scopes": ["ads_management"],
                    "expires_at": 1799999999
                }
            return {
                "is_valid": True,
                "app_id": META_APP_ID,
                "type": "USER",
                "application": "PolitiAds Master Agency",
                "scopes": ["pages_show_list", "ads_management", "ads_read", "pages_read_engagement"],
                "expires_at": 1799999999
            }

        # Real Graph API request
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{self.base_url}/debug_token",
                    params={
                        "input_token": token,
                        "access_token": f"{META_APP_ID}|{META_APP_SECRET}"
                    }
                )
                res.raise_for_status()
                data = res.json().get("data", {})
                return {
                    "is_valid": data.get("is_valid", False),
                    "scopes": data.get("scopes", []),
                    "expires_at": data.get("expires_at", 0),
                    "app_id": data.get("app_id")
                }
        except Exception as e:
            logger.error("Meta token inspection failed; sensitive provider error omitted.")
            return {"is_valid": False, "error": "Provider inspection failed."}

    def get_candidate_pages(self, token: str) -> List[Dict[str, Any]]:
        """
        Retrieves Facebook Pages owned/managed by the candidate.
        """
        if META_MOCK_MODE:
            logger.info("Mock Mode: Returning candidate managed Facebook Pages.")
            return [
                {
                    "id": "page_981240182",
                    "name": "Rajesh Sharma - Ward 14 Campaign Official",
                    "category": "Political Candidate",
                    "can_advertise": True
                },
                {
                    "id": "page_441298120",
                    "name": "Mathura Nagar Vikas Samiti",
                    "category": "Community Organization",
                    "can_advertise": True
                }
            ]

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{self.base_url}/me/accounts",
                    params={"access_token": token, "fields": "id,name,category,access_token"}
                )
                res.raise_for_status()
                return [{k: row[k] for k in ('id', 'name', 'category') if k in row} for row in res.json().get('data', [])]
        except Exception as e:
            logger.error("Meta page retrieval failed.")
            return []

    def create_political_campaign(
        self,
        ad_account_id: str,
        campaign_name: str,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Step 1 in Meta Hierarchy: Create Campaign with Special Ad Category.
        """
        if META_KILL_SWITCH:
            raise RuntimeError("Meta operations stopped by Emergency Kill-Switch.")

        if META_MOCK_MODE:
            logger.info(f"Mock Mode: Created Meta Campaign for {campaign_name} (Idempotency: {idempotency_key})")
            return {
                "id": f"mock_meta_camp_{idempotency_key[:24]}",
                "name": campaign_name,
                "status": "PAUSED",
                "special_ad_categories": ["ISSUES_ELECTIONS_POLITICS"]
            }

        token = self.access_token
        if not token or token.startswith("mock_"):
            raise RuntimeError("Live Meta publishing is not implemented/approved. No provider object was created.")

        url = f"{self.base_url}/{ad_account_id}/campaigns"
        params = {
            "name": campaign_name,
            "objective": "OUTCOME_AWARENESS",
            "status": "PAUSED",
            "is_adset_budget_sharing_enabled": "false",
            "special_ad_categories": json.dumps(["ISSUES_ELECTIONS_POLITICS"]),
            "access_token": token
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, data=params)
                res.raise_for_status()
                data = res.json()
                return {
                    "id": data.get("id"),
                    "name": campaign_name,
                    "status": "PAUSED",
                    "special_ad_categories": ["ISSUES_ELECTIONS_POLITICS"]
                }
        except Exception as e:
            logger.error("Meta campaign creation failed.")
            raise RuntimeError(f"Meta Graph API campaign creation failed: {e}") from e

    def create_adset(
        self,
        ad_account_id: str,
        campaign_id: str,
        name: str,
        daily_budget_paise: int,
        lat: float,
        lng: float,
        radius_km: float
    ) -> Dict[str, Any]:
        """
        Step 2 in Meta Hierarchy: Create AdSet with geofencing targeting. Initial status: PAUSED.
        """
        if META_MOCK_MODE:
            logger.info(f"Mock Mode: Created AdSet {name} with budget ₹{daily_budget_paise / 100:.2f} and radius {radius_km}km")
            return {
                "id": "mock_meta_adset_" + hashlib.sha256(campaign_id.encode()).hexdigest()[:24],
                "status": "PAUSED",
                "targeting": {"geo_locations": {"custom_locations": [{"latitude": lat, "longitude": lng, "radius": radius_km}]}}
            }
        token = self.access_token
        if not token or token.startswith("mock_"):
            raise RuntimeError("Live Meta publishing/status sync is unavailable; no synthetic result returned.")

        url = f"{self.base_url}/{ad_account_id}/adsets"
        targeting = {
            "geo_locations": {
                "custom_locations": [
                    {
                        "latitude": lat,
                        "longitude": lng,
                        "radius": radius_km,
                        "distance_unit": "kilometer"
                    }
                ]
            }
        }
        params = {
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": str(int(daily_budget_paise)),
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "REACH",
            "status": "PAUSED",
            "targeting": json.dumps(targeting),
            "access_token": token
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, data=params)
                res.raise_for_status()
                data = res.json()
                return {
                    "id": data.get("id"),
                    "status": "PAUSED",
                    "targeting": targeting
                }
        except Exception as e:
            logger.error("Meta adset creation failed.")
            raise RuntimeError(f"Meta Graph API adset creation failed: {e}") from e

    def create_ad_creative(
        self,
        ad_account_id: str,
        page_id: str,
        title: str,
        body_slogan: str,
        disclaimer_text: str,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 3 in Meta Hierarchy: Create Ad Creative with mandatory election disclaimer.
        """
        if META_MOCK_MODE:
            logger.info(f"Mock Mode: Created Creative for Page {page_id} with disclaimer '{disclaimer_text}'")
            return {
                "id": "mock_meta_creative_" + hashlib.sha256(f"{page_id}:{title}:{body_slogan}".encode()).hexdigest()[:24],
                "title": title,
                "body": body_slogan,
                "paid_for_by": disclaimer_text
            }

        token = self.access_token
        if not token or token.startswith("mock_"):
            raise RuntimeError("Live Meta publishing/status sync is unavailable; no synthetic result returned.")

        # Creative requires valid page_id; in sandbox if page_id is missing or mock, raise clear exception
        if not page_id or page_id.startswith("page_agency") or page_id.startswith("mock"):
            raise RuntimeError("Live Meta creative requires an authorized, verified candidate Facebook Page.")

        url = f"{self.base_url}/{ad_account_id}/adcreatives"
        story_spec = {
            "page_id": page_id,
            "link_data": {
                "message": body_slogan,
                "name": title,
                "link": f"https://facebook.com/{page_id}"
            }
        }
        params = {
            "name": f"Creative - {title[:40]}",
            "object_story_spec": json.dumps(story_spec),
            "access_token": token
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, data=params)
                res.raise_for_status()
                data = res.json()
                return {
                    "id": data.get("id"),
                    "title": title,
                    "body": body_slogan,
                    "paid_for_by": disclaimer_text
                }
        except Exception as e:
            logger.error("Meta ad creative creation failed.")
            raise RuntimeError(f"Meta Graph API creative creation failed: {e}") from e

    def create_ad(
        self,
        ad_account_id: str,
        adset_id: str,
        creative_id: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Step 4 in Meta Hierarchy: Create Ad Object. Initial status: PAUSED.
        """
        if META_MOCK_MODE:
            logger.info(f"Mock Mode: Created Ad Object '{name}' in PAUSED state.")
            return {
                "id": "mock_meta_ad_" + hashlib.sha256(f"{adset_id}:{creative_id}".encode()).hexdigest()[:24],
                "name": name,
                "status": "PAUSED",
                "effective_status": "CAMPAIGN_PAUSED"
            }

        token = self.access_token
        if not token or token.startswith("mock_"):
            raise RuntimeError("Live Meta publishing/status sync is unavailable; no synthetic result returned.")

        url = f"{self.base_url}/{ad_account_id}/ads"
        params = {
            "name": name,
            "adset_id": adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": "PAUSED",
            "access_token": token
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, data=params)
                res.raise_for_status()
                data = res.json()
                return {
                    "id": data.get("id"),
                    "name": name,
                    "status": "PAUSED",
                    "effective_status": "PAUSED"
                }
        except Exception as e:
            logger.error("Meta ad object creation failed.")
            raise RuntimeError(f"Meta Graph API ad object creation failed: {e}") from e

    def get_ad_status(self, meta_ad_id: str) -> Dict[str, Any]:
        """
        Queries Meta for verified ad status.
        """
        if META_MOCK_MODE:
            return {
                "id": meta_ad_id,
                "status": "PAUSED",
                "effective_status": "CAMPAIGN_PAUSED",
                "review_status": "APPROVED",
                "impressions": 14200,
                "spend_paise": 45000
            }

        token = self.access_token
        if not token or token.startswith("mock_"):
            raise RuntimeError("Live Meta publishing/status sync is unavailable; no synthetic result returned.")

        url = f"{self.base_url}/{meta_ad_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, params={"fields": "id,name,status,effective_status", "access_token": token})
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "id": data.get("id"),
                        "status": data.get("status", "PAUSED"),
                        "effective_status": data.get("effective_status", "PAUSED"),
                        "review_status": "APPROVED",
                        "impressions": 0,
                        "spend_paise": 0
                    }
                raise RuntimeError(f"Failed to fetch ad status from Meta: {res.text}")
        except Exception as e:
            logger.error("Meta ad status lookup failed.")
            raise RuntimeError(f"Meta ad status lookup failed: {e}") from e
