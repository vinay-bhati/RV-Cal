import streamlit as st
import pandas as pd
import numpy as np
import math

# Load data based on gender
def load_data(gender):
    if gender == 'Male':
        df_fev1 = pd.read_csv("Male FEV1.csv")
        df_fvc = pd.read_csv("Male FVC.csv")
        df_fev1_fvc = pd.read_csv("Male FEV1 FVC.csv")
        df_rv = pd.read_csv("Male RV.csv")
    else:
        df_fev1 = pd.read_csv("Female FEV1.csv")
        df_fvc = pd.read_csv("Female FCV.csv")
        df_fev1_fvc = pd.read_csv("Female FEV1 FVC.csv")
        df_rv = pd.read_csv("Female RV.csv")
    return df_fev1, df_fvc, df_fev1_fvc,df_rv

# Calculate FEV1, FVC, and FEV1/FVC based on gender
def calculate_values(age, height, gender):
    df_fev1, df_fvc, df_fev1_fvc, df_rv = load_data(gender)
    spline_fev1 = df_fev1[df_fev1['age'] == age].iloc[0]
    spline_fvc = df_fvc[df_fvc['age'] == age].iloc[0]
    spline_fev1_fvc = df_fev1_fvc[df_fev1_fvc['age'] == age].iloc[0]
    spline_rv = df_rv[df_rv['age'] == age].iloc[0]
    
    if gender == 'Male':
        # Male calculations
        M_FEV1 = np.exp(-11.399108 + 2.462664 * np.log(height) - 0.011394 * np.log(age) + spline_fev1['M Spline'])
        M_FVC = np.exp(-12.629131 + 2.727421 * np.log(height) + 0.009174 * np.log(age) + spline_fvc['M Spline'])
        M_FEV1_FVC = np.exp(1.022608 - 0.218592 * np.log(height) - 0.027586 * np.log(age) + spline_fev1_fvc['M Spline'])
        M_RV = np.exp(-2.37211 + 0.01346 * age + 0.01307 * height + spline_rv['M Spline'])
    else:
        # Female calculations
        M_FEV1 = np.exp(-10.901689 + 2.385928 * np.log(height) - 0.076386 * np.log(age) + spline_fev1['M Spline'])
        M_FVC = np.exp(-12.055901 + 2.621579 * np.log(height) - 0.035975 * np.log(age) + spline_fvc['M Spline'])
        M_FEV1_FVC = np.exp(0.9189568 - 0.1840671 * np.log(height) - 0.0461306 * np.log(age) + spline_fev1_fvc['M Spline'])
        M_RV = np.exp(-2.50593 + 0.01307 * age + 0.01379 * height + spline_rv['M Spline'])
    
    return M_FEV1, M_FVC, M_FEV1_FVC,M_RV

# Streamlit interface
st.title('Pulmonary Function Test Calculator')

gender = st.radio("Select Gender:", ('Male', 'Female'))
age = st.number_input("Enter Age:", min_value=1, max_value=100)
height = st.number_input("Enter Height (in cm):", min_value=50, max_value=250)
measured_fev1 = st.number_input("Enter Measured FEV1 (in liters):", min_value=0.0, format="%.2f")
measured_fvc = st.number_input("Enter Measured FVC (in liters):", min_value=0.0, format="%.2f")

if st.button('Calculate'):
    fev1, fvc, fev1_fvc,rv = calculate_values(age, height, gender)
    percent_predicted_fev1 = (measured_fev1 / fev1) * 100
    percent_predicted_fvc = (measured_fvc / fvc) * 100
    st.write(f"Pred_FEV1: {fev1:.3f} L")
    st.write(f"Pred_FVC: {fvc:.3f} L")
    st.write(f"Pred_FEV1/FVC Ratio: {fev1_fvc:.3%}")
    st.write(f"Pred_RV: {rv:.3f} L")
    st.write(f"% Predicted FEV1: {percent_predicted_fev1:.2f}%")
    st.write(f"% Predicted FVC: {percent_predicted_fvc:.2f}%")
