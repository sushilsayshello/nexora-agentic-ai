# Nexora Sentinel: A Machine Learning Pipeline for Transaction Trustworthiness

## Overview

Nexora Sentinel is a comprehensive machine learning pipeline designed to assess the trustworthiness of online transactions. It integrates multiple specialized AI models to provide a holistic 'Trust Score' and a definitive decision (APPROVED, REVIEW, BLOCKED), enhancing security and ensuring accessible and fair commerce.

## Project Components

The pipeline consists of four main machine learning models, each addressing a critical aspect of transaction trustworthiness:

1.  **Purchase Intent Predictor (Model 1)**
    *   **Purpose:** Predicts a user's likelihood to complete a purchase based on their browsing behavior.
    *   **Dataset:** `online_shoppers_intention.csv`
    *   **Model:** Optimized XGBoost Classifier.
    *   **Key Features:** `PageValues`, `BounceRates`, `ExitRates`, `VisitorType`, `TrafficType`, `Month`.
    *   **Techniques:** Label Encoding for categorical features, StandardScaler for numerical features, and class weighting to address imbalance.

2.  **Fraud Risk Detector (Model 2)**
    *   **Purpose:** Identifies potentially fraudulent transactions.
    *   **Dataset:** `creditcard.csv`
    *   **Model:** Optimized XGBoost Classifier.
    *   **Key Features:** Anonymized transaction features (V1-V28), `Amount`, `Time`.
    *   **Techniques:** StandardScaler for `Amount` and `Time`, and class weighting for severe class imbalance.

3.  **Accessibility Mandate Recommender (Model 3)**
    *   **Purpose:** Recommends appropriate verification methods based on a user's accessibility profile.
    *   **Dataset:** `Accessibility dataset.csv` (synthetic data generated if not available).
    *   **Model:** Random Forest Classifier (or XGBoost, showing high accuracy).
    *   **Key Features:** User behavioral data and device settings (e.g., `screen_reader_usage`, `high_contrast_enabled`, `device_type`).
    *   **Techniques:** One-hot encoding for `device_type`.

4.  **Nexora Trust Engine (Core Integration)**
    *   **Purpose:** Combines the outputs from the Purchase Intent, Fraud Risk, and Accessibility models into a single, weighted `trust_score`.
    *   **Decision Logic:** Based on predefined thresholds, it classifies transactions as APPROVED, REVIEW, or BLOCKED.
    *   **Customization:** Configurable weights for each component and thresholds for decisions.

## Data Sources

*   `Accessibility dataset.csv`: World Health Organization (WHO) disability statistics used for understanding accessibility needs.
*   `ai_company_adoption.csv`: Data on AI adoption trends over time, providing context for the project's relevance.
*   `creditcard.csv`: Anonymized credit card transaction data, heavily imbalanced, used for fraud detection.
*   `online_shoppers_intention.csv`: User browsing data to predict online purchase intent.

_Note: Synthetic datasets are generated for `shoppers`, `creditcard`, and `accessibility` if the original files are not found, ensuring pipeline executability._

## Key Features and Innovations

*   **End-to-End ML Pipeline:** A fully integrated system from data loading and preprocessing to model training, evaluation, and decision-making.
*   **Robust Imbalance Handling:** Utilizes techniques like class weighting and SMOTE to effectively train models on imbalanced datasets (e.g., fraud detection, purchase intent).
*   **Modular Architecture:** The Nexora Trust Engine is encapsulated within a Python class (`NexoraTrustEngine`) for reusability and clarity.
*   **Accessibility Integration:** Incorporates accessibility profiles into the trust assessment, recommending tailored verification methods.
*   **Comprehensive Evaluation:** Each model is rigorously evaluated using metrics such as AUC, Accuracy, Precision, Recall, F1-score, and visualized with ROC curves and Confusion Matrices.
*   **Dynamic Visualizations:** Generates various plots to illustrate data distributions, model performance, feature importances, AI adoption trends, and the final Trust Score breakdown.
*   **Model Persistence:** All trained models and the Trust Engine configuration are saved using `joblib` for future deployment and use.

## Setup and Usage

1.  **Dependencies:** Install necessary libraries using `pip install pandas numpy scikit-learn xgboost imbalanced-learn matplotlib seaborn joblib`.
2.  **Data:** Place the required CSV files (`online_shoppers_intention.csv`, `creditcard.csv`, `Accessibility dataset.csv`, `ai_company_adoption.csv`) in the same directory as the notebook, or rely on synthetic data generation.
3.  **Run the Notebook:** Execute the Jupyter notebook cells sequentially. The pipeline will automatically load data, train models, and perform analysis.

## Outputs

The pipeline generates several outputs, including:

*   **Model Performance Reports:** Classification reports, confusion matrices, and ROC curves for each predictive model.
*   **Feature Importance Plots:** Visualizations highlighting key features for purchase intent prediction.
*   **Trust Score Analysis:** Detailed breakdown of contributions to the final Trust Score for different scenarios.
*   **Mandate Distribution:** Visualization of recommended accessibility verification methods.
*   **AI Adoption Trends:** Plots showing the growth of AI adoption and task automation over time.
*   **Saved Models:** Serialized model files (`.pkl`) for each component and the Trust Engine configuration.

This project provides a robust framework for building intelligent, ethical, and user-centric transaction verification systems.
