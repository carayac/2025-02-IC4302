from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, split, lower, trim, Row


#create a spark session for use in other functions and do not open multiple sessions
def createSession(app_name="Spark Processor Job"):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    return spark

def read_augmented_data(spark, input_path):
    # Read the augmented data from the specified input path
    df = spark.read.json(input_path)
    return df

def extract_entities(df):
    return df

def get_related_products(df):
    return df

def add_related_products(df):
    return df

def normalize_text_lowercase(text):
    return text.lower().strip()

def normalize_date_fields(df):
    # Normalize date fields to a standard format (e.g., DD/MM/YYYY)
    
    return df

def normalize_description(df):
    # Normalize description creatint a short description wirh max 140 characters
    
    return df

def normalize_data(df):
    # Normalize the text fields to lowercase and trim whitespace
    
    return df

def main():
    spark = createSession()
    input_path = "hdfs://path/to/augmented/data"
    df = read_augmented_data(spark, input_path)
    normalized_df = normalize_data(df)
    # Further processing can be done here
    spark.stop()
