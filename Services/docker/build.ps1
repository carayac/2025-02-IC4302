param (
    [Parameter(Mandatory = $true)]
    [string]$Username
)

# Login a Docker
docker login

# # ---------------------------------------- BeautifulSoup ----------------------------------------
# Set-Location BeautifulSoup
# docker build -t "$Username/beautiful-soup" .
# docker push "$Username/beautiful-soup"
# Set-Location ..

# # ---------------------------------------- Controller ----------------------------------------
# Set-Location Controller
# docker build -t "$Username/controller" .
# docker push "$Username/controller"
# Set-Location ..

# # ---------------------------------------- Spacy Entity Extractor ----------------------------------------
# Set-Location SpacyEntityExtractor
# docker build -t "$Username/spacy-entity-extractor" .
# docker push "$Username/spacy-entity-extractor"
# Set-Location ..

# ---------------------------------------- Spark Processor Job ----------------------------------------
Set-Location SparkProcessorJob
docker build -t "$Username/spark-processor-job" .
docker push "$Username/spark-processor-job"
Set-Location ..
