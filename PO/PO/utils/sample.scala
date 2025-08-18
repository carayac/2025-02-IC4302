//cd utils
// https://stackoverflow.com/questions/21964709/how-to-set-or-change-the-default-java-jdk-version-on-macos
//export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)
import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.SparkSession._
import org.elasticsearch.spark.sql
import org.elasticsearch.spark.sql._
import org.elasticsearch.spark._ 

sc.stop()
spark.stop();

// kubectl port-forward service/ic4302-es-http 9200:9200
val conf = new SparkConf();
conf.set("es.index.auto.create", "true");
conf.set("es.nodes", "http://127.0.0.1:9200/");
conf.set("es.net.http.auth.user", "elastic");
conf.set("es.net.http.auth.pass", "XML3s4c1pO0q79wKFS89N43Q");
conf.set("es.port", "9200");
conf.set("es.nodes.wan.only", "true");


val sc = new SparkContext(conf);

val spark = SparkSession.builder.config(sc.getConf).getOrCreate();

val sqlcontext = new org.apache.spark.sql.SQLContext(sc);

val options = Map("es.read.field.as.array.include" -> "data");



val data = spark.read.json("/Users/nereo/Documents/GitHub/tec/2025/02/DB2/PO/utils/sample/*.json");

val data = spark.read.json("/Users/Innovation Computers/Desktop/2025-02-IC4302/PO/PO/utils/sample/*.json");


data.printSchema()
data.show
data.createOrReplaceTempView("datatmp2")
spark.sql("SELECT col.* FROM (SELECT explode(collection) FROM datatmp2)").createOrReplaceTempView("data_tmp")
spark.sql("SELECT initcap(category) as category, count(1) as category_count FROM data_tmp GROUP BY category").show()

spark.sql("SELECT * FROM data_tmp LIMIT 1000").createOrReplaceTempView("data")
spark.sql("SELECT initcap(category) as category, count(1) as category_count FROM data GROUP BY category").show()
spark.sql("SELECT * FROM data").show()
spark.sql("SELECT rel_doi from data").show(false)
spark.sql("SELECT rel_doi, author.author_name AS author_name, author.author_inst AS author_inst FROM (SELECT rel_doi, explode(rel_authors) AS author from data)").show(false)
spark.sql("(SELECT rel_doi, rel_authors from data)").show(false)
spark.sql("SELECT rel_doi, author.author_inst as author_inst, author.author_name as author_name FROM (SELECT rel_doi, explode(rel_authors) as author from data)").show(false)

spark.sql("SELECT rel_doi, author.author_name AS author_name, author.author_inst AS author_inst FROM (SELECT rel_doi, explode(rel_authors) AS author from data)").createOrReplaceTempView("authors")
spark.sql("SELECT * from authors").show()
spark.sql("SELECT * from authors").count()
spark.sql("SELECT rel_doi, date(rel_date) AS rel_date FROM data").show()
spark.sql("SELECT rel_doi, date(rel_date) AS rel_date FROM data").printSchema()
spark.sql("SELECT rel_doi, date(rel_date) AS rel_date FROM data").printSchema()
spark.sql("SELECT rel_doi, date_format(rel_date, \"dd/MM/y\") AS rel_date, rel_date AS old_rel_date  FROM (SELECT rel_doi, date(rel_date) AS rel_date FROM data)").show(false)
spark.sql("SELECT rel_doi, date_format(rel_date, \"dd/MM/y\") AS rel_date, rel_date AS old_rel_date  FROM (SELECT rel_doi, date(rel_date) AS rel_date FROM data)").createOrReplaceTempView("dates")

spark.sql("SELECT rel_doi, author_name FROM authors").show()
spark.sql("SELECT rel_doi, collect_set(author_name) AS author_names FROM authors GROUP BY rel_doi").show()
spark.sql("SELECT rel_doi, collect_set(author_name) AS author_names FROM authors GROUP BY rel_doi").printSchema()
spark.sql("SELECT a.rel_doi, a.author_names, b.rel_date FROM (SELECT rel_doi, collect_set(author_name) AS author_names FROM authors GROUP BY rel_doi) AS a INNER JOIN dates AS b ON a.rel_doi = b.rel_doi").printSchema()
spark.sql("SELECT a.rel_doi, a.author_names, b.rel_date FROM (SELECT rel_doi, collect_set(author_name) AS author_names FROM authors GROUP BY rel_doi) AS a INNER JOIN dates AS b ON a.rel_doi = b.rel_doi").write.json("/Users/nereo/Documents/GitHub/tec/2025/02/DB2/PO/utils/transformed")
spark.sql("SELECT a.rel_doi, a.author_names, b.rel_date FROM (SELECT rel_doi, collect_set(author_name) AS author_names FROM authors GROUP BY rel_doi) AS a INNER JOIN dates AS b ON a.rel_doi = b.rel_doi").write.parquet("/Users/nereo/Documents/GitHub/tec/2025/02/DB2/PO/utils/transformed_parquet")
spark.sql("SELECT a.rel_doi, a.author_names, b.rel_date FROM (SELECT rel_doi, collect_set(author_name) AS author_names FROM authors GROUP BY rel_doi) AS a INNER JOIN dates AS b ON a.rel_doi = b.rel_doi").saveToEs("data")

