import pandas as pd
import numpy as np
import streamlit as st
import streamlit_authenticator as stauth
from sqlalchemy import create_engine, engine, text
import requests
import plotly.express as px
import altair as alt
from yaml.loader import SafeLoader
import yaml

# Credentials 
with open('capstone/frontend/authentication.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Authenticator variable
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# Login
name, authentication_status, username = authenticator.login('Login', 'main')

# Server url
server_url = "http://127.0.0.1:5000"

# Routes to login
if authentication_status:
    
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{name}* to your H&M KPI platform!')

    @st.cache_data
    def load_data(url):
        try:
            response_json = requests.get(url).json()
            data = pd.json_normalize(response_json, "result")
        except Exception as e:
            print(e)
        return data 

    st.subheader("Gilles de Trazegnies MCSBT")
    st.title("H&M KPI's Capstone Project")

    # ARTICLES DATABASE
    # /////////////////////////////////////

    st.subheader("Articles Database")

    # Loading the articles dataframe from my API
    articles_df = load_data(f"{server_url}/api/v1/articles")

    ## Genrating filters
    # ---------------------

    # Generating list of different colors
    colors_list = articles_df['colour_group_name'].unique()
    colors_list.sort()

    # Generating filter for the colors with multiselect
    colors_multiselect = st.sidebar.multiselect(
        label = "PRODUCT COLORS",
        options = colors_list,
        default = colors_list,
        key = "multiselect_colors"
    )    


    ## Filtering the dataset
    # -------------------------

    articles_df = articles_df[articles_df['colour_group_name'].isin(colors_multiselect)]

    ## Generating the KPIs
    # -------------------------

    num_of_articles = len(articles_df["article_id"])#.nunique()

    st.metric(
        label = "Number of total articles",
        value = num_of_articles,
        delta = num_of_articles,
    )

    # Counting the usage by color
    colors = articles_df.groupby('colour_group_name').count()
    colors = colors[['colour_group_code']]
    colors.rename(columns={'colour_group_code': 'count'}, inplace=True)

    # Counting the total number of articles in the men´s section
    men = articles_df[articles_df.section_name.str.contains("Men")]
    prod_men = men.groupby('section_name').count()
    prod_men = prod_men[['article_id']]
    prod_men.rename(columns={'article_id': 'count'}, inplace=True)
    
    # Counting the total number of articles in the women´s section
    women = articles_df[articles_df.section_name.str.contains("Women")]
    prod_women = women.groupby('section_name').count()
    prod_women = prod_women[['article_id']]
    prod_women.rename(columns={'article_id': 'count'}, inplace=True)

    # product percentages by color
    colors_per = articles_df.groupby('colour_group_name').count()
    colors_per = colors_per[['colour_group_code']]
    colors_per.rename(columns={'colour_group_code': 'count'}, inplace=True)
    colors_per['percentage'] = (colors_per['count'] / num_of_articles) * 100
    threshold = 2.0
    colors_per_filtered = colors_per.loc[colors_per['percentage'] >= threshold]

    # plotting figures
    st.caption("product count on different colors")
    st.bar_chart(colors['count'])
    
    figure_colors = px.pie(colors_per_filtered, values='percentage', names= colors_per_filtered.index, title='Colors Percentage (>= {}%)'.format(threshold))
    figure_colors.update_traces(textposition='inside', textinfo='percent+label')
    figure_colors.update_layout(showlegend=True)
    st.plotly_chart(figure_colors, use_container_width=True)

    st.caption("Men's products count")
    st.bar_chart(prod_men['count'])

    st.caption("Women's products count")
    st.bar_chart(prod_women['count'])

    # CUSTOMERS DATABASE
    # /////////////////////////////////////

    st.subheader("Customers Database")

    # Loading the customers dataframe from my API
    customers_df = load_data(f"{server_url}/api/v1/customers")

    ## Genrating filters
    # -------------------------

    # Generating list of different status
    status_list = customers_df['club_member_status'].unique()

    st.sidebar.write("FILTERS")

    # Create filter for status using multiselect
    status_filter = st.sidebar.multiselect(
        label = "CLUB MEMBER STATUS",
        options = status_list,
        default = status_list,
        key = "multiselect_status"
    )

    # Creating age filter using a slider
    age_filter = st.sidebar.slider(
        'Select a range of ages',
        0, 100, (20, 80))

    ## Apply filters to customer dataframe
    customers_df = customers_df[(customers_df['age']>=age_filter[0]) & (customers_df['age']<=age_filter[1])]
    customers_df = customers_df[customers_df['club_member_status'].isin(status_filter)]

    ## generating the KPIs
    # -------------------------

    num_of_customers = len(customers_df["customer_id"])#.nunique()
    avg_age = np.mean(customers_df["age"])
    num_status = customers_df["club_member_status"].nunique()

    kpi1, kpi2, kpi3 = st.columns(3)

    kpi1.metric(
        label = "Number of different customers",
        value = num_of_customers,
        delta = num_of_customers,
    )

    kpi2.metric(
        label = "Number of different member status",
        value = num_status,
        delta = num_status,
    )
            
    kpi3.metric(
        label = "Average age of customers",
        value = round(avg_age, 2),
        delta = -10 + avg_age,
    )

    st.caption("Customer age count")
    st.bar_chart(customers_df.groupby(["age"])["customer_id"].count())

    # Percentages of the distribution of club member status (active, pre-create, left club)
    club_member_status = customers_df.groupby('club_member_status').count()
    club_member_status = club_member_status[['customer_id']]
    club_member_status.rename(columns={'customer_id': 'count'}, inplace=True)
    club_member_status['percentage'] = (club_member_status['count'] / num_of_customers) * 100

    fashion_news = customers_df.groupby('fashion_news_frequency').mean()
    fashion_news = fashion_news[['age']]
    fashion_news.rename(columns={'age': 'average_customer_age'}, inplace=True)
    fashion_news['total_count'] = customers_df.groupby('fashion_news_frequency').count().age
    fashion_news['percentage'] = (fashion_news['total_count'] / num_of_customers) * 100

    cols = st.columns([1, 1])

    with cols[0]:
        fig_status = px.pie(club_member_status, values='percentage', names=club_member_status.index,
                    title='Club Member Status Percentages')
        st.plotly_chart(fig_status, use_container_width=True)

    with cols[1]:
        fig_news = px.pie(fashion_news, values='percentage', names=fashion_news.index,
                    title='Fashion News Frequency Percentages')
        st.plotly_chart(fig_news, use_container_width=True)

    
    # TRANSACTIONS DATABASE
    # /////////////////////////////////////

    st.subheader("Transactions Database")

    # Loading the transactions dataframe from my API
    transactions_df = load_data(f"{server_url}/api/v1/transactions")

    ## Generating filters
    # -------------------------

    # Generate sales channel id list
    sales_channel_list = transactions_df['sales_channel_id'].unique()
    sales_channel_list.sort()

    # Creating filter for channel id using multiselect
    sales_channel_filter = st.sidebar.multiselect(
        label = "SALES CHANNEL",
        options = sales_channel_list,
        default = sales_channel_list,
        key = "multiselect_sales_channel"
    )    

    # Create a filter for number of transactions
    num_transactions_filter = st.sidebar.slider(
        'Select the number of transactions',
        0, 1000, 500)

    ## Filtering the transaction dataset
     # ------------------------------------

    transactions_df = transactions_df.iloc[:num_transactions_filter]
    transactions_df = transactions_df[transactions_df['sales_channel_id'].isin(sales_channel_filter)]

    ## Generating KPIs
     # -------------------------

    kpi5, kpi6 = st.columns(2)

    total_revenue = sum(transactions_df['price'])
    average_transaction_value = total_revenue / len(transactions_df['price'])

    kpi5.metric(
        label = "Total revenue in sales",
        value = total_revenue,
        delta = total_revenue,
    )

    kpi6.metric(
        label = "Average transaction value",
        value = average_transaction_value,
        delta = average_transaction_value,
    )

    # Sales percentage that took place online vs on the physical store
    total_sales_channel_1 = len(transactions_df[transactions_df['sales_channel_id'] == 1])
    total_sales_channel_2 = len(transactions_df[transactions_df['sales_channel_id'] == 2])

    percentage_channel_1 = (total_sales_channel_1 / len(transactions_df['sales_channel_id'])) * 100
    percentage_channel_2 = (total_sales_channel_2 / len(transactions_df['sales_channel_id'])) * 100

    sales_channel_df = pd.DataFrame()
    sales_channel_df['channel'] = sales_channel_list
    sales_channel_df['percentage'] = [percentage_channel_1, percentage_channel_2]

    fig_channel = px.pie(sales_channel_df, values='percentage', names='channel',
                title='Sales Channel Percentage')
    st.plotly_chart(fig_channel, use_container_width=True)

   