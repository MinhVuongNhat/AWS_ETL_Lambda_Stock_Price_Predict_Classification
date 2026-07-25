# Base Image: AWS Lambda Python 3.12
FROM public.ecr.aws/lambda/python:3.12

# Copy file requirements và cài đặt thư viện
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir xgboost -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy source code
COPY src/ ${LAMBDA_TASK_ROOT}

# Default handler
CMD ["lambda_quality_gate.lambda_handler"]