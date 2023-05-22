import mpld3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

#add title
st.title("Christmas gift recommender")

#add text
st.write("Demo app to help you to choose **a nice gift for your child**")

#import dataset
df=pd.read_csv('amazon_items.csv')



#add header
st.header("Amazon best sellers")

#add interactive elements
st.sidebar.write('Which categories are available?')
category=st.sidebar.selectbox("Filter by category", df['category'].unique())

df_categories= df.loc[df["category"]==category]

#PLOTS

# st.write("Age group distribution")
# используем встроенную возможность делать график с анимацией
ax = df.groupby(['age_range']).size().sort_values(ascending=False)
st.bar_chart(ax)


# используем статичную картинку
static_figure, ax_subplots = plt.subplots()
ax_subplots = df.groupby(['age_range']).size().sort_values(ascending=False).plot.bar(figsize=(14,7))
ax_subplots.bar_label(ax_subplots.containers[0])

st.pyplot(static_figure)




animated_figure = plt.figure()

ax_animate = df.groupby(['age_range']).size().sort_values(ascending=False)

plt.plot(ax_animate)

# интерактивность pip install mpld3
fig_animate_html = mpld3.fig_to_html(animated_figure)
components.html(fig_animate_html, height=600)
