import pickle
import pandas as pd
import numpy as np

nmf_model = pickle.load(open('my_nmf_model.sav', "rb"))
nmf_df = pickle.load(open('nmf_dataframe.sav', 'rb'))
Q = pickle.load(open('Q_df.sav', 'rb'))
products = nmf_df.columns

def get_asin_name(asin):
    vote5_df = pd.read_csv('/Users/Varvara/spiced_working_files/final_project/Recommender/vote_5.csv', index_col=0)
    product_name=vote5_df[vote5_df.index==(asin)]['title'].values[0]
    return product_name

def recommend_nmf(user_input, name='Recommendation', model=nmf_model):    
    """Filters and recommends the top k movies 
    for any given input query based 
    on a trained NMF model.
    Parameters
    ----------
    query : dict
        A dictionary of movies already seen. 
        Takes the form {"product_A": 3, "product_B": 3} etc
    nmf_model : pickle
        pickle nmf_model read from disk
    k : int, optional
        no. of top products to recommend, by default 10
    """
    # 1. candiate generation
    
    # construct a user vector
    
    user_dataframe = pd.DataFrame.from_records(data=[user_input], index=[name],columns=nmf_df.columns)
    user_dataframe_copy = user_dataframe.copy()
    
    user_R = user_dataframe.fillna(0)
    user_R
   
    # 2. scoring
    
    # calculate the score with the NMF nmf_model
    user_P = nmf_model.transform(user_R)
    user_R = np.dot(user_P, Q)
    rec_df = pd.DataFrame(user_R, index=[name], columns=user_dataframe.columns)
    
    # 3. ranking
    
    # define the products already rated by the user
    df4=rec_df.T.sort_values(by=name, ascending=False)
    sorted_recommendations = df4.index.sort_values(ascending=False)
    sorted_recommendations_df = sorted_recommendations.to_frame()
    sorted_recommendations_df = pd.DataFrame(sorted_recommendations_df)
    sorted_recommendations_df_list = list(sorted_recommendations_df.index)
    recom_short = sorted_recommendations_df_list[:10]
    print(recom_short)
    
    df2=user_dataframe_copy.T
    rated_asin=df2[df2.Recommendation.isna()== False]
    sorted_new_user_df = rated_asin.index.sort_values(ascending=False)
    sorted_new_user_df = sorted_new_user_df.to_frame()
    sorted_new_user_df= pd.DataFrame(sorted_new_user_df)
    sorted_new_user_df_list = list(sorted_new_user_df.index)
    print(sorted_new_user_df_list)
    
    final_rec = [asin for asin in recom_short if asin not in sorted_new_user_df_list]
    print(final_rec)
    
    
    # return the top-k highst rated movie ids or titles
    recommendations = []
    for asin in final_rec:
        product_title = get_asin_name(asin)
        recommendations.append(product_title)
        #recommendations_df = pd.DataFrame(recommendations)
    
    output = recommendations
    print(output)

    return output