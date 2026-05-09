param(
    [string]$TestPath = "tests/test_csv_validator.py"
)

$ErrorActionPreference = "Stop"

python -m unittest -v $TestPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

exit 0
