# LMSYS Chatbot Arena - Exploratory Data Analysis

This project performs a deep-dive Exploratory Data Analysis (EDA) on the [LMSYS Chatbot Arena dataset](https://www.kaggle.com/competitions/lmsys-chatbot-arena). The dataset consists of 57k+ rows of pairwise comparisons where humans rated which of two Large Language Models (LLMs) gave a better response.

## Analysis Goals

*   **Winner Distribution:** Visualize the frequency of wins for Model A, Model B, and Ties.
*   **Response Length Analysis:** Analyze the relationship between response length and winning probability.
*   **Model Performance:** Identify which models are the most frequent "top performers" and calculate win rates.
*   **Language Detection:** Detect and visualize the language distribution within the dataset.

## Project Structure

```text
project/
│
├── lmsys-chatbot-arena/       
│   ├── train.csv              
│   ├── test.csv              
│   └── sample_submission.csv 
│
├── eda.ipynb                 
├── lecture1.ipynb            
├── .gitignore               
└── README.md                