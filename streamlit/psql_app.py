import streamlit as st
import psycopg2
import numpy as np
import pickle
from nmf_recommender import recommend_nmf, get_asin_name, products
import config as cf
from sqlalchemy import create_engine
import time
import logging
import pandas as pd
from sqlalchemy import text
import google_lang
from google_lang.google_trans_new1 import google_translator
from langdetect import detect
import wordcloud
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import seaborn as sns
import matplotlib.pyplot as plt
from gensim.models import Phrases
from gensim import corpora
from gensim import models
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk import pos_tag
import nltk
nltk.download('omw-1.4')
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from itertools import chain
from tqdm import tqdm
from tqdm.notebook import tqdm
tqdm.pandas(desc="progress_map")
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from textblob import TextBlob
import plotly.express as px


st.title("Christmas gift recommender")

# Creating pages
page = st.sidebar.selectbox('Select page:', ('Visualization', 'NLP on reviews', 'Postgres DB', 'Toy Recommender'))
if page == 'Visualization':
    st.header("**Amazon data insights**")
    page_icon = ('/Users/Varvara/Downloads/edit.png')
    st.sidebar.markdown('The "Toys and Games" data is scraped from Amazon website using Scrapy API.')
    st.sidebar.markdown('There are around 400 bestsellers in more then 20 categories.')

    st.sidebar.markdown('---')
    st.sidebar.write('Developed by Varvara Fruehmann')
    # import dataset
    df = pd.read_csv('amazon_items.csv')
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Age group distribution**")
        static_figure, ax_subplots = plt.subplots()
        ax_subplots = df.groupby(['age_range']).size().sort_values(ascending=False).plot.bar(figsize=(14, 7))
        ax_subplots.bar_label(ax_subplots.containers[0])
        st.pyplot(static_figure)
        st.write("Most of the Bestsellers are for the kids in the age range of 6-12 years('School age') and 3-5 years ('Toddlers').")


    with col2:
        st.write('**Price range distribution**')
        fig, ax_subplots = plt.subplots()
        ax_subplots = df.groupby(['price_range']).size().plot.bar(figsize=(14, 7))
        ax_subplots.bar_label(ax_subplots.containers[0])
        st.pyplot(fig)
        st.write("Most options are in the 'cheap' segment up to 15 EUR and 'middle_priced' up to 40 EUR.")

    with col3:
        st.write('**Category distribution**')
        static_figure, ax_subplots = plt.subplots()
        ax_subplots = df.groupby(['category']).size().sort_values(ascending=False).plot.bar(figsize=(14, 7))
        ax_subplots.bar_label(ax_subplots.containers[0])
        st.pyplot(static_figure)
        st.write("The most popular categories are Building Sets, Board Games, Games & Accessories, Learning & Education.")


    st.write("**Correlation between price and number of reviews**")
    fig = px.scatter(
        x=df["price"],
        y=df["reviews_num"],
    )
    fig.update_layout(
        xaxis_title="price",
        yaxis_title="reviews_num"
    )
    st.write(fig)

    st.write("**Correlation between rating and price**")

    fig = px.scatter(
        x=df["rating"],
        y=df["price"]
    )
    fig.update_layout(
        xaxis_title="rating",
        yaxis_title="price"
    )
    st.write(fig)


elif page == 'NLP on reviews':
    st.session_state.url = 'https://img1.picmix.com/output/stamp/normal/0/5/8/2/1112850_c341b.gif'
    cf.background(st.session_state.url)

    st.header("Auto translation and Topic modelling")
    st.write("**1. Auto-translate using Google API**")
    # import dataset
    df = pd.read_csv('/Users/Varvara/spiced_working_files/final_project/NLP/langdetect/reviews_full_text.csv')
    df['reviews'] = df['text'] + df['title']
    st.write("**Original comment**")
    st.write(df['reviews'][0])

    def detect_and_translate(text, target_lang='en'):
        result_lang = detect(text)
        if result_lang == target_lang:
            return text
        else:
            translator = google_translator()
            translate_text = translator.translate(text, lang_src=result_lang, lang_tgt=target_lang)
            return translate_text

    text = df['reviews'][0]
    st.write("**Translated comment**")
    text2 = detect_and_translate(text)
    st.write(detect_and_translate(text))


    st.write("**2. WordCloud of this translated comment**")
    wordcloud = WordCloud().generate(text2)
    # Display the generated image:
    figure, ax_subplots = plt.subplots(figsize = (12, 8))
    ax_subplots.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(figure)

    st.write("**3. LDA**")
    df1 = pd.read_csv('/Users/Varvara/spiced_working_files/final_project/NLP/Amazon_reviews_processed.csv')
    # df1['reviews'] = pd.Series(df1['reviews'], dtype="string")
    #df1['sentences'] = df1.reviews.apply(lambda x: x.progress_map(sent_tokenize))
    df1['sentences'] = df1.reviews.progress_map(sent_tokenize)
    df1['tokens_sentences'] = df1['sentences'].progress_map(
        lambda sentences: [word_tokenize(sentence) for sentence in sentences])
    df1['POS_tokens'] = df1['tokens_sentences'].progress_map(
        lambda tokens_sentences: [pos_tag(tokens) for tokens in tokens_sentences])


    def get_wordnet_pos(treebank_tag):
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return ''

    lemmatizer = WordNetLemmatizer()
    df1['tokens_sentences_lemmatized'] = df1['POS_tokens'].progress_map(
        lambda list_tokens_POS: [
            [
                lemmatizer.lemmatize(el[0], get_wordnet_pos(el[1]))
                if get_wordnet_pos(el[1]) != '' else el[0] for el in tokens_POS
            ]
            for tokens_POS in list_tokens_POS
        ]
    )
    stopwords_verbs = ['say', 'get', 'go', 'know', 'may', 'need', 'like', 'make', 'see', 'want', 'come', 'take', 'use',
                       'would', 'can']
    stopwords_other = ['one', 'mr', 'bbc', 'image', 'getty', 'de', 'en', 'caption', 'also', 'copyright', 'something']
    my_stopwords = stopwords.words('english') + stopwords_verbs + stopwords_other
    df1['tokens'] = df1['tokens_sentences_lemmatized'].map(lambda sentences: list(chain.from_iterable(sentences)))
    df1['tokens'] = df1['tokens'].map(lambda tokens: [token.lower() for token in tokens if token.isalpha()
                                                      and token.lower() not in my_stopwords and len(token) > 1])


    tokens = df1['tokens'].tolist()
    bigram_model = Phrases(tokens)
    trigram_model = Phrases(bigram_model[tokens], min_count=1)
    tokens = list(trigram_model[bigram_model[tokens]])
    dictionary_LDA = corpora.Dictionary(tokens)
    dictionary_LDA.filter_extremes(no_below=3)
    corpus = [dictionary_LDA.doc2bow(tok) for tok in tokens]
    np.random.seed(123456)
    num_topics = 20
    lda_model = models.LdaModel(corpus, num_topics=num_topics, \
                                id2word=dictionary_LDA, \
                                passes=4, alpha=[0.01] * num_topics, \
                                eta=[0.01] * len(dictionary_LDA.keys()))
    for i, topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=20):
        st.write(str(i) + ": " + topic)
    test = 'Great gift. Not much to say other than its lego quality'
    st.write("**Test on the random review**")
    st.write(test)
    #st.write(lda_model[corpus[0]])
    tokens = word_tokenize(test)
    topics = lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=20)
    st.write(pd.DataFrame([(el[0], round(el[1], 2), topics[el[0]][1]) for el in lda_model[dictionary_LDA.doc2bow(tokens)]],
                 columns=['topic #', 'weight', 'words in topic']))


elif page == 'Postgres DB':
    st.header("**filtered on Amazon Bestsellers**")
    st.subheader("**using Postgres Database**")
    st.session_state.url = 'https://cdn.dribbble.com/users/1078019/screenshots/14815674/media/c79de6558325fe1651b90dee663d2db5.mp4'
    cf.background(st.session_state.url)

    # Initialize connection.
    # Uses st.experimental_singleton to only run once.
    @st.experimental_singleton
    def init_connection():
        return psycopg2.connect(**st.secrets["postgres"])


    conn = init_connection()


    # Perform query.
    # Uses st.experimental_memo to only rerun when the query changes or after 10 min.
    @st.experimental_memo(ttl=600)
    def run_query(query):
        with conn.cursor() as cur:
            cur.execute(query)
            # colnames = [desc[0] for desc in cur.description]
            # return colnames, cur.fetchall()
            return cur.fetchall()


    # names, rows = run_query(
    #     "SELECT name,price,age_range, category, price_range, link FROM amazon_items  ORDER BY 1  ;")
    col_names = ["name", "price", "age_range", "category", 'brand', "price_range", "link"]
    rows = run_query(
        "SELECT name,price,age_range, category, brand, price_range, link FROM amazon_items  ORDER BY 1 LIMIT 400 ;")

    # save as DataFrame
    # df = pd.DataFrame(rows, columns=names)

    df = pd.DataFrame(rows, columns=col_names)
    st.write(df.style.format({'price': '{:.2f}'}))

    age_range = ["School age", "Toddlers", "Teenagers", "Baby"]
    age_input = st.selectbox('**Select age range**', age_range)
    dict_age = {"School age": "'School age'", "Toddlers": "'Toddlers'", "Teenagers": "'Teenagers'", "Baby": "'Baby'"}
    query = f"SELECT name, price, link FROM amazon_items WHERE age_range = {dict_age[age_input]} ORDER BY 1 LIMIT 5;"
    age_filter = run_query(query)
    # Print results.
    for item in age_filter:
        st.write(f"**{item[0]}, **{item[1]} EUR**, **check the product:** {item[2]}**")
        # for value in results:
        #     st.markdown("- " + value)
        # list_age = st.write(f"{item[0]}, **{item[1]} EUR**, **check the product:** {item[2]}")

    price_range = ["cheap", "middle-priced", "expensive"]
    price_input = st.selectbox('**Select price range**', price_range)
    dict_price = {"cheap": "'cheap'", "middle-priced": "'middle-priced'", "expensive": "'expensive'"}
    query_1 = f"SELECT name, age, price, link FROM amazon_items WHERE price_range = {dict_price[price_input]} LIMIT 5;"
    price_filter = run_query(query_1)
    # Print results.
    for item in price_filter:
        st.write(f"**{item[0]},**Kid's age: {item[1]} years**, **{item[2]} EUR**, **check the product:** {item[3]}**")

    #col_names = ["name", "category", "age", "price", "link"]
    #category_input = st.multiselect("Filter by category", df['category'].unique())

    category = ['Boomboxes & MP3-Players', "Kids' Art Clay & Dough",
                         'Play Figure Playsets', 'Amazon devices', 'Games & Accessories',
                         'Building Sets', 'Arts & Crafts', 'Electronic Toys', '3-D Puzzles',
                         'Learning & Education', 'Toy Advent Calendars', 'Card games',
                         'Board Games', 'Playsets', "Kids' School Water Bottles",
                         'Dress-Up Accessories', 'Sports Toys & Outdoor',
                         'Jewellery Accessories', 'Building & Construction Toys',
                         'Jigsaw Accessories', 'Single Cards', 'Card Games',
                         'Magic Kits & Accessories', 'Jigsaw Puzzles',
                         'Baby & Toddler Toys',  'Sound Toys',
                         'Kitchen & Food Toys', 'Dolls', 'Stickers', 'playsets',
                         'Trains & Railed Vehicles', 'Lunch Boxes', 'Early development',
                         'Dice Games', 'Shops & Accessories', 'Bath Toys',
                         'Early Development ', 'Remote & App Controlled Vehicles',
                         'Jigsaws & Puzzles ']
    #df_categories = df.loc[df["category"] == category]
    category_input = st.selectbox('**Select category**', df['category'].unique())
    cat_dict = {"Boomboxes & MP3-Players": "'Boomboxes & MP3-Players'", "Kids' Art Clay & Dough": "'Kids' Art Clay & Dough'",
                "Play Figure Playsets": "'Play Figure Playsets'",
                "Amazon devices": "'Amazon devices'", "Games & Accessories": "'Games & Accessories'",
                "Building Sets": "'Building Sets'", "Arts & Crafts": "'Arts & Crafts'",
                "Electronic Toys": "'Electronic Toys'", "3-D Puzzles": "'3-D Puzzles'",
                "Learning & Education": "'Learning & Education'", "Toy Advent Calendars": "'Toy Advent Calendars'",
                "Card games": "'Card games'", "Board Games": "'Board Games'",
                "Dress-Up Accessories": "'Dress-Up Accessories'", "Sports Toys & Outdoor": "'Sports Toys & Outdoor'",
                "Building & Construction Toys": "'Building & Construction Toys'", "Jewellery Accessories": "'Jewellery Accessories'",
                "Sound Toys": "'Sound Toys'", "Remote & App Controlled Vehicles": "'Remote & App Controlled Vehicles'",
                "Dolls": "'Dolls'", "Trains & Railed Vehicles": "'Trains & Railed Vehicles'",
                "Jigsaws & Puzzles": "'Jigsaws & Puzzles'"}
    query_2 = f"SELECT name,category, age, price, link FROM amazon_items WHERE category = {cat_dict[category_input]} LIMIT 5;"
    cat_filter = run_query(query_2)
    # Print results
    for item in cat_filter:
        st.write(f"**{item[0]}, {item[1]},**Kid's age: {item[2]} years**, **{item[3]} EUR**, **check the product:** {item[4]}**")


    brand = ['PlayDoh', 'LEGO', 'Ravensburger', 'Barbie', 'FisherPrice', 'GraviTrax', 'Hasbro', 'Mattel', 'Paw Patrol', 'Hot Wheels']
    brand_input = st.selectbox('**Select brand**', df['brand'].unique())
    brand_dict = {"PlayDoh": "'PlayDoh'",
                "LEGO": "'LEGO'",
                "Ravensburger": "'Ravensburger'",
                "Barbie": "'Barbie'", "FisherPrice": "'FisherPrice'",
                "GraviTrax": "'GraviTrax'", "Hasbro": "'Hasbro'",
                "Mattel": "'Mattel'", "Paw Patrol": "'Paw Patrol'",
                "Hot Wheels": "'Hot Wheels'"}
    query_3 = f"SELECT name,brand, age, price, link FROM amazon_items WHERE brand = {brand_dict[brand_input]} LIMIT 5;"
    brand_filter = run_query(query_3)
    # Print results
    for item in brand_filter:
        st.write(
            f"**{item[0]}, {item[1]},**Kid's age: {item[2]} years**, **{item[3]} EUR**, **check the product:** {item[4]}**")

elif page == 'Toy Recommender':
    st.header("based on Amazon medium dataset")
    st.session_state.url = 'https://cdn.dribbble.com/users/1003944/screenshots/14810411/media/9dfef999d29e966952a888444e9b36f9.gif'
    cf.background(st.session_state.url)


    @st.cache(allow_output_mutation=True)
    def user_input():
        return {}


    st.subheader('Get toys recommendations:')
    nmf_input = user_input()
    with st.form(key='nmf_recommender'):
        for i in range(1, 6):
            k = st.selectbox('Select product', products, key=i)
            v = st.slider(label='rating', min_value=1, max_value=5, key=i + 5)
            nmf_input[k] = v
        submitted = st.form_submit_button('Get recommendations')

    if submitted:
        # if k and v:

        # st.write(nmf_input)
        results = recommend_nmf(nmf_input)
        # st.write(results)
        for product in results:
            st.markdown("- " + product)
