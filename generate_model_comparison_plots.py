import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

def generate_comparison_plots():
    csv_path = "reports/model_comparison.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    df = pd.read_csv(csv_path)
    os.makedirs("reports/plots", exist_ok=True)
    
    nutrients = df['Nutrient'].unique()
    colors = ['#34495e', '#2980b9', '#8e44ad', '#27ae60', '#e67e22']
    
    # -----------------------------------------------------------
    # 1. INDIVIDUAL NUTRIENT MODEL COMPARISON BAR CHARTS (PNG)
    # -----------------------------------------------------------
    for nutrient in nutrients:
        sub_df = df[df['Nutrient'] == nutrient].copy()
        
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        
        models = sub_df['Model'].tolist()
        x = np.arange(len(models))
        width = 0.22
        
        rects1 = ax.bar(x - width, sub_df['ROC_AUC_Score'], width, label='ROC-AUC Score', color='#27ae60')
        rects2 = ax.bar(x, sub_df['Recall_Sensitivity'], width, label='Recall (Sensitivity)', color='#2980b9')
        rects3 = ax.bar(x + width, sub_df['Validation_Accuracy'], width, label='Validation Accuracy', color='#8e44ad')
        
        ax.set_ylabel('Metric Value (0.0 - 1.0)', fontsize=12, fontweight='bold')
        ax.set_title(f'Model Family Comparison - {nutrient.upper()} Deficiency Screening', fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=11, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
        
        # Add value labels
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.3f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, rotation=45)

        autolabel(rects1)
        autolabel(rects2)
        autolabel(rects3)
        
        plt.tight_layout()
        save_path = f"reports/plots/Model_Comparison_{nutrient.upper()}.png"
        plt.savefig(save_path)
        plt.close()
        print(f"Saved comparison plot: {save_path}")

    # -----------------------------------------------------------
    # 2. MASTER ALL-NUTRIENTS ROC-AUC COMPARISON CHART (PNG)
    # -----------------------------------------------------------
    plt.figure(figsize=(12, 7), dpi=300)
    pivot_auc = df.pivot(index='Nutrient', columns='Model', values='ROC_AUC_Score')
    
    # Reorder columns if needed
    model_order = ['LogisticRegression', 'RandomForest', 'ExtraTrees', 'XGBoost', 'CatBoost']
    pivot_auc = pivot_auc[[m for m in model_order if m in pivot_auc.columns]]
    
    ax = pivot_auc.plot(kind='bar', figsize=(12, 7), width=0.8, color=['#7f8c8d', '#3498db', '#9b59b6', '#2ecc71', '#e67e22'])
    plt.ylabel('Validation ROC-AUC Score', fontsize=12, fontweight='bold')
    plt.xlabel('Target Micronutrient', fontsize=12, fontweight='bold')
    plt.title('Master Model Comparison: Validation ROC-AUC Across All Nutrients', fontsize=14, fontweight='bold', pad=15)
    plt.xticks(rotation=0, fontsize=10, fontweight='bold')
    plt.ylim(0.4, 1.05)
    plt.axhline(0.70, color='red', linestyle='--', linewidth=1, label='Clinical Utility Threshold (AUC >= 0.70)')
    plt.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.9)
    
    plt.tight_layout()
    master_path = "reports/plots/Master_Model_Comparison_ROC_AUC.png"
    plt.savefig(master_path)
    plt.close()
    print(f"Saved master comparison plot: {master_path}")

if __name__ == "__main__":
    generate_comparison_plots()
