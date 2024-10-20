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
        df_fev1 = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Male FEV1.csv")
        df_fvc = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Male FVC.csv")
        df_fev1_fvc = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Male FEV1 FVC.csv")
        #df_rv = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Male RV.csv")
    else:
        df_fev1 = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Female FEV1.csv")
        df_fvc = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Female FCV.csv")
        df_fev1_fvc = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Female FEV1 FVC.csv")
        #df_rv = pd.read_csv(r"C:\Users\vbhati\OneDrive - Pulmonx\Documents\GLI Calculator\Female RV.csv")
    return df_fev1, df_fvc, df_fev1_fvc

# Calculate FEV1, FVC, and FEV1/FVC based on gender
def calculate_values(age, height, gender):
    df_fev1, df_fvc, df_fev1_fvc = load_data(gender)
    spline_fev1 = df_fev1[df_fev1['age'] == age].iloc[0]
    spline_fvc = df_fvc[df_fvc['age'] == age].iloc[0]
    spline_fev1_fvc = df_fev1_fvc[df_fev1_fvc['age'] == age].iloc[0]
    #spline_rv = df_rv[df_rv['age'] == age].iloc[0]
    
    if gender == 'Male':
        # Male calculations
        M_FEV1 = np.exp(-11.399108 + 2.462664 * np.log(height) - 0.011394 * np.log(age) + spline_fev1['M Spline'])
        M_FVC = np.exp(-12.629131 + 2.727421 * np.log(height) + 0.009174 * np.log(age) + spline_fvc['M Spline'])
        M_FEV1_FVC = np.exp(1.022608 - 0.218592 * np.log(height) - 0.027586 * np.log(age) + spline_fev1_fvc['M Spline'])
    else:
        # Female calculations
        M_FEV1 = np.exp(-10.901689 + 2.385928 * np.log(height) - 0.076386 * np.log(age) + spline_fev1['M Spline'])
        M_FVC = np.exp(-12.055901 + 2.621579 * np.log(height) - 0.035975 * np.log(age) + spline_fvc['M Spline'])
        M_FEV1_FVC = np.exp(0.9189568 - 0.1840671 * np.log(height) - 0.0461306 * np.log(age) + spline_fev1_fvc['M Spline'])
        #M_RV = np.exp(-2.50593 + 0.01307 * age + 0.01379 * height + spline_rv['M Spline'])
    
    return M_FEV1, M_FVC, M_FEV1_FVC,#M_RV

def calculate_rv_est(percent_predicted_fvc, measured_fev1_fvc, age, gender):
    # Converting gender to numeric value: 1 for Male, 0 for Female
    gender_numeric = 1 if gender == 'Male' else 0
    
    # Calculation as per the provided formula
    rv_est = round(
        (percent_predicted_fvc * 4.09177 +
         round(measured_fev1_fvc,3) * -208.123 +
         np.sqrt(percent_predicted_fvc) * -93.1544 +
         age * -2.01415 +
         gender_numeric * -11.0523 +
         909.1686), 1)
    
    return rv_est

def calculate_rv_predicted(rv_percent_est):
    rv150 = round((1 / (1 + math.exp(-1 * (-8.334997 + 0.0506715 * rv_percent_est)))), 3) * 100
    rv175 = round((1 / (1 + math.exp(-1 * (-10.22612 + 0.054502 * rv_percent_est)))), 3) * 100
    rv200 = round((1 / (1 + math.exp(-1 * (-10.69602 + 0.0515848 * rv_percent_est)))), 3) * 100
    return rv150, rv175, rv200


# First command: set page configuration
st.set_page_config(
    page_title='RV Estimate Calculator',
    layout='wide',
    initial_sidebar_state='expanded'
)

## CSS to increase font size for specific elements identified via developer tools
st.markdown("""
<style>
/* Targeting paragraphs within the Markdown container for widget labels */
div[data-testid="stMarkdownContainer"] p {
    font-size: 18px !important;  /* Increase font size of labels */
    font-weight: bold !important;  /* Make text bold */
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
/* Customizing the font size for metric values */
[data-testid="stMetricValue"] > div {
    font-size: 20px !important;  /* Set your desired font size here */
}
</style>
""", unsafe_allow_html=True)

st.title('RV Estimate Calculator')

email = st.text_input("Enter email ID:")

if email:
    is_email_valid = validate_email(email)
    if not is_email_valid:
        st.error("Invalid email address. Please enter a valid email.")
    else:
        # Place this where you define your interface components
        rv_threshold = st.slider("Select RV % Est Threshold for Patient Care:", 100, 200, 150)
        standard = st.radio("Select Standard:", ('GLI', 'ECSC'),horizontal=True,index=None)

        if standard == 'GLI':
            has_fvc_pred = st.radio("Do You Have FVC % Predicted?", ('Yes', 'No'),horizontal=True,index=None)
            if has_fvc_pred == 'Yes':
                gender = st.radio("Select Gender:", ('Male', 'Female'), horizontal=True,index=None)
        
                # Create layout with columns for age, measured FEV1, measured FVC, and FVC % Predicted
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    age = st.number_input("Enter Age (Years):", min_value=3, max_value=95, step=1, key='age_yes')
                with col2:
                    measured_fev1 = st.number_input("Enter Measured FEV1 (XX.XX):", min_value=0.0, format="%.2f", step=0.01, key='fev1_yes')
                with col3:
                    measured_fvc = st.number_input("Enter Measured FVC (XX.XX):", min_value=0.0, format="%.2f", step=0.01, key='fvc_yes')
                with col4:
                    fvc_percent_predicted = st.number_input("Enter FVC % Predicted:", min_value=0.0, format="%.1f", step=0.1, key='fvc_percent_pred')

                if st.button('Evaluate'):
                    # Display measured values and provided FVC % Predicted
                    col5, col6, col7, col8= st.columns(4)
                    with col5:
                        st.metric(label="Measured FEV1", value=f"{measured_fev1:.2f} L")
                    with col6:
                        st.metric(label="Measured FVC", value=f"{measured_fvc:.2f} L")
                    with col7:
                        st.metric(label="FVC % Predicted", value=f"{fvc_percent_predicted:.1f}%")
                    with col8:
                        # Calculate FEV1/FVC ratio from measured values and display
                        measured_fev1_fvc = measured_fev1 / measured_fvc if measured_fvc != 0 else 0
                        st.metric(label="Measured FEV1/FVC", value=f"{measured_fev1_fvc:.2f}")
                    
                    col9, col10, col11,col12 = st.columns(4)
                    rv_percent_est = calculate_rv_est(fvc_percent_predicted, measured_fev1_fvc, age, gender)
                    # Calculate RV % Predicted Prevalence
                    RV150, RV175, RV200 = calculate_rv_predicted(rv_percent_est)
                    # Adding a row to display RV % est
                    col9, col10, col11, col12 = st.columns(4)
                    with col9:
                        st.metric(label="RV % Estimate", value=f"{rv_percent_est:.1f}")
                    with col10:
                        st.metric(label="RV >150% Probability", value=f"{RV150:.1f}%")
                    with col11:
                        st.metric(label="RV >175% Probability", value=f"{RV175:.1f}%")
                    with col12:
                        st.metric(label="RV >200% Probability", value=f"{RV200:.1f}%")

                    st.write("Final Result")
                    # Final Result based on the RV% Est threshold
                    if rv_percent_est >= rv_threshold:
                        st.success(f"Patient Can be Sent to Next Step 🟢")
                    else:
                        st.error(f"Patient is Fit, No Further Care Required 🔴")
                    
            elif has_fvc_pred == 'No':
                gender = st.radio("Select Gender:", ('Male', 'Female'),horizontal=True,index=None)

                # Create a layout with columns for age, height, FEV1, and FVC on one line
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    age = st.number_input("Enter Age (Years):", min_value=3, max_value=95, step=1, key='age')
                with col2:
                    height = st.number_input("Enter Height (in cm):", min_value=150, max_value=250, step=1, key='height')
                with col3:
                    measured_fev1 = st.number_input("Enter Measured FEV1 (XX.XX):", min_value=0.0, format="%.2f", step=0.01, key='fev1')
                with col4:
                    measured_fvc = st.number_input("Enter Measured FVC (XX.XX):", min_value=0.0, format="%.2f", step=0.01, key='fvc')

                # Calculate button can be placed below the inputs or in a new line
                if st.button('Calculate'):
                    fev1, fvc, fev1_fvc = calculate_values(age, height, gender)
                    percent_predicted_fev1 = (measured_fev1 / fev1) * 100
                    percent_predicted_fvc = round(measured_fvc / fvc * 100,1) if fvc != 0 else 0

                    col1, col2, col3, col4 = st.columns(4)  # Create four columns
                    
                    with col1:
                        st.metric(label="Predicted FEV1", value=f"{fev1:.2f} L")
                    with col2:
                        st.metric(label="Predicted FVC", value=f"{fvc:.2f} L")
                    with col3:
                        st.metric(label="Predicted FEV1/FVC", value=f"{fev1_fvc:.2f}")
                    with col4:
                        st.metric(label="% Predicted FVC", value=f"{percent_predicted_fvc:.1f}")

                    col5, col6, col7, col8 = st.columns(4)
                    
                    with col5:
                        st.metric(label="Measured FEV1", value=f"{measured_fev1:.2f} L")
                    with col6:
                        st.metric(label="Measured FVC", value=f"{measured_fvc:.2f} L")
                    with col7:
                        # Calculate FEV1/FVC ratio from measured values and display
                        measured_fev1_fvc = measured_fev1 / measured_fvc if measured_fvc != 0 else 0
                        st.metric(label="Measured FEV1/FVC", value=f"{measured_fev1_fvc:.2f}")
                    rv_percent_est = calculate_rv_est(percent_predicted_fvc, measured_fev1_fvc, age, gender)
                    # Calculate RV % Predicted Prevalence
                    RV150, RV175, RV200 = calculate_rv_predicted(rv_percent_est)
                    # Adding a row to display RV % est
                    col9, col10, col11, col12 = st.columns(4)
                    with col9:
                        st.metric(label="RV % Estimate", value=f"{rv_percent_est:.1f}")
                    with col10:
                        st.metric(label="RV >150% Probability", value=f"{RV150:.1f}%")
                    with col11:
                        st.metric(label="RV >175% Probability", value=f"{RV175:.1f}%")
                    with col12:
                        st.metric(label="RV >200% Probability", value=f"{RV200:.1f}%")

                    st.write("Final Result")
                    # Final Result based on the RV% Est threshold
                    if rv_percent_est >= rv_threshold:
                        st.success(f"Patient Can be Sent to Next Step 🟢")
                    else:
                        st.error(f"Patient is Fit, No Further Care Required 🔴")
        elif standard == 'ECSC':
            st.write("Work in Progress. This standard is not available yet.")
else:
    st.write("Please enter an email address to continue.")
