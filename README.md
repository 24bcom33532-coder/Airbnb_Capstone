# Airbnb_Capstone
Predictive modeling and exploratory data analysis for Airbnb listing prices.
# Airbnb Revenue and Customer Experience Analytics

## 1. Project Overview

This project focuses on analysing Airbnb property listings to understand revenue patterns, occupancy trends, pricing strategies, and customer experience.

The project uses data analytics and visualisation techniques to identify useful business insights that can help property hosts and managers make informed decisions.

## 2. Objectives

- Analyse Airbnb listing prices across different room types and cities.
- Understand estimated revenue and occupancy patterns.
- Examine the relationship between pricing, occupancy, and revenue.
- Analyse customer ratings and review activity.
- Identify trends and provide data-driven business recommendations.

## 3. Dataset

The dataset was obtained from Kaggle:

**Dataset:** Airbnb Property Rental Price

**Source:** https://www.kaggle.com/datasets/datavidia/airbnb-property-rental-price

**License:** MIT License

The dataset contains Airbnb listing information, including property details, nightly prices, guest ratings, reviews, estimated annual revenue, and estimated occupancy.

The original dataset contained 261,895 records and 55 columns. After data cleaning, the dataset contained 261,870 records and 61 columns.

## 4. Tools and Technologies Used

- Python
- Google Colab
- Pandas and NumPy
- Matplotlib and Seaborn
- Plotly
- Streamlit
- GitHub

## 5. Project Workflow

1. Dataset collection from Kaggle.
2. Data cleaning and preprocessing.
3. Exploratory Data Analysis (EDA).
4. Python-based data analysis and visualisation.
5. Development of an interactive Streamlit dashboard.
6. Interpretation of insights and preparation of business recommendations.

## 6. Dashboard Features

The interactive dashboard provides:

- Key performance indicators (KPIs).
- Room-type-wise revenue and occupancy comparisons.
- Nightly price and estimated revenue analysis.
- City-wise listing analysis.
- Guest rating and review analysis.
- Interactive filters for exploring the dataset.
- Data tables for detailed listing information.

## 7. How to Run the Project

Make sure Python is installed on your system.

Install the required libraries:

pip install streamlit pandas plotly numpy

Place the cleaned dataset and `app.py` in the same project folder.

Run the following command in the terminal:

python -m streamlit run app.py

The dashboard will open in your web browser.

## 8. Important Note

The revenue and occupancy figures used in this project are dataset-provided estimates. They should not be interpreted as verified actual revenue, profit, or occupancy figures.

## 9. Conclusion

This project demonstrates how data analytics can be applied to the hospitality industry to understand pricing, revenue, occupancy, and customer experience. The interactive dashboard presents key findings in an accessible format and supports data-driven business decision-making.
