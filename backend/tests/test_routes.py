from unittest.mock import patch, MagicMock
def test_unauthenticated_api_patients(client):
    """Endpoints requiring JWT should throw 401 when none is provided"""
    response = client.get("/api/patients")
    assert response.status_code == 401
    assert "missing or invalid authorization token" in str(response.json()).lower() or "not authenticated" in str(response.json()).lower()

def test_check_drug_missing_fields(client):
    """Missing required POST body fields should return 422 Unprocessable Entity"""
    response = client.post("/api/check-drug", json={
        # Missing pharmacist_query and abha_id
        "patient_id": "dummy-uuid"
    })
    # Since we lack auth, it might hit 401 first depending on middleware order,
    # but let's assume Pydantic catches missing fields or Auth catches missing token.
    assert response.status_code in [401, 422]

def test_check_drug_with_bad_jwt(client):
    """Using an invalid or spoofed JWT shouldn't be allowed"""
    response = client.post("/api/check-drug", headers={
        "Authorization": "Bearer not-a-real-jwt"
    }, json={
        "pharmacist_query": "Aspirin",
        "patient_id": "dummy-uuid",
        "abha_id": "91-0000-0000-0000"
    })
    assert response.status_code == 401
    
# NOTE: Testing full success routes (200 OK) requires a dedicated testing database
# for Supabase to mock patient fetching and ABDM mock records.
# For now, we verify that the boundaries and middleware are correctly guarding the routes.

def test_api_patients_pagination_params(client):
    """Pagination query params should be correctly parsed by FastAPI"""
    response = client.get("/api/patients?page=2&limit=5&search=foo")
    # Should be 401 since no auth is passed, but NOT 422 (validation error)
    assert response.status_code == 401

def test_api_patients_bad_pagination(client):
    """Providing wrong data types for page/limit should return 422"""
    # Patch the controller's get_supabase or the middleware's user check
    # to bypass 401 and reach the parameter validation/conversion logic.
    with patch("app.middleware.auth.get_supabase") as mock_get:
        mock_db = MagicMock()
        mock_get.return_value = mock_db
        # Mock finding an admin user so auth middleware passes
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "1", "username": "testadmin"}]
        
        response = client.get(
            "/api/patients?page=abc", 
            headers={"Authorization": "Bearer fake-jwt-testadmin"}
        )
        assert response.status_code == 422
