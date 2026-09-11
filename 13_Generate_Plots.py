import os
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix, roc_auc_score, average_precision_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

def generate_individual_plots():
    logging.info("Starting Separate Plot Generation Module (Module 13)...")
    
    os.makedirs("reports/plots", exist_ok=True)
    
    val_file = "processed_data/val_engineered.csv"
    if not os.path.exists(val_file):
        logging.error(f"Validation file {val_file} missing.")
        return
        
    val_df = pd.read_csv(val_file)
    targets = [c for c in val_df.columns if c.startswith('target_')]
    
    valid_features = [c for c in val_df.columns if not c.startswith('target_') and c != 'SEQN']
    if os.path.exists("models/feature_names.json"):
        with open("models/feature_names.json") as f:
            valid_features = json.load(f)
            
    X_val = val_df[valid_features].select_dtypes(include=[np.number])
    models = ['LogisticRegression', 'RandomForest', 'ExtraTrees', 'XGBoost', 'CatBoost']
    
    for target in targets:
        y_val = val_df[target]
        nutrient = target.replace('target_', '').upper()
        
        logging.info(f"Generating individual evaluation plots for {nutrient}...")
        
        # ----------------------------------------------------
        # 1. STANDALONE ROC CURVE PIC
        # ----------------------------------------------------
        plt.figure(figsize=(8, 6), dpi=300)
        plt.plot([0, 1], [0, 1], 'k--', label='Chance (AUC = 0.50)')
        
        loaded_models = {}
        for mname in models:
            mpath = f"models/tuning/best_{mname}_{target.replace('target_', '')}.pkl"
            if os.path.exists(mpath):
                model = joblib.load(mpath)
                loaded_models[mname] = model
                try:
                    y_prob = model.predict_proba(X_val)[:, 1]
                    fpr, tpr, _ = roc_curve(y_val, y_prob)
                    auc_val = roc_auc_score(y_val, y_prob)
                    plt.plot(fpr, tpr, label=f"{mname} (AUC = {auc_val:.4f})", linewidth=2)
                except Exception as e:
                    pass
                    
        plt.xlabel('False Positive Rate (1 - Specificity)', fontsize=12, fontweight='bold')
        plt.ylabel('True Positive Rate (Sensitivity / Recall)', fontsize=12, fontweight='bold')
        plt.title(f'ROC Curve - {nutrient} Deficiency Risk Screening', fontsize=14, fontweight='bold', pad=15)
        plt.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9)
        plt.tight_layout()
        roc_pic_path = f"reports/plots/ROC_Curve_{nutrient}.png"
        plt.savefig(roc_pic_path)
        plt.close()
        logging.info(f"Saved: {roc_pic_path}")
        
        # ----------------------------------------------------
        # 2. STANDALONE PRECISION-RECALL CURVE PIC
        # ----------------------------------------------------
        plt.figure(figsize=(8, 6), dpi=300)
        for mname, model in loaded_models.items():
            try:
                y_prob = model.predict_proba(X_val)[:, 1]
                prec, rec, _ = precision_recall_curve(y_val, y_prob)
                pr_auc = average_precision_score(y_val, y_prob)
                plt.plot(rec, prec, label=f"{mname} (PR-AUC = {pr_auc:.4f})", linewidth=2)
            except Exception as e:
                pass
                
        plt.xlabel('Recall (Sensitivity)', fontsize=12, fontweight='bold')
        plt.ylabel('Precision', fontsize=12, fontweight='bold')
        plt.title(f'Precision-Recall Curve - {nutrient} Deficiency', fontsize=14, fontweight='bold', pad=15)
        plt.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
        plt.tight_layout()
        pr_pic_path = f"reports/plots/PR_Curve_{nutrient}.png"
        plt.savefig(pr_pic_path)
        plt.close()
        logging.info(f"Saved: {pr_pic_path}")
        
        # ----------------------------------------------------
        # 3. STANDALONE CONFUSION MATRIX HEATMAP PIC (Best Model)
        # ----------------------------------------------------
        best_model_path = f"models/best_model_{target.replace('target_', '')}.pkl"
        if os.path.exists(best_model_path):
            best_model = joblib.load(best_model_path)
            try:
                y_prob = best_model.predict_proba(X_val)[:, 1]
                y_pred = (y_prob >= 0.5).astype(int)
                cm = confusion_matrix(y_val, y_pred)
                
                plt.figure(figsize=(7, 5), dpi=300)
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                            xticklabels=['Normal', 'Deficient'],
                            yticklabels=['Normal', 'Deficient'],
                            annot_kws={"size": 14, "weight": "bold"})
                plt.xlabel('Predicted Clinical Status', fontsize=12, fontweight='bold')
                plt.ylabel('True Ground-Truth Status', fontsize=12, fontweight='bold')
                plt.title(f'Confusion Matrix (Selected Best Model) - {nutrient}', fontsize=13, fontweight='bold', pad=15)
                plt.tight_layout()
                cm_pic_path = f"reports/plots/Confusion_Matrix_{nutrient}.png"
                plt.savefig(cm_pic_path)
                plt.close()
                logging.info(f"Saved: {cm_pic_path}")
            except Exception as e:
                pass

        # ----------------------------------------------------
        # 4. STANDALONE FEATURE IMPORTANCE PIC
        # ----------------------------------------------------
        if os.path.exists(best_model_path):
            best_model = joblib.load(best_model_path)
            try:
                clf = best_model.named_steps.get('classifier', best_model)
                importances = None
                if hasattr(clf, 'feature_importances_'):
                    importances = clf.feature_importances_
                elif hasattr(clf, 'coef_'):
                    importances = np.abs(clf.coef_[0])
                    
                if importances is not None and len(importances) == len(valid_features):
                    feat_imp = pd.Series(importances, index=valid_features).sort_values(ascending=False).head(10)
                    plt.figure(figsize=(9, 5), dpi=300)
                    sns.barplot(x=feat_imp.values, y=feat_imp.index, palette='Blues_r')
                    plt.xlabel('Importance / Feature Attribution Score', fontsize=12, fontweight='bold')
                    plt.ylabel('Feature Variable', fontsize=12, fontweight='bold')
                    plt.title(f'Top 10 Feature Importances - {nutrient}', fontsize=14, fontweight='bold', pad=15)
                    plt.tight_layout()
                    fi_pic_path = f"reports/plots/Feature_Importance_{nutrient}.png"
                    plt.savefig(fi_pic_path)
                    plt.close()
                    logging.info(f"Saved: {fi_pic_path}")
            except Exception as e:
                pass

        # ----------------------------------------------------
        # 5. STANDALONE TRAIN VS TEST ACCURACY DIAGNOSTIC BAR CHART PIC
        # ----------------------------------------------------
        comp_csv = "reports/cross_validation_results.csv"
        if os.path.exists(comp_csv):
            cv_df = pd.read_csv(comp_csv)
            nut_cv = cv_df[cv_df['Nutrient'] == target.replace('target_', '')]
            if not nut_cv.empty:
                plt.figure(figsize=(9, 5), dpi=300)
                x = np.arange(len(nut_cv))
                width = 0.35
                plt.bar(x - width/2, nut_cv['Train_Accuracy'], width, label='Training Accuracy', color='#2b5c8f')
                plt.bar(x + width/2, nut_cv['Validation_Accuracy'], width, label='Validation Accuracy', color='#d95f02')
                plt.xticks(x, nut_cv['Model'], rotation=15, fontweight='bold')
                plt.ylabel('Accuracy Score', fontsize=12, fontweight='bold')
                plt.ylim(0, 1.05)
                plt.title(f'Overfitting Diagnostic: Train vs Test Accuracy - {nutrient}', fontsize=13, fontweight='bold', pad=15)
                plt.legend(loc='lower right', frameon=True)
                plt.tight_layout()
                gap_pic_path = f"reports/plots/Train_vs_Test_Accuracy_{nutrient}.png"
                plt.savefig(gap_pic_path)
                plt.close()
                logging.info(f"Saved: {gap_pic_path}")

    # ----------------------------------------------------
    # 6. GLOBAL ABLATION STUDY PIC
    # ----------------------------------------------------
    ablation_csv = "reports/ablation_results.csv"
    if os.path.exists(ablation_csv):
        abl_df = pd.read_csv(ablation_csv)
        plt.figure(figsize=(10, 6), dpi=300)
        sns.barplot(data=abl_df, x='Nutrient', y='Validation_ROC_AUC', hue='Feature_Subset', palette='viridis')
        plt.ylabel('Validation ROC-AUC Score', fontsize=12, fontweight='bold')
        plt.title('Feature Group Ablation Study Comparison', fontsize=14, fontweight='bold', pad=15)
        plt.legend(title='Feature Subset', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        abl_pic_path = "reports/plots/Ablation_Study_ROC_AUC.png"
        plt.savefig(abl_pic_path)
        plt.close()
        logging.info(f"Saved: {abl_pic_path}")

    # ----------------------------------------------------
    # 7. DEFICIENCY CO-OCCURRENCE HEATMAP PIC
    # ----------------------------------------------------
    co_csv = "reports/deficiency_co_occurrence.csv"
    if os.path.exists(co_csv):
        co_df = pd.read_csv(co_csv, index_col=0)
        plt.figure(figsize=(8, 6), dpi=300)
        sns.heatmap(co_df, annot=True, fmt='.2f', cmap='YlGnBu', cbar=True)
        plt.title('Deficiency Target Co-Occurrence Matrix (Correlation)', fontsize=13, fontweight='bold', pad=15)
        plt.tight_layout()
        co_pic_path = "reports/plots/Deficiency_CoOccurrence_Heatmap.png"
        plt.savefig(co_pic_path)
        plt.close()
        logging.info(f"Saved: {co_pic_path}")

    logging.info("Separate Plot Generation Module Completed Successfully.")

if __name__ == "__main__":
    generate_individual_plots()
