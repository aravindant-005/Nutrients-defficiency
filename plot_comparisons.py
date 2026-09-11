import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_model_comparison():
    # Load comparison data
    df = pd.read_csv("reports/model_comparison.csv")
    
    # We want to plot Validation ROC-AUC for all models across all nutrients
    plt.figure(figsize=(14, 8))
    sns.barplot(data=df, x='Nutrient', y='Validation_ROC_AUC', hue='Model', palette='viridis')
    
    plt.title('Validation ROC-AUC by Model and Nutrient', fontsize=16)
    plt.xlabel('Nutrient Target', fontsize=14)
    plt.ylabel('Validation ROC-AUC Score', fontsize=14)
    plt.axhline(0.5, color='red', linestyle='--', label='Random Guessing (0.5)')
    plt.legend(title='Machine Learning Model', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.ylim(0.4, 0.6) # since scores are generally low, zoom in
    
    plt.tight_layout()
    
    # Save the plot
    os.makedirs("reports/images", exist_ok=True)
    plot_path = "reports/images/model_comparison_auc.png"
    plt.savefig(plot_path, dpi=300)
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    plot_model_comparison()
