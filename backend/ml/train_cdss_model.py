import pandas as pd
import numpy as np
import random
import os
import json
import uuid
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import generate_data_67

def generate_negative_samples(positive_pairs, list1, list2, num_samples):
    """
    Discrete function to generate negative samples by randomly pairing items
    that do not exist in the positive_pairs list.
    """
    negative_pairs = set()
    positive_set = set(positive_pairs)
    
    attempts = 0
    max_attempts = num_samples * 2
    
    while len(negative_pairs) < num_samples and attempts < max_attempts:
        attempts += 1
        item1 = random.choice(list1)
        item2 = random.choice(list2)
        
        pair = (item1, item2)
        reverse_pair = (item2, item1)
        
        if pair not in positive_set and reverse_pair not in positive_set:
            negative_pairs.add(pair)
            
    return list(negative_pairs)

def build_and_train_cdss_model():
    print("Checking if datasets exist...")
    if not os.path.exists("abdm_records.json") or not os.path.exists("patients_data.json"):
        print("Negative interactions or base records do not fully exist. Rerunning generate_data_67 module...")
        MOCK_PHARMACIST_ID = str(uuid.uuid4())
        DEFAULT_PASS = "hashed_password_placeholder"
        patients_data, abdm_data, family_data = generate_data_67.generate_1000_dataset(MOCK_PHARMACIST_ID, DEFAULT_PASS)
        
        with open('patients_data.json', 'w') as f:
            json.dump(patients_data, f)
        with open('abdm_records.json', 'w') as f:
            json.dump(abdm_data, f)
        with open('family_rels.json', 'w') as f:
            json.dump(family_data, f)
        
    print("Loading interaction data for training...")
    
    # 1. Load DDI Data
    print("Reading drug interactions for positive pairs...")
    ddi_data = generate_data_67.fetch_tdc_ddi_data(sample_size=2000) 
    
    positive_ddi_pairs = []
    all_drugs = set()
    for row in ddi_data:
        d1 = row.get('Drug1', '')
        d2 = row.get('Drug2', '')
        positive_ddi_pairs.append((d1, d2))
        all_drugs.add(d1)
        all_drugs.add(d2)
        
    all_drugs_list = list(all_drugs)
    
    print("Generating negative DDI samples via discrete function...")
    negative_ddi_pairs = generate_negative_samples(positive_ddi_pairs, all_drugs_list, all_drugs_list, len(positive_ddi_pairs))
    
    # 2. Genetic Risk Data
    print("Reading genetic data from PharmGKB for positive pairs...")
    genetic_data = generate_data_67.fetch_pharmgkb_genetic_data(sample_size=1000)
    
    positive_genetic_pairs = []
    all_genes_phenotypes = set()
    for row in genetic_data:
        drug = row.get('Drug(s)', '')
        gene = row.get('Gene', 'Unknown')
        phenotype = row.get('Phenotype(s)', 'Unknown')
        condition = f"Genetic Variant: {gene} | Phenotype: {phenotype}"
        positive_genetic_pairs.append((drug, condition))
        all_drugs_list.append(drug)  # ensure drug list has these
        all_genes_phenotypes.add(condition)
        
    all_conditions_list = list(all_genes_phenotypes)
    
    print("Generating negative genetic samples via discrete function...")
    negative_genetic_pairs = generate_negative_samples(positive_genetic_pairs, all_drugs_list, all_conditions_list, len(positive_genetic_pairs))
    
    X_texts = []
    y_labels = []
    
    # Add positive DDI (Risk/Danger)
    for p1, p2 in positive_ddi_pairs:
        X_texts.append(f"{p1} | {p2}")
        y_labels.append(1)
        
    # Add negative DDI (Safe)
    for p1, p2 in negative_ddi_pairs:
        X_texts.append(f"{p1} | {p2}")
        y_labels.append(0)
        
    # Add positive Genetic (Risk/Danger)
    for d, c in positive_genetic_pairs:
        X_texts.append(f"{d} | {c}")
        y_labels.append(1)
        
    # Add negative Genetic (Safe)
    for d, c in negative_genetic_pairs:
        X_texts.append(f"{d} | {c}")
        y_labels.append(0)
        
    df = pd.DataFrame({'text': X_texts, 'label': y_labels})
    
    print("\nTraining Model on TF-IDF features...")
    from sklearn.linear_model import LogisticRegression
    
    # We use a skewed class_weight to heavily penalize missing DANGER (1) 
    # This naturally drastically improves Recall for Danger at the cost of Precision
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))),
        ('clf', LogisticRegression(class_weight={0: 1, 1: 5}, max_iter=1000, random_state=42))
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    
    print("\n--- CDSS ML PIPELINE EVALUATION ---")
    print(f"Accuracy Score: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred, target_names=['Safe', 'Danger']))
    
    joblib.dump(pipeline, 'cdss_model.joblib')
    print("\n✅ Model saved natively to cdss_model.joblib.")

if __name__ == "__main__":
    build_and_train_cdss_model()
