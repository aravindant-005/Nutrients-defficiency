import pandas as pd
import os

def display_results():
    csv_path = "reports/model_comparison.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    df = pd.read_csv(csv_path)
    nutrients = df['Nutrient'].unique()
    
    print("\n" + "="*95)
    print("      MICRONUTRIENT DEFICIENCY RISK SCREENING - MODEL COMPARISON REPORT")
    print("="*95)
    
    for nutrient in nutrients:
        sub_df = df[df['Nutrient'] == nutrient].copy()
        
        # Sort by ROC-AUC
        sub_df = sub_df.sort_values(by='ROC_AUC_Score', ascending=False)
        
        print(f"\n Target Nutrient: {nutrient.upper()}")
        print("-" * 95)
        print(f"{'Model Family':<18} | {'Train Acc':<10} | {'Val Acc':<10} | {'Acc Gap':<9} | {'ROC-AUC':<9} | {'Recall (Sens)':<13} | {'Spec':<8} | {'Status':<10}")
        print("-" * 95)
        
        best_row = sub_df.iloc[0]
        
        for _, row in sub_df.iterrows():
            mname = row['Model']
            tr_acc = f"{row['Train_Accuracy']:.4f}"
            val_acc = f"{row['Validation_Accuracy']:.4f}"
            gap = f"{row['Accuracy_Gap']:+.4f}"
            auc = f"{row['ROC_AUC_Score']:.4f}"
            rec = f"{row['Recall_Sensitivity']:.4f}"
            spec = f"{row['Specificity']:.4f}"
            
            is_best = (mname == best_row['Model'])
            status = "SELECTED" if is_best else "Candidate"
            
            prefix = "-> " if is_best else "   "
            print(f"{prefix}{mname:<15} | {tr_acc:<10} | {val_acc:<10} | {gap:<9} | {auc:<9} | {rec:<13} | {spec:<8} | {status:<10}")
            
        print("-" * 95)

if __name__ == "__main__":
    display_results()
