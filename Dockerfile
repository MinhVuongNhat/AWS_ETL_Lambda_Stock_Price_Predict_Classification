# Dùng Python 3.10 của AWS Lambda
FROM public.ecr.aws/lambda/python:3.12

# Copy file requirements và cài đặt thư viện
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn trong thư mục src/ vào Container
COPY src/ ${LAMBDA_TASK_ROOT}

# Mặc định để Quality Gate làm entrypoint (Lên AWS có thể Override sau)
CMD ["lambda_quality_gate.lambda_handler"]