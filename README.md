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

## ⚙️ Optional Docker Dataset Initialization

1. **Pull PostgreSQL Docker Image**
```bash
docker pull postgres
```
2. **Run PostgreSQL Container**
```bash
docker run --name postgresql \
  -e POSTGRES_PASSWORD=password \
  -d -p 5432:5432 postgres
```
3. **Copy SQL file to container**
```bash
docker cp init_database_products.sql postgresql:/tmp/
```
4. **Execute SQL file**
```bash
docker exec -i postgresql psql -U postgres -d postgres -f /tmp/init_database_products.sql
```
5. **List databases**
```bash
docker exec -it postgresql psql -U postgres -c "\l"
```
6. **Connect to database**
```bash
docker exec -it postgresql psql -U postgres -d products_database
```
7. **List tables**
```bash
\dt
```
8. **View table structure**
```bash
\d table_name
```
9. **Exit PostgreSQL**
```bash
\q
```
---

## Goals
We aim to create a retrieval-augmented framework to extract similar electronic products based on a given query.  
The system models a category of Amazon products in a relational database, enabling structured queries and efficient retrieval.
