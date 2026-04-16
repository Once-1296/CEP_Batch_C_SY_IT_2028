from app.nlp.cdss import predict_risk, get_cdss_model

def test_model_loaded():
    model = get_cdss_model()
    assert model is not None, "CDSS Model should be loaded"

def test_predict_risk():
    # Test valid combination logic
    result = predict_risk("Paracetamol", ["Common Cold", "Vitamin D3", "Seasonal Allergies"])
    
    assert result["status"] in ["SAFE", "DANGER"]
    assert "risk_probability" in result

def test_predict_risk_ddi_danger():
    # Warfarin vs Aspirin is a known severe DDI
    result = predict_risk("Aspirin", ["Warfarin", "Hypertension"])
    
    assert result["status"] == "DANGER"
    assert result["risk_probability"] >= 0.75
    assert result["conflicting_item"] == "Warfarin"
    assert len(result["details"]) == 2

def test_predict_risk_empty_patient():
    result = predict_risk("Aspirin", [])
    assert result["status"] == "SAFE"
    assert result["risk_probability"] == 0.0
