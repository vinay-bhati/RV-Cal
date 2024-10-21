import streamlit as st
import pandas as pd
import numpy as np
import math
from validate_email import validate_email
import boto3
from io import StringIO
from datetime import date, datetime

# Load AWS configuration from secrets
access_key = st.secrets["aws"]["access_key"]
secret_key = st.secrets["aws"]["secret_key"]
bucket_name = st.secrets["aws"]["bucket_name"]
s3_filename = st.secrets["aws"]["s3_filename"]

# Initialize the S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

def append_to_s3(email, rv_threshold, standard, has_fvc_pred, gender, age, height, measured_fev1, measured_fvc, fvc_percent_predicted, predicted_fev1, predicted_fvc, predicted_fev1_fvc, rv_percent_est, rv150_prob, rv175_prob, rv200_prob):
    # Prepare the CSV row as a string, note the newline at the start
    date_today = date.today().isoformat()
    date_time = datetime.now().isoformat()
    data_row = f"\n{email}|{rv_threshold}|{standard}|{has_fvc_pred}|{gender}|{age}|{height}|{measured_fev1}|{measured_fvc}|{fvc_percent_predicted}|{round(predicted_fev1, 2) if has_fvc_pred == 'No' else ''}|{round(predicted_fvc, 2) if has_fvc_pred == 'No' else ''}|{round(predicted_fev1_fvc, 2) if has_fvc_pred == 'No' else ''}|{rv_percent_est}|{round(rv150_prob,2)}|{round(rv175_prob,2)}|{round(rv200_prob,2)}|{date_today}|{date_time}"

    # Bucket and file details
    bucket_name = st.secrets["aws"]["bucket_name"]
    s3_filename = st.secrets["aws"]["s3_filename"]

    # Initialize S3 client
    s3_client = boto3.client('s3', aws_access_key_id=st.secrets["aws"]["access_key"], aws_secret_access_key=st.secrets["aws"]["secret_key"])

    # Download the existing CSV from S3
    response = s3_client.get_object(Bucket=bucket_name, Key=s3_filename)
    existing_data = response['Body'].read().decode('utf-8')

    # Append the new data
    updated_data = existing_data + data_row

    # Upload the updated data back to S3
    s3_client.put_object(Bucket=bucket_name, Key=s3_filename, Body=updated_data.encode('utf-8'))

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
        #df_rv = "Male RV.csv"
    else:
        df_fev1 = pd.read_csv("Female FEV1.csv")
        df_fvc = pd.read_csv("Female FCV.csv")
        df_fev1_fvc = pd.read_csv("Female FEV1 FVC.csv")
        #df_rv = "Female RV.csv"
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
    # Load constants from secrets
    consts = st.secrets["rv_est_constants"]
    
    # Converting gender to numeric value: 1 for Male, 0 for Female
    gender_numeric = 1 if gender == 'Male' else 0
    
    # Use constants from secrets.toml for calculations
    rv_est = round(
        (percent_predicted_fvc * consts["fvc_multiplier"] +
         round(measured_fev1_fvc, 3) * consts["fev1_fvc_multiplier"] +
         np.sqrt(percent_predicted_fvc) * consts["fvc_sqrt_multiplier"] +
         age * consts["age_multiplier"] +
         gender_numeric * consts["gender_multiplier"] +
         consts["constant"]), 1)
    
    return rv_est

def calculate_rv_predicted(rv_percent_est):
    # Load constants from secrets
    preds = st.secrets["rv_pred_constants"]
    
    # Using the logistic regression model to predict probabilities
    rv150 = round((1 / (1 + math.exp(-1 * (preds["rv150_coef"] + preds["rv150_intercept"] * rv_percent_est)))), 3) * 100
    rv175 = round((1 / (1 + math.exp(-1 * (preds["rv175_coef"] + preds["rv175_intercept"] * rv_percent_est)))), 3) * 100
    rv200 = round((1 / (1 + math.exp(-1 * (preds["rv200_coef"] + preds["rv200_intercept"] * rv_percent_est)))), 3) * 100
    
    return rv150, rv175, rv200

def calculate_ecsc_fvc(age, height, fev1, fvc, gender, race):
    """Calculate ECSC based Predicted FVC based on the formula."""
    if gender == 1 and race == 1:
        return round((0.00064 * age - 0.000269 * (age ** 2) + 0.00018642 * (height ** 2) - 0.1933), 2)
    elif gender == 0 and race == 1:
        return round((0.0187 * age - 0.000382 * (age ** 2) + 0.00014815 * (height ** 2) - 0.356), 2)
    elif gender == 1 and race == 2:
        return round((-0.01821 * age + 0.00016643 * (height ** 2) - 0.1517), 2)
    elif gender == 0 and race == 2:
        return round((0.00536 * age - 0.000265 * (age ** 2) + 0.00013606 * (height ** 2) - 0.3039), 2)
    return "Insufficient data for prediction"

def calculate_ecsc_metrics(age, height, measured_fev1, predicted_fvc, measured_fvc):
    """Calculate additional respiratory metrics based on user input and predicted FVC."""
    if measured_fvc and predicted_fvc:
        fvc_percent_predicted = round((measured_fvc / predicted_fvc) * 100, 3)
    else:
        fvc_percent_predicted = None

    # Assuming FEV1/FVC ratio is a straightforward division
    if measured_fev1 and measured_fvc:
        fev1_fvc_ratio = round((measured_fev1 / measured_fvc) * 100, 3)
    else:
        fev1_fvc_ratio = None

    # Calculate RV % est based on the provided formula
    if age is not None and measured_fev1 and fvc_percent_predicted and fev1_fvc_ratio:
        rv_percent_est = round((fvc_percent_predicted * 3.46 - fev1_fvc_ratio * 179.8 -
                                np.sqrt(fvc_percent_predicted) * 79.53 - age * 0.98 - height * 10.88 + 737.06), 1)
    else:
        rv_percent_est = None

    # Calculate probabilities for RV150, RV175, RV200
    if rv_percent_est is not None:
        rv150 = round((1 / (1 + np.exp(-1 * (-9.218401 + 0.0572793 * rv_percent_est)))), 3) * 100
        rv175 = round((1 / (1 + np.exp(-1 * (-9.995177 + 0.0551463 * rv_percent_est)))), 3) * 100
        rv200 = round((1 / (1 + np.exp(-1 * (-11.32753 + 0.0561363 * rv_percent_est)))), 3) * 100
    else:
        rv150, rv175, rv200 = None, None, None

    return fvc_percent_predicted, fev1_fvc_ratio, rv_percent_est, rv150, rv175, rv200

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
        
                if gender:
                    # Create layout with columns for age, measured FEV1, measured FVC, and FVC % Predicted
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        age = st.number_input("Enter Age (Years):", min_value=3, max_value=95, step=1, key='age_yes')
                    with col2:
                        measured_fev1 = st.number_input("Enter Measured FEV1 (XX.XX):",min_value=0.0,format="%.2f", step=0.01, key='fev1_yes')
                    with col3:
                        measured_fvc = st.number_input("Enter Measured FVC (XX.XX):", min_value=0.0, format="%.2f", step=0.01, key='fvc_yes')
                    with col4:
                        fvc_percent_predicted = st.number_input("Enter FVC % Predicted:", min_value=0.0,format="%.1f", step=0.1, key='fvc_percent_pred')
                        
                    # Store the button press result in a variable
                    evaluate_pressed = st.button('Evaluate')
                    
                    if evaluate_pressed and age and measured_fev1 and measured_fvc and fvc_percent_predicted:
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
                        # Append the data to the CSV file in S3
                        append_to_s3(email, rv_threshold, standard, has_fvc_pred, gender, age, None, measured_fev1, measured_fvc, fvc_percent_predicted, None, None, None, rv_percent_est, RV150, RV175, RV200)
                    elif evaluate_pressed:
                        st.error("Please fill in all required fields before evaluating.")
                        
            elif has_fvc_pred == 'No':
                gender = st.radio("Select Gender:", ('Male', 'Female'),horizontal=True,index=None)

                if gender:
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

                     # Store the button press result in a variable
                    calculate_pressed = st.button('Calculate')
                    
                    # Calculate button can be placed below the inputs or in a new line
                    if calculate_pressed and age and height and measured_fev1:
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
                        # Append the data to the CSV file in S3
                        append_to_s3(email, rv_threshold, standard, has_fvc_pred, gender, age, height, measured_fev1, measured_fvc, percent_predicted_fvc, fev1, fvc, fev1_fvc, rv_percent_est, RV150, RV175, RV200)

                    elif calculate_pressed:
                        st.error("Please fill in all required fields before calculating.")
                        
        elif standard == 'ECSC':
            gender = st.radio("Select Sex:", (1, 0), format_func=lambda x: 'Male' if x == 1 else 'Female',index=None)
            
            if gender is not None:  # Ensures that race is only shown if gender is selected
                race = st.radio("Select Race:", (1, 2), format_func=lambda x: 'White' if x == 1 else 'Black',index=None)
                
                if race is not None:  # Ensures that the remaining inputs are only shown if race is selected
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        age = st.number_input("Age:", min_value=3, max_value=95, step=1)
                    with col2:
                        height = st.number_input("Height (in cm):", min_value=100, max_value=250, step=1)
                    with col3:
                        measured_fev1 = st.number_input("Enter Measured FEV1 (XX.XX):", min_value=0.0, format="%.2f", step=0.01)
                    with col4:
                        measured_fvc = st.number_input("Enter Measured FVC (XX.XX):", min_value=0.0, format="%.2f", step=0.01)

                    #Store the button press result in a variable
                    calculate_ECSC = st.button('Calculate ECSC')

                    if calculate_ECSC and age and height and measured_fev1 and measured_fvc:
                        pred_fvc = calculate_ecsc_fvc(age, height, measured_fev1, measured_fvc, gender, race)
                        fvc_percent_predicted, fev1_fvc_ratio, rv_percent_est, rv150, rv175, rv200 = calculate_ecsc_metrics(age, height, measured_fev1, pred_fvc, measured_fvc)

                        col5, col6, col7, col8,col9, col10, col11 = st.columns(7)
                        # Display the calculated values
                        
                        st.metric(label="Predicted FVC:", value=f"{pred_fvc}")
                        #st.write(f"Predicted FVC: {pred_fvc} L")
                        
                        st.metric(label="FVC % Predicted:", value=f"{fvc_percent_predicted}")
                        #st.write(f"FVC % Predicted: {fvc_percent_predicted}%")

                        st.metric(label="FEV1/FVC Ratio:", value=f"{fev1_fvc_ratio}")
                        #st.write(f"FEV1/FVC Ratio: {fev1_fvc_ratio}%")

                        st.metric(label="RV % Estimated:", value=f"{rv_percent_est}")
                        #st.write(f"RV % Estimated: {rv_percent_est}")

                        st.metric(label="RV >150% Probability", value=f"{rv150}%")
                        #st.write(f"RV >150% Probability: {rv150}%")

                        st.metric(label="RV >175% Probability", value=f"{rv175}%")
                        #st.write(f"RV >175% Probability: {rv175}%")

                        st.metric(label="RV >200% Probability", value=f"{rv200}%")
                        #st.write(f"RV >200% Probability: {rv200}%")

                    
                    elif calculate_ECSC:
                        st.error("Please fill in all required fields before calculating.")
else:
    st.write("Please enter an email address to continue.")
