param (
    [Parameter(Mandatory = $true)]
    [string]$Username
)

# Login a Docker
docker login

# # ---------------------------------------- BeautifulSoup ----------------------------------------
# Set-Location BeautifulSoup
# docker build -t "$USERNAME/beautiful-soup" .
# docker push "$USERNAME/beautiful-soup"
# cd ..

# ----------------------------------------Controller----------------------------------------
Set-Location Controller
docker build -t "$USERNAME/controller" .
docker push "$USERNAME/controller"
cd ..

# # # # ---------------------------------------- Spacy Entity Extractor ----------------------------------------
# Set-Location SpacyEntityExtractor
# docker build -t "$USERNAME/spacy-entity-extractor" .
# docker push "$USERNAME/spacy-entity-extractor"
# cd ..

# # # ---------------------------------------- Spark Processor Job ----------------------------------------
# Set-Location SparkProcessorJob
# docker build -t "$USERNAME/spark-processor-job" .
# docker push "$USERNAME/spark-processor-job"
# cd ..

# # ---------------------------------------- Spark Processor Job ----------------------------------------
# Set-Location SparkProcessorJob
# docker build -t "$Username/spark-processor-job" .
# docker push "$Username/spark-processor-job"
# Set-Location ..
