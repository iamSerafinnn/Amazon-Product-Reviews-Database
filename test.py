
import ssl, certifi
import pandas as pd
import Amazon_Reviews_2023

#Authenticating this python file to access the amazon_reviews dataset from HuggingFace.co and
#give it a valid HTTPS request for authentication
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

#This are the URLs of the amazon reviews dataset
url = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw_meta_Electronics/full-00000-of-00010.parquet"

#Extracting and reading the informations in the dataset into a dataframe
df = pd.read_parquet(url, engine="pyarrow")


# print("Shape:", df.shape)
# print("Column names:", df.columns)
# print("Data types:", df.dtypes)
# print("Memory usage:")
# print(df.memory_usage())
print("__________________________________\n\n")

column = df['features']
# for i in range(0,3):
#     print(type(column[i]))
#     print(column[i])
