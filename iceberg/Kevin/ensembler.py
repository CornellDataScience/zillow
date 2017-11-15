import numpy as np
import pandas as pd


pred = pd.read_csv('ensem_predictions.csv')
"""
pred_1 = (pd.read_csv('predictions.csv'))["is_iceberg"]
pred_2 = (pd.read_csv('predictions_2.csv'))["is_iceberg"]
pred_3 = (pd.read_csv('predictions_3.csv'))["is_iceberg"]
pred_4 = (pd.read_csv('predictions_4.csv'))["is_iceberg"]
pred_5 = (pd.read_csv('predictions_5.csv'))["is_iceberg"]
pred_6 = (pd.read_csv('predictions_6.csv'))["is_iceberg"]
pred_7 = (pd.read_csv('predictions_7.csv'))["is_iceberg"]
pred_8 = (pd.read_csv('predictions_8.csv'))["is_iceberg"]   """

ensem_preds = pd.read_csv('ensem_predictions.csv')["is_iceberg"]
resnet_preds = pd.read_csv('resnet_preds.csv')["is_iceberg"]

#ensembled_predictions = (pred_1 + pred_2 + pred_3 + pred_4 + pred_5 + pred_6 + pred_7 + pred_8) / 8.0
ensembled_predictions = (ensem_preds + resnet_preds) / 2.0

print(ensembled_predictions)
pred_df = pred['id'].copy()
pred_df = pd.concat([pred_df, ensembled_predictions], axis=1)
print(pred_df)
print("creating csv")
pred_df.to_csv('res_16combo.csv', index = False)