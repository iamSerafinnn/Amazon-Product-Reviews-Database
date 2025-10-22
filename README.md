# Amazon Electronics Retrieval Framework

## 📂 Datasets

### Original Dataset
We are using the **Amazon Electronics dataset (2023)** from Hugging Face:  
[raw_meta_Electronics/full-00000-of-00010.parquet](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/blob/main/raw_meta_Electronics/full-00000-of-00010.parquet)

### Cleaned Dataset
The dataset was cleaned by:
- Removing rows with no price, empty features, or empty description  
- Removing rows with no main category  
- Dropping the last three null columns  

The cleaned dataset is available here:  
[Cleaned Amazon Electronics Dataset](https://drive.google.com/file/d/15sY1xVYFIWQgI9gmd1HVHm9DU3wsrv9b/view?usp=drive_link)

---

## ⚙️ Running the Dataset Initialization

1. **Start PostgreSQL services**
```bash
brew services start postgresql
```
2. **Run the SQL initialization script**
```bash
psql -U $(whoami) -d postgres -f init_database_products.sqll
```


---

## Goals
We aim to create a retrieval-augmented framework to extract similar electronic products based on a given query.  
The system models a category of Amazon products in a relational database, enabling structured queries and efficient retrieval.
