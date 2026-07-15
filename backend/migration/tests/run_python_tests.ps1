param(
    [string]$TestPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($TestPath)) {
    python -m unittest discover -s backend/migration/tests -p "test*.py" -v
} else {
    python -m unittest -v $TestPath
}
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

exit 0
