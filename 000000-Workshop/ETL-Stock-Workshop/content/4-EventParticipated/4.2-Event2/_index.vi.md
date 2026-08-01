---
title: "Sự kiện 2 - FCAJ Meetup #2"
date: "2026-06-13"
weight: 2
chapter: false
pre: "<b> 4.2. </b>"
---

#### Sự kiện 2 – FCAJ Meetup #2 (13/06/2026)

{{% notice info %}}
📅 **Ngày:** 13/06/2026 | 📍 **Hình thức:** Tham gia trực tiếp | 🏢 **Đơn vị tổ chức:** First Cloud AI Journey (FCAJ)
{{% /notice %}}

---

#### Báo cáo tóm tắt: "FCAJ Meetup #2 – Kiến trúc Cloud, Bảo mật & Giám sát"

##### Mục tiêu sự kiện
- Tiếp tục đào sâu kiến thức về kiến trúc và dịch vụ AWS Cloud trong cộng đồng.
- Chia sẻ kinh nghiệm thực tế trong bảo mật cloud, phát triển ứng dụng và giám sát SLA.
- Truyền cảm hứng thông qua các case study dự án cloud thực tế.

##### Diễn giả & Chủ đề

| Diễn giả | Chủ đề |
|:---|:---|
| **Hoàng Trọng** | Kiến trúc Cloud & Các thực hành tốt nhất trên AWS |
| **Đạt & Cường** | Phát triển ứng dụng trên AWS Cloud |
| **Hiếu Nghị** | Giám sát SLA và đánh giá rủi ro trên AWS |
| **Kiên & Thọ** | Chia sẻ dự án FCAJ & Thảo luận cộng đồng |

---

#### Điểm nổi bật

**1. Kiến trúc Cloud & Thực hành tốt nhất trên AWS (Hoàng Trọng)**
- Đi sâu vào AWS Well-Architected Framework: 5 trụ cột Operational Excellence, Security, Reliability, Performance Efficiency và Cost Optimization.
- Các design pattern cho ứng dụng high-availability và fault-tolerant trên AWS.
- Hướng dẫn thực tế chọn dịch vụ AWS phù hợp cho từng loại workload.
- Các anti-pattern kiến trúc phổ biến cần tránh khi thiết kế hệ thống cloud.

**2. Phát triển ứng dụng trên AWS Cloud (Đạt & Cường)**
- Xây dựng web application có khả năng mở rộng bằng serverless services (Lambda, API Gateway, DynamoDB).
- Infrastructure as Code (IaC) với AWS CloudFormation hoặc CDK để tự động hóa provisioning tài nguyên.
- Tích hợp CI/CD pipeline với AWS CodePipeline và CodeDeploy cho continuous delivery.
- Chiến lược xử lý state trong stateless Lambda functions sử dụng DynamoDB và S3.

**3. Giám sát SLA & Đánh giá rủi ro AWS (Hiếu Nghị)**
- Hiểu AWS Service Level Agreements (SLA) và cam kết uptime của các dịch vụ chính (EC2, RDS, Lambda, S3).
- Xây dựng custom monitoring dashboard để theo dõi tuân thủ SLA và phát hiện bất thường real-time.
- Hệ thống giám sát rủi ro sinh viên: áp dụng khái niệm giám sát AWS để theo dõi chỉ số hiệu suất.
- Chiến lược cảnh báo leo thang bằng Amazon CloudWatch Alarms và SNS notifications.

**4. Chia sẻ dự án FCAJ (Kiên & Thọ)**
- Trình bày tiến độ dự án FCAJ của các nhóm: tổng quan kiến trúc, cập nhật tiến độ và các vướng mắc.
- Thảo luận bài học rút ra và giải quyết vấn đề cộng tác giữa các thành viên.
- Phiên feedback đồng đẳng để cải thiện kiến trúc và phương pháp triển khai dự án.

---

#### Bài học rút ra

- **Well-Architected là bắt buộc:** Áp dụng 5 trụ cột ngay từ đầu giúp tránh refactor tốn kém về sau.
- **Infrastructure as Code tăng tốc delivery:** Tự động hóa provisioning với CDK/CloudFormation đảm bảo triển khai nhất quán, có thể lặp lại.
- **Giám sát SLA = Liên tục kinh doanh:** Hiểu SLA dịch vụ AWS và chủ động giám sát rất quan trọng cho workload production.
- **Học hỏi từ đồng đẳng rất hiệu quả:** Nghe các team FCAJ khác chia sẻ vấn đề và cách tiếp cận mang lại góc nhìn mới cho quyết định kiến trúc của nhóm mình.

---

#### Áp dụng vào dự án
- Xem xét kiến trúc Lambda + API Gateway + DynamoDB hiện tại theo các trụ cột Well-Architected (đặc biệt Reliability và Cost Optimization).
- Xem xét thêm CloudWatch Alarms cho tỷ lệ lỗi 5xx API Gateway và Lambda timeout.
- Thực hiện peer architecture review trong nhóm trước khi hoàn thiện thiết kế hệ thống.

---

#### Ảnh sự kiện
*Thêm ảnh sự kiện của bạn tại đây.*

---

FCAJ Meetup #2 tiếp tục xây dựng trên nền tảng vững chắc từ buổi đầu tiên, tập trung đặc biệt vào kiến trúc cloud thực tế, giám sát và phát triển ứng dụng. Phiên chia sẻ dự án đồng đẳng đặc biệt có giá trị, nuôi dưỡng văn hóa học tập cộng tác giữa tất cả các team trong chương trình FCAJ.
