FROM python:3.12-slim

WORKDIR /app

# git_ops.py (infra/bot/) shells out to both via subprocess for the deploy-key
# write path (Story 6.1) — python:3.12-slim ships neither.
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main_matrix.py"]
