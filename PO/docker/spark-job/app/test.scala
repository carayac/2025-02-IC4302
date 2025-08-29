import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.SparkSession._
import org.elasticsearch.spark.sql
import org.elasticsearch.spark.sql._
import org.elasticsearch.spark._ 

sc.stop()
spark.stop()


val tmp_data = spark.read.json("/data")
tmp_data.createOrReplaceTempView("tmp")

tmp_data.printSchema()