---
title: "Sự kiện 7 - FCAJ x AABW Community Day"
date: "2026-07-25"
weight: 7
chapter: false
pre: "<b> 4.7. </b>"
---

#### Sự kiện 7 – FCAJ x AABW Community Day (25/07/2026)

{{% notice info %}}
📅 **Ngày:** 25/07/2026 | 📍 **Hình thức:** Tham gia trực tiếp | 🏢 **Đơn vị tổ chức:** First Cloud AI Journey (FCAJ) x AWS Ambassadors & Builders in Vietnam (AABW)
{{% /notice %}}

---

#### Báo cáo tóm tắt: "FCAJ x AABW Community Day – Hackathon, Giải pháp Cloud & Phát triển Native App"

##### Mục tiêu sự kiện
- Giới thiệu hành trình và kết quả của các nhóm FCAJ qua hình thức trình bày dự án theo phong cách hackathon.
- Chia sẻ kiến thức kiến trúc cloud nâng cao và thực hành tốt nhất trong phát triển native application.
- Tôn vinh sự cộng tác cộng đồng giữa FCAJ và AABW (AWS Ambassadors & Builders in Vietnam).
- Tạo cơ hội kết nối giữa học viên, AWS ambassador và người thực hành cloud có kinh nghiệm.

##### Các bài trình bày

| # | Bài trình bày | Mô tả |
|:---|:---|:---|
| 1 | **Hackathon Journey – 3KA** | Chia sẻ hành trình và trải nghiệm hackathon của team FCAJ |
| 2 | **SA Professional – Native App Development** | Kiến thức Solutions Architect về thiết kế native app trên cloud |
| 3 | **SignalScout** | Demo ứng dụng signal intelligence chạy trên cloud |
| 4 | **OneTeam Community Day** | Điểm nổi bật cộng đồng và tổng kết chương trình |

---

#### Điểm nổi bật

**1. Hackathon Journey – 3KA**
- Team 3KA chia sẻ hành trình end-to-end hoàn chỉnh xây dựng giải pháp cloud trong giai đoạn hackathon FCAJ.
- Walkthrough kiến trúc: từ yêu cầu và thiết kế qua triển khai, kiểm thử và deploy trên AWS.
- Các quyết định kỹ thuật chính: lý do lựa chọn dịch vụ, đánh đổi và bài học rút ra từ deploy AWS thực tế.
- Khó khăn vượt qua: tối ưu cold start, bottleneck data pipeline và quản lý chi phí trong giới hạn Free Tier.
- Phản tư về teamwork, quản lý thời gian dưới ràng buộc hackathon và quy trình phát triển lặp.

**2. SA Professional – Phát triển Native App trên AWS**
- Hướng dẫn cấp Solutions Architect về thiết kế ứng dụng cloud-native hiện đại.
- **Twelve-Factor App methodology** áp dụng vào AWS: cấu hình qua biến môi trường, quy trình disposable và parity dev/prod.
- So sánh các kiến trúc pattern cho native app: monolith vs. microservices vs. serverless — chọn đúng approach dựa trên quy mô nhóm, workload và yêu cầu scalability.
- Đi sâu vào container orchestration: ECS vs. EKS vs. App Runner cho các kịch bản deploy khác nhau.
- Best practice thiết kế API, versioning và backwards compatibility trên API Gateway.
- Observability stack: triển khai structured logging (CloudWatch Logs Insights), distributed tracing (X-Ray) và metrics dashboards.

**3. SignalScout – Signal Intelligence chạy trên Cloud**
- Demo trực tiếp SignalScout: ứng dụng cloud tổng hợp, phân tích và trực quan hóa dữ liệu signal intelligence.
- Kiến trúc: nhập dữ liệu real-time → xử lý Lambda → lưu DynamoDB → API Gateway → React frontend.
- Tích hợp machine learning: anomaly detection models deploy như Lambda functions để phân loại signal real-time.
- Thiết kế scalability: xử lý burst traffic với SQS buffering và quản lý concurrency Lambda.
- Bài học thực tế khi xây dựng ứng dụng cloud production-ready như team sinh viên với ràng buộc thời gian và ngân sách.

**4. OneTeam Community Day – Tổng kết & Bế mạc**
- Tổng kết chương trình: điểm nổi bật, thành tích và kỷ niệm đáng nhớ từ khóa FCAJ.
- Ghi nhận cộng đồng: tôn vinh đóng góp nổi bật của học viên, mentor và đội admin.
- Phiên networking: Q&A mở, trao đổi kiến thức và kết nối giữa học viên FCAJ và thành viên AABW.
- Hướng tới tương lai: các giai đoạn FCAJ tiếp theo, lộ trình học tập khuyến nghị và tham gia cộng đồng liên tục.

---

#### Bài học rút ra

- **Kinh nghiệm dự án end-to-end là vô giá:** Nghe hành trình hackathon hoàn chỉnh của Team 3KA củng cố rằng học hỏi quý giá nhất đến từ việc xây dựng và deploy hệ thống thực dưới áp lực, không phải chỉ học lý thuyết.
- **Nguyên tắc cloud-native là phổ quát:** Twelve-Factor App và pattern microservices được SA professional thảo luận áp dụng trực tiếp cho kiến trúc Lambda + API Gateway + DynamoDB của nhóm.
- **Production readiness vượt ra ngoài chức năng:** SignalScout chứng minh observability (logging, tracing, dashboards), thiết kế scalability và quản lý chi phí là bắt buộc cho mọi hệ thống AWS production.
- **Cộng đồng nhân lên việc học:** Format FCAJ x AABW kết nối học viên với AWS ambassador và builders có chuyên môn sâu, thực chiến — kiến thức không tìm được trong tài liệu.
- **Phản tư là một phần của hành trình:** Tổng kết OneTeam chứng minh rằng phản tư chương trình có cấu trúc có giá trị ngang với công việc kỹ thuật.

---

#### Áp dụng vào dự án
- Áp dụng nguyên tắc Twelve-Factor App để refactor quản lý cấu hình Lambda (hiện dùng hardcoded env vars — chuyển sang AWS Systems Manager Parameter Store).
- Triển khai AWS X-Ray distributed tracing trên Lambda functions để có end-to-end visibility về latency và error path.
- Sử dụng pattern SQS buffering của SignalScout làm cảm hứng xử lý burst traffic trong pipeline nhập dữ liệu cổ phiếu.
- Tài liệu hóa hành trình end-to-end của dự án trong Workshop (trang này!) theo format narrative được Team 3KA chứng minh.

---

#### Ảnh sự kiện

![FCAJ x AABW Community Day – Buổi triển lãm hackathon và gặp gỡ cộng đồng](/images/event/25-07.jpg)

---

FCAJ x AABW Community Day là sự kiện bế mạc hoàn hảo cho chương trình FCAJ — kết hợp giới thiệu thành tích dự án học viên với các bài nói kỹ thuật đẳng cấp từ AWS ambassador và builder. Nó để lại trong mỗi thành viên năng lượng và động lực tiếp tục xây dựng, học hỏi và đóng góp cho cộng đồng AWS Việt Nam.
