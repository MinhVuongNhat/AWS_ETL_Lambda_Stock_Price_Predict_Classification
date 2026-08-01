---
title: "Sự kiện 6 - FCAJ Meetup #3 & Chung kết Tranh Hùng"
date: "2026-07-11"
weight: 6
chapter: false
pre: "<b> 4.6. </b>"
---

#### Sự kiện 6 – FCAJ Meetup #3 & Chung kết Tranh Hùng (11/07/2026)

{{% notice info %}}
📅 **Ngày:** 11/07/2026 | 📍 **Hình thức:** Tham gia trực tiếp | 🏢 **Đơn vị tổ chức:** First Cloud AI Journey (FCAJ)
{{% /notice %}}

---

#### Báo cáo tóm tắt: "FCAJ Meetup #3 – Chung kết Tranh Hùng & Các buổi chia sẻ kỹ thuật"

##### Mục tiêu sự kiện
- Trao danh hiệu vô địch Tranh Hùng cho đội chiến thắng từ các đội đã vượt qua vòng loại.
- Tiếp tục chia sẻ kiến thức kỹ thuật với các bài nói về bảo mật AWS, chứng chỉ cloud practitioner và giám sát rủi ro sinh viên.
- Tôn vinh thành tích và củng cố tinh thần cộng đồng trong chương trình FCAJ.

---

#### Phần 1: Chung kết Tranh Hùng

Chung kết cuộc thi kiến thức AWS **Tranh Hùng** giữa các đội kết thúc giải đấu bắt đầu từ vòng loại ngày 20/06/2026.

**Thể thức chung kết**
- Các đội vượt qua vòng loại ngày 20/06 thi đấu trực tiếp trong vòng chung kết.
- Quy tắc tính điểm giống vòng loại: +1 điểm câu đúng, -1 điểm câu sai.
- Câu hỏi chung kết nâng cao hơn, bao gồm thiết kế kiến trúc, đánh đổi dịch vụ AWS và giải quyết vấn đề theo tình huống.

**Chủ đề nổi bật vòng chung kết**
- Thiết kế kiến trúc disaster recovery đa vùng (RPO/RTO targets).
- Lựa chọn giữa Aurora Serverless và DynamoDB cho workload ứng dụng khác nhau.
- AWS Step Functions để điều phối workflow serverless phức tạp.
- Cấu hình CloudFront distribution và chiến lược cache invalidation.
- Security Hub vs. GuardDuty vs. Inspector: chọn công cụ bảo mật phù hợp.
- AWS Organizations và Service Control Policies cho governance đa tài khoản.

---

#### Phần 2: Các buổi chia sẻ kỹ thuật

Sau chung kết, meetup tiếp tục với ba bài trình bày kỹ thuật:

**Bài 1: Inside the Exam – AWS Cloud Practitioner**
- Phân tích toàn diện cấu trúc đề thi AWS Certified Cloud Practitioner (CLF-C02) và trọng số các domain.
- Chiến lược ôn thi: tài nguyên khuyến nghị (AWS Skill Builder, Stephane Maarek, bài thi thử TutorialsDojo).
- Các chủ đề trọng tâm: cloud concepts, dịch vụ cốt lõi AWS, bảo mật & tuân thủ, thanh toán & định giá.
- Mẹo thi: quản lý thời gian, loại bỏ đáp án sai rõ ràng và kỹ thuật loại trừ.
- Hỏi đáp về các bẫy thường gặp và cách tiếp cận câu hỏi dạng tình huống.

**Bài 2: Bảo vệ ứng dụng Web với AWS Security Agent**
- Giới thiệu xây dựng security agent thông minh trên AWS để giám sát và phản hồi các mối đe dọa ứng dụng web.
- Kiến trúc: Application Load Balancer → WAF → Lambda security agent → CloudWatch logs → SNS alerting.
- Sử dụng Amazon Bedrock hoặc Claude để tạo lớp phân tích bảo mật AI-driven.
- Phát hiện mối đe dọa real-time và khắc phục tự động: block IP, cập nhật WAF rule và kích hoạt incident response.
- Demo: phát hiện mẫu SQL injection và tự động cập nhật danh sách block IP của WAF.

**Bài 3: Giám sát SLA AWS – Hệ thống đánh giá rủi ro sinh viên**
- Demo thực tế hệ thống giám sát rủi ro sinh viên trên AWS được xây dựng trong chương trình FCAJ.
- Kiến trúc: nhập dữ liệu (chỉ số sinh viên) → S3 → xử lý Lambda → DynamoDB → CloudWatch dashboard.
- Định nghĩa ngưỡng SLA cho KPI hiệu suất sinh viên và cảnh báo tự động cho sinh viên có nguy cơ.
- Bài học rút ra từ việc xây dựng hệ thống giám sát cấp production với ràng buộc AWS Free Tier.

---

#### Bài học rút ra

- **Cạnh tranh thúc đẩy chiều sâu:** Chung kết đẩy thành viên học các chủ đề AWS nâng cao hơn (đa vùng, Step Functions, Organizations) mà họ thường không gặp trong công việc dự án thông thường.
- **Chứng chỉ cung cấp cấu trúc:** Bài nói về AWS Cloud Practitioner làm rõ rằng học chứng chỉ, kể cả với developer đã dùng AWS trong dự án, giúp hệ thống hóa và lấp đầy lỗ hổng kiến thức.
- **Bảo mật AI-powered là tương lai:** Bài nói về security agent chứng minh rằng thế hệ bảo mật cloud tiếp theo không phải là rule tĩnh — mà là hệ thống thông minh, thích ứng học từ các mối đe dọa mới real-time.
- **Monitoring = chất lượng:** Xây dựng hệ thống monitoring mạnh mẽ (như trong bài SLA) quan trọng không kém xây dựng ứng dụng; đây thường là sự khác biệt giữa dự án thử nghiệm và hệ thống production.

---

#### Áp dụng vào dự án
- Học tài liệu chứng chỉ AWS Cloud Practitioner để hệ thống hóa hiểu biết và lấp lỗ hổng từ cuộc thi Tranh Hùng.
- Áp dụng kiến trúc security agent để bảo vệ API Gateway endpoint của nhóm với phát hiện mối đe dọa thông minh hơn.
- Triển khai CloudWatch dashboards cho `NasdaqStockPredictions` API để giám sát tuân thủ SLA và tỷ lệ lỗi.

---

#### Ảnh sự kiện

![FCAJ Meetup #3 – Chung kết Tranh Hùng và các buổi chia sẻ kỹ thuật](/images/event/11-07.png)

---

Sự kiện kết hợp Chung kết Tranh Hùng và FCAJ Meetup #3 có lẽ là sự kiện sôi động và đậm chất nhất trong toàn bộ chương trình. Đỉnh điểm cạnh tranh của giải đấu, kết hợp với ba bài nói kỹ thuật chất lượng cao, tạo nên một buổi kết thúc xuất sắc cho giai đoạn xây dựng cộng đồng giữa chương trình.
