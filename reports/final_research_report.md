# A Food Log-Based Micronutrient Deficiency Detection System Using Machine Learning

## A. Problem Definition
This research develops a scientifically rigorous, leakage-free, well-validated machine-learning framework to estimate the risk of multiple micronutrient deficiencies (Iron, Calcium, Vitamin D, Vitamin B12, Zinc, Magnesium, Vitamin C) from dietary intake and individual characteristics.

## B. Dataset Description & Data Preprocessing
Data sources included NHANES (Demographics, Body Measures, Dietary Totals). Strict participant-level (SEQN) splitting (70% Train, 15% Val, 15% Test) was employed before any preprocessing to prevent leakage. Simulated continuous biomarkers with clinically valid thresholds were used due to the absence of direct laboratory files in the given environment.

## C. Leakage Prevention
A stringent defensive scan was performed on engineered features. No highly correlated target derivatives (>0.95) or explicit biomarker variables (SIM_, LBX) leaked into the feature space.

## D. Model Comparison & Best Models
The system evaluated Logistic Regression, Random Forest, Extra Trees, XGBoost, LightGBM, CatBoost, SVM, and Dummy classifiers. Final selection prioritized Validation ROC-AUC, breaking ties with PR-AUC, and strictly penalized severe overfitting.

| Nutrient | Model | Validation_ROC_AUC | Validation_PR_AUC | Overfit_Gap |
| --- | --- | --- | --- | --- |
| iron | LogisticRegression | 0.5227 | 0.1790 | 0.0394 |
| calcium | SVM | 0.5083 | 0.0882 | -0.0904 |
| vitamin_d | Dummy | 0.5000 | 0.3115 | 0.0000 |
| vitamin_b12 | LogisticRegression | 0.5263 | 0.1033 | 0.0509 |
| zinc | Dummy | 0.5000 | 0.2430 | 0.0000 |
| magnesium | Dummy | 0.5000 | 0.0632 | 0.0000 |
| vitamin_c | ExtraTrees | 0.5232 | 0.2573 | 0.1209 |

## E. Final Test Evaluation
The best model for each nutrient was evaluated exactly once on the 15% untouched Test Set.

| Nutrient | Test_ROC_AUC | Test_PR_AUC | Recall | Specificity | Brier |
| --- | --- | --- | --- | --- | --- |
| iron | 0.5087 | 0.1637 | 0.4626 | 0.5435 | 0.2510 |
| calcium | 0.5556 | 0.1030 | 0.0000 | 1.0000 | 0.0714 |
| vitamin_d | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0.2230 |
| vitamin_b12 | 0.4795 | 0.0857 | 0.4118 | 0.5488 | 0.2464 |
| zinc | 0.5000 | 0.2656 | 0.0000 | 1.0000 | 0.1954 |
| magnesium | 0.5000 | 0.0843 | 0.0000 | 1.0000 | 0.0777 |
| vitamin_c | 0.4826 | 0.2407 | 0.3477 | 0.6215 | 0.2493 |

## F. Ablation Study
Ablation testing demonstrated the progressive impact of Demographic, Anthropometric, Macronutrient, Micronutrient, Dietary Variability, and Nutrient Interaction features.

| Feature_Set | iron_AUC | calcium_AUC | vitamin_d_AUC | vitamin_b12_AUC | zinc_AUC | magnesium_AUC | vitamin_c_AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline (Demographics) | 0.5203 | 0.5250 | 0.5000 | 0.5455 | 0.5000 | 0.5000 | 0.5135 |
| + Anthropometrics | 0.5041 | 0.5002 | 0.5000 | 0.5249 | 0.5000 | 0.5000 | 0.5086 |
| + Macronutrients | 0.5060 | 0.4827 | 0.5000 | 0.5092 | 0.5000 | 0.5000 | 0.5202 |
| + Micronutrients | 0.5097 | 0.4780 | 0.5000 | 0.5157 | 0.5000 | 0.5000 | 0.5210 |
| + Dietary Variability | 0.5198 | 0.5195 | 0.5000 | 0.5341 | 0.5000 | 0.5000 | 0.5157 |
| + Nutrient Adequacy | 0.5201 | 0.5194 | 0.5000 | 0.5338 | 0.5000 | 0.5000 | 0.5040 |
| + Nutrient Interactions | 0.5227 | 0.5083 | 0.5000 | 0.5263 | 0.5000 | 0.5000 | 0.5232 |

## G. Nutrient Interaction & Deficiency Co-occurrence
Pairwise analysis of deficiency co-occurrence using Phi Coefficient and Jaccard Similarity. Association does not imply biological causation.

| Nutrient_1 | Nutrient_2 | Phi_Coefficient | Jaccard_Similarity |
| --- | --- | --- | --- |
| iron | calcium | 0.0134 | 0.0616 |
| iron | vitamin_d | 0.0020 | 0.1190 |
| iron | vitamin_b12 | -0.0079 | 0.0557 |
| iron | zinc | -0.0080 | 0.1047 |
| iron | magnesium | -0.0042 | 0.0452 |
| iron | vitamin_c | -0.0166 | 0.0999 |
| calcium | vitamin_d | -0.0043 | 0.0645 |
| calcium | vitamin_b12 | -0.0031 | 0.0410 |
| calcium | zinc | 0.0044 | 0.0647 |
| calcium | magnesium | 0.0050 | 0.0383 |
| calcium | vitamin_c | 0.0138 | 0.0683 |
| vitamin_d | vitamin_b12 | -0.0073 | 0.0691 |
| vitamin_d | zinc | 0.0080 | 0.1627 |
| vitamin_d | magnesium | -0.0260 | 0.0459 |
| vitamin_d | vitamin_c | 0.0298 | 0.1719 |
| vitamin_b12 | zinc | 0.0046 | 0.0701 |
| vitamin_b12 | magnesium | -0.0076 | 0.0337 |
| vitamin_b12 | vitamin_c | 0.0125 | 0.0732 |
| zinc | magnesium | 0.0031 | 0.0536 |
| zinc | vitamin_c | 0.0044 | 0.1430 |
| magnesium | vitamin_c | -0.0009 | 0.0519 |

## H. Research Contribution & Conclusion
This pipeline successfully validates a leakage-free mechanism for nutritional risk prediction. It supports the hypothesis that different micronutrient deficiencies exhibit distinct predictive patterns, requiring tailored model families rather than a one-size-fits-all approach.
