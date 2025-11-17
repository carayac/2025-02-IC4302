param (
    [Parameter(Mandatory = $true)]
    [string]$Username
)

# Login a Docker
docker login


# #-------------------------INICIO DATASEEDER ----------------------------
Set-Location ./DataSeeder
docker build -t "$Username/dataseeder" .
docker push "$Username/dataseeder"
cd ..
# #-------------------------FIN DATASEEDER ----------------------------

