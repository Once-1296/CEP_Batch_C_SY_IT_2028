import pytest
import anyio
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
from app.controllers.schema import DrugCheckRequest
from app.controllers.safety_controller import check_drug_safety

class MockSupabase:
    def __init__(self, patient_data=None, abdm_data=None, family_data=None):
        self.patient_data = patient_data or []
        self.abdm_data = abdm_data or []
        self.family_data = family_data or []
        
    def table(self, table_name):
        mock_chain = MagicMock()
        
        if table_name == "patients":
            mock_chain.select.return_value.eq.return_value.execute.return_value.data = self.patient_data
        elif table_name == "abdm_mock_records":
            mock_chain.select.return_value.eq.return_value.execute.return_value.data = self.abdm_data
        elif table_name == "family_relationships":
            mock_chain.select.return_value.eq.return_value.execute.return_value.data = self.family_data
            
        return mock_chain

def test_genomic_marker_alert():
    async def run_test():
        # Setup mock data for basic_health_details with genotype_markers
        patient_data = [{"id": "user-uuid", "name": "Test User", "abha_id": "1234"}]
        abdm_data = [{
            "abha_id": "1234",
            "basic_health_details": {
                "genotype_markers": {
                    "HLA-B*1502": "Positive"
                }
            }
        }]
        
        req = DrugCheckRequest(pharmacist_query="carbamazepine", patient_id="user-uuid", abha_id="1234")
        mock_db = MockSupabase(patient_data=patient_data, abdm_data=abdm_data)
        
        with patch("app.controllers.safety_controller.get_supabase", return_value=mock_db), \
             patch("app.controllers.safety_controller.BRAND_MAP", {"carbamazepine": ["carbamazepine"]}), \
             patch("app.controllers.safety_controller.CLINICAL_MAP", {
                 "carbamazepine": {
                     "HLA-B*1502": {
                         "Positive": "High risk of Stevens-Johnson syndrome."
                     }
                 }
             }):
            
            result = await check_drug_safety(req)
            
            assert result["severity_tier"] == "Red"
            assert result["risk_probability"] >= 0.95
            assert "Genomic Alert" in result["message"]
            assert "HLA-B*1502" in result["message"]
            assert isinstance(result["resolved_salts"], list)
            assert result["resolved_salts"] == ["carbamazepine"]
            assert "ml_details" not in result

    anyio.run(run_test)

def test_safe_drug_no_conflicts():
    async def run_test():
        patient_data = [{"id": "user-uuid", "name": "Test User", "abha_id": "1234"}]
        abdm_data = [{"abha_id": "1234"}]
        
        req = DrugCheckRequest(pharmacist_query="vitamin c", patient_id="user-uuid", abha_id="1234")
        mock_db = MockSupabase(patient_data=patient_data, abdm_data=abdm_data)
        
        with patch("app.controllers.safety_controller.get_supabase", return_value=mock_db), \
             patch("app.controllers.safety_controller.BRAND_MAP", {"vitamin c": ["ascorbic acid"]}):
            
            result = await check_drug_safety(req)
            
            assert result["severity_tier"] == "Green"
            assert "No adverse drug interactions" in result["message"]
            assert isinstance(result["resolved_salts"], list)
            assert result["resolved_salts"] == ["ascorbic acid"]

    anyio.run(run_test)
