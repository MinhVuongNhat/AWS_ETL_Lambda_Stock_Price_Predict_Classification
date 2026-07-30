---
title : "Create SQS Queue"
date: ""
weight : 3
chapter : false
pre : " <b> 5.2.3. </b> "
---

#### Create Amazon SQS Queue

Amazon SQS is the backbone of the **Fan-Out architecture** in Pipeline B. The Lambda Producer pushes chunks of ticker lists into the Queue, and multiple Lambda Consumers run in parallel to process them.

![Sqs Fanout Architecture](/images/2.3/sqs-fanout-architecture.png)

---

#### Step 1: Create SQS Queue

```bash
aws sqs create-queue \
    --queue-name daily-collector-queue \
    --region ap-southeast-1 \
    --attributes '{
        "VisibilityTimeout": "300",
        "MessageRetentionPeriod": "86400",
        "ReceiveMessageWaitTimeSeconds": "20"
    }'
```

**Attribute explanation:**

| Attribute | Value | Explanation |
|:---|:---|:---|
| `VisibilityTimeout` | `300` seconds | Time Lambda Consumer holds the message before returning it to queue on failure |
| `MessageRetentionPeriod` | `86400` seconds (1 day) | How long messages are retained in the queue |
| `ReceiveMessageWaitTimeSeconds` | `20` seconds | Long-polling — reduces unnecessary API calls |

---

#### Step 2: Get Queue URL

```bash
aws sqs get-queue-url \
    --queue-name daily-collector-queue \
    --region ap-southeast-1
```

Expected result:
```json
{
    "QueueUrl": "https://sqs.ap-southeast-1.amazonaws.com/123456789012/daily-collector-queue"
}
```

Save this **Queue URL** — you will need it when configuring Lambda environment variables.

![Sqs Queue Created](/images/2.3/sqs-queue-created.png)
