FROM public.ecr.aws/lambda/python:3.10

# Cài đặt thư viện
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào Container
COPY src/ ${LAMBDA_TASK_ROOT}

# Chỉ định Entry Point
CMD ["lambda_function.lambda_handler"]