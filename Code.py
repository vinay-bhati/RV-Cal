import streamlit as st
import pandas as pd
import numpy as np
import math
from validate_email import validate_email

# Initialize session state variables if they don't exist
if 'standard' not in st.session_state:
    st.session_state['standard'] = None
if 'has_fvc_pred' not in st.session_state:
    st.session_state['has_fvc_pred'] = None

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


# First command: set page configuration
st.set_page_config(
    page_title='Pulmonary Function Test Calculator',
    layout='wide',
    initial_sidebar_state='expanded'
)

## CSS to increase font size for specific elements identified via developer tools
st.markdown("""
<style>
/* Targeting paragraphs within the Markdown container for widget labels */
div[data-testid="stMarkdownContainer"] p {
    font-size: 18px !important;  /* Increase font size of labels */
}

/* Customize input fields to increase font size */
input, select, textarea {
    font-size: 18px !important;  /* Increase font size in input fields */
    height: 50px !important;  /* Make input fields taller for better interaction */
}

/* Enhance the visibility of buttons */
button {
    font-size: 18px !important;
    height: 50px !important;
}
</style>
""", unsafe_allow_html=True)

st.title('Pulmonary Function Test Calculator')

email = st.text_input("Enter your email ID:")
is_email_valid = validate_email(email)
standard = st.radio("Select Standard:", ('GLI', 'ECSC'), index=0)

if is_email_valid:
    if standard == 'GLI':
        has_fvc_pred = st.radio("Do You Have FVC % Predicted?", ('Yes', 'No'))
        if has_fvc_pred == 'Yes':
            st.write("Work in Progress. Functionality to handle existing FVC % Predicted values is being developed.")
        elif has_fvc_pred == 'No':
            gender = st.radio("Select Gender:", ('Male', 'Female'))

            # Create a layout with columns for age, height, FEV1, and FVC on one line
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                age = st.number_input("Enter Age:", min_value=1, max_value=100, step=1, key='age')

            with col2:
                height = st.number_input("Enter Height (in cm):", min_value=50, max_value=250, step=1, key='height')

            with col3:
                measured_fev1 = st.number_input("Enter Measured FEV1 (in liters):", min_value=0.0, format="%.2f", step=0.01, key='fev1')

            with col4:
                measured_fvc = st.number_input("Enter Measured FVC (in liters):", min_value=0.0, format="%.2f", step=0.01, key='fvc')

            # Calculate button can be placed below the inputs or in a new line
            if st.button('Calculate'):
                fev1, fvc, fev1_fvc, rv = calculate_values(age, height, gender)
                percent_predicted_fev1 = (measured_fev1 / fev1) * 100
                percent_predicted_fvc = (measured_fvc / fvc) * 100
                st.write(f"Predicted FEV1: {fev1:.2f} L")
                st.write(f"Predicted FVC: {fvc:.2f} L")
                st.write(f"Predicted FEV1/FVC Ratio: {fev1_fvc:.2%}")
                st.write(f"Predicted RV: {rv:.2f} L")
                st.write(f"% Predicted FEV1: {percent_predicted_fev1:.2f}%")
                st.write(f"% Predicted FVC: {percent_predicted_fvc:.2f}%")
    elif standard == 'ECSC':
        st.write("Work in Progress. This standard is not available yet.")
else:
    st.error("Invalid email address. Please enter a valid email.")