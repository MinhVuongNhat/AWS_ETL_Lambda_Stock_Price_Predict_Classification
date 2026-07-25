# ============================================================
#  deploy_container_lambda.ps1
#  Script deploy tất cả Lambda functions từ Container Image
#  Chạy: .\deploy_container_lambda.ps1
# ============================================================

# ── CẤU HÌNH ────────────────────────────────────────────────
$AWS_ACCOUNT_ID  = "430970051812"
$AWS_REGION      = "ap-southeast-1"
$ECR_REPO_NAME   = "stock-lambda"
$IMAGE_TAG        = "latest"
$LAMBDA_ROLE_ARN = "arn:aws:iam::${AWS_ACCOUNT_ID}:role/LambdaExecutionRole"   # <-- Đổi nếu role name khác

# Các Lambda function và handler tương ứng
$FUNCTIONS = @(
    @{ Name = "stock-predictor";        Handler = "lambda_stock_predictor.lambda_handler" },
    @{ Name = "stock-daily-etl";        Handler = "lambda_daily_etl.lambda_handler" },
    @{ Name = "stock-daily-collector";  Handler = "lambda_daily_collector.lambda_handler" },
    @{ Name = "stock-quality-gate";     Handler = "lambda_quality_gate.lambda_handler" },
    @{ Name = "stock-api";              Handler = "lambda_api_handler.lambda_handler" }
)

# ── BƯỚC 1: Đăng nhập ECR ───────────────────────────────────
$ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
$IMAGE_URI = "${ECR_URI}/${ECR_REPO_NAME}:${IMAGE_TAG}"

Write-Host "`n[1/4] Đăng nhập ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $AWS_REGION |
    docker login --username AWS --password-stdin $ECR_URI

if ($LASTEXITCODE -ne 0) { Write-Error "Đăng nhập ECR thất bại"; exit 1 }

# ── BƯỚC 2: Tạo ECR repo nếu chưa có ────────────────────────
Write-Host "`n[2/4] Kiểm tra / tạo ECR repository..." -ForegroundColor Cyan
$repoExists = aws ecr describe-repositories `
    --repository-names $ECR_REPO_NAME `
    --region $AWS_REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Repo chua ton tai, dang tao..."
    aws ecr create-repository `
        --repository-name $ECR_REPO_NAME `
        --region $AWS_REGION `
        --image-scanning-configuration scanOnPush=true | Out-Null
    Write-Host "  Da tao repo: $ECR_REPO_NAME"
} else {
    Write-Host "  Repo da ton tai: $ECR_REPO_NAME"
}

# ── BƯỚC 3: Build và Push Image ─────────────────────────────
Write-Host "`n[3/4] Build Docker image..." -ForegroundColor Cyan
docker build --platform linux/amd64 -t "${ECR_REPO_NAME}:${IMAGE_TAG}" .

if ($LASTEXITCODE -ne 0) { Write-Error "Docker build that bai"; exit 1 }

docker tag "${ECR_REPO_NAME}:${IMAGE_TAG}" $IMAGE_URI
docker push $IMAGE_URI

if ($LASTEXITCODE -ne 0) { Write-Error "Docker push that bai"; exit 1 }
Write-Host "  Image da push: $IMAGE_URI"

# ── BƯỚC 4: Tạo hoặc Update từng Lambda Function ────────────
Write-Host "`n[4/4] Deploy Lambda functions..." -ForegroundColor Cyan

foreach ($fn in $FUNCTIONS) {
    $fnName    = $fn.Name
    $handler   = $fn.Handler

    Write-Host "`n  -> Xu ly: $fnName ($handler)"

    # Kiểm tra function đã tồn tại chưa
    $exists = aws lambda get-function --function-name $fnName --region $AWS_REGION 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        # Tạo mới
        Write-Host "    Tao moi Lambda function..."
        aws lambda create-function `
            --function-name $fnName `
            --package-type Image `
            --code ImageUri=$IMAGE_URI `
            --role $LAMBDA_ROLE_ARN `
            --region $AWS_REGION `
            --architectures x86_64 `
            --memory-size 512 `
            --timeout 300 `
            --image-config "Command=$handler" | Out-Null
        Write-Host "    Da tao: $fnName"
    } else {
        # Update code (image mới)
        Write-Host "    Update image cho Lambda function..."
        aws lambda update-function-code `
            --function-name $fnName `
            --image-uri $IMAGE_URI `
            --region $AWS_REGION | Out-Null
        
        # Chờ update hoàn tất rồi mới update config
        aws lambda wait function-updated `
            --function-name $fnName `
            --region $AWS_REGION

        # Update handler (CMD override)
        aws lambda update-function-configuration `
            --function-name $fnName `
            --image-config "Command=$handler" `
            --region $AWS_REGION | Out-Null
        Write-Host "    Da update: $fnName"
    }
}

Write-Host "`nDeploy hoan tat! Tat ca Lambda dang dung image: $IMAGE_URI" -ForegroundColor Green
