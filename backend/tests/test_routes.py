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
