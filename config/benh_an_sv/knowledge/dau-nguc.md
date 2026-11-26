---
trieu_chung: Đau ngực
tien_to_id: DN
nguon: Bài 1. Tiếp cận bệnh nhân đau ngực — ThS.BS. Nguyễn Đình Quốc Anh, TS.BS. Hoàng Văn Sỹ
cau_truc: theo-nguyen-nhan
trang_thai: NHAP   # chỉ người dùng được đổi thành DA_RA_SOAT
nguoi_tao: Claude. Trích dẫn lấy từ văn bản chương; cột Loại do quy tắc tự động xếp từ bản v1, cần bạn duyệt
---

# Kiến thức đau ngực (từ Bài 1), xếp theo từng nguyên nhân

## Quy ước
- Mỗi nguyên nhân có một khối. Trong khối, mỗi dòng là một dấu hiệu với: Nguồn dữ kiện (BS bệnh sử, TC tiền căn, K khám/nghiệm pháp, CLS cận lâm sàng) và Loại.
- Loại: **G** gợi ý, **C** chẩn đoán (sách nêu là biểu hiện điển hình/đặc trưng/tiêu chuẩn của bệnh), **L** loại trừ (sách dùng chữ "loại trừ"), **IN** ít nghĩ (sách nói hiếm/ít khi), **LY** lưu ý (có thể gặp, không đặc hiệu, không loại trừ hoàn toàn), **CPL** chưa phân loại.
- Quy tắc xếp tự động ở bản này: dấu `+` của v1 thành G, trừ khi mục sách là mô tả bệnh cảnh điển hình (mục 6.x), có chữ "điển hình/đặc trưng", là cận lâm sàng hoặc là cột của Bảng 2, Bảng 3 thì thành C; `-` thành IN; `~` thành LY. Sách Bài 1 chưa có dòng nào dùng chữ "loại trừ" cho một nguyên nhân cụ thể nên chưa có L. Bạn hãy duyệt lại cột Loại.
- Cột "Trích nguyên văn" chép y nguyên từ sách, trong “ ”. Đã kiểm tra bằng tools/kiem_tra_kien_thuc.py.
- Yếu tố nguy cơ chung (rối loạn lipid, đái tháo đường, tăng huyết áp, hút thuốc) không lập khối riêng ở đây, nằm trong các dòng TC của bệnh động mạch vành.

## Danh sách nguyên nhân (Bảng 1)
| ID | Nguyên nhân (theo sách) | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-DN-N01 | Bệnh động mạch vành | TIM-MV | Bảng 1 | “Bệnh động mạch vành (đau thắt ngực ổn định, đau thắt ngực không ổn định, nhồi máu cơ tim)” |
| KN-DN-N02 | Viêm màng ngoài tim, viêm cơ tim | TIM-MNT, TIM-VCT | Bảng 1 | “Viêm màng ngoài tim, viêm cơ tim” |
| KN-DN-N03 | Phình bóc tách động mạch chủ | TIM-DMC | Bảng 1 | “Phình bóc tách động mạch chủ” |
| KN-DN-N04 | Thuyên tắc phổi | PHOI-TTP | Bảng 1 | “Thuyên tắc phổi” |
| KN-DN-N05 | Tăng áp phổi | PHOI-TAP | Bảng 1 | “Tăng áp phổi” |
| KN-DN-N06 | Viêm màng phổi và/hoặc viêm phổi | PHOI-MP, PHOI-VP | Bảng 1 | “Viêm màng phổi và/hoặc viêm phổi” |
| KN-DN-N07 | Viêm khí phế quản | PHOI-KPQ | Bảng 1 | “Viêm khí phế quản” |
| KN-DN-N08 | Tràn khí màng phổi | PHOI-TKMP | Bảng 1 | “Tràn khí màng phổi” |
| KN-DN-N09 | Ung thư phổi | PHOI-UNG | Bảng 1 | “Ung thư phổi” |
| KN-DN-N10 | Bệnh trào ngược dạ dày - thực quản | TH-GERD | Bảng 1 | “Bệnh trào ngược dạ dày - thực quản” |
| KN-DN-N11 | Loét dạ dày - tá tràng | TH-LOET | Bảng 1 | “Loét dạ dày - tá tràng” |
| KN-DN-N12 | Bệnh túi mật | TH-TUIMAT | Bảng 1 | “Bệnh túi mật” |
| KN-DN-N13 | Viêm tụy | TH-TUY | Bảng 1 | “Viêm tụy” |
| KN-DN-N14 | Viêm sụn sườn, chấn thương, căng cơ | TT-THANH | Bảng 1 | “Viêm sụn sườn” “Chấn thương” “Căng cơ” |
| KN-DN-N15 | Bệnh đĩa đệm cột sống cổ | TT-DIADEM | Bảng 1 | “Bệnh đĩa đệm cột sống cổ” |
| KN-DN-N16 | Herpes zoster | TT-HZ | Bảng 1 | “Herpes zoster” |
| KN-DN-N17 | Rối loạn hoảng sợ | TAMLY | Bảng 1 | “Rối loạn hoảng sợ” |

## TIM-MV — Bệnh mạch vành (HCVC, HCVM, NMCT)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B01@TIM-MV | BS | C | Đau kiểu siết chặt, đè ép | DN-05 | 2.1 | “Đau kiểu siết chặt, đè ép được xem là biểu hiện điển hình của cơn đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-B07@TIM-MV | BS | C | Đau sau xương ức lan lên cổ, hàm, vai hoặc cánh tay | DN-02, DN-03 | 2.2 | “Đau sau xương ức lan lên cổ, hàm, vai hoặc cánh tay điển hình cho đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-B36@TIM-MV | BS | C | Đau thắt ngực ổn định: xảy ra sau gắng sức, gặp lạnh, stress | DN-01 | 6.1 | “Cơn đau xảy ra sau gắng sức, gặp lạnh hoặc stress.” |
| KN-DN-B37@TIM-MV | BS | C | Đau thắt ngực ổn định: kéo dài 20 giây đến 20 phút | DN-04 | 6.1 | “Đau kéo dài 20 giây đến 20 phút.” |
| KN-DN-B38@TIM-MV | BS | C | Đau thắt ngực ổn định: giảm nhanh khi ngưng hoạt động hoặc ngậm nitroglycerin | DN-07 | 6.1 | “Đau giảm nhanh khi bệnh nhân ngưng mọi hoạt động hoặc ngậm nitroglycerin.” |
| KN-DN-B39@TIM-MV | BS | C | Đau thắt ngực ổn định: sau xương ức, siết chặt, nghiền nát | DN-02, DN-05 | 6.1 | “Đau ngay sau xương ức.” “Cảm giác như siết chặt, nghiền nát.” |
| KN-DN-B40@TIM-MV | BS | C | Hội chứng vành cấp: đau khi nghỉ, kéo dài trên 20 phút, không giảm với nitroglycerin | DN-01, DN-04, DN-07 | 6.1 | “Cơn đau thường xảy ra khi nghỉ ngơi, lan rộng hơn, kéo dài hơn 20 phút và không giảm đau với nitroglycerin.” |
| KN-DN-B41@TIM-MV | BS | C | Hội chứng vành cấp: rất mệt, khó thở, vã mồ hôi, buồn nôn, nôn | DN-10, DN-11, DN-17 | 6.1 | “Tình trạng này khiến cho bệnh nhân rất mệt, khó thở, vã mồ hôi, có thể buồn nôn và nôn.” |
| KN-DN-P01-01@TIM-MV | BS | C | Bảng 2, cột Đau thắt ngực | — | Bảng 2 | “Siết chặt hoặc đè ép” |
| KN-DN-P01-02@TIM-MV | BS | C | Bảng 2, cột Đau thắt ngực | — | Bảng 2 | “Khởi phát khi gắng sức” |
| KN-DN-P01-03@TIM-MV | BS | C | Bảng 2, cột Đau thắt ngực | — | Bảng 2 | “Giảm khi nghỉ” |
| KN-DN-P01-04@TIM-MV | BS | C | Bảng 2, cột Đau thắt ngực | — | Bảng 2 | “Giảm khi dùng nitrate” |
| KN-DN-P01-05@TIM-MV | BS | C | Bảng 2, cột Đau thắt ngực | — | Bảng 2 | “Không liên quan đến tư thế” |
| KN-DN-P01-06@TIM-MV | BS | C | Bảng 2, cột Đau thắt ngực | — | Bảng 2 | “Không ảnh hưởng bởi hô hấp” |
| KN-DN-P04-01@TIM-MV | BS | C | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | — | Bảng 3 | “Khởi phát khi nghỉ” |
| KN-DN-P04-02@TIM-MV | BS | C | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | — | Bảng 3 | “Đau nhiều” |
| KN-DN-P04-03@TIM-MV | BS | C | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | — | Bảng 3 | “Vã mồ hôi” |
| KN-DN-P04-04@TIM-MV | BS | C | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | — | Bảng 3 | “Lo lắng nhiều” |
| KN-DN-P04-05@TIM-MV | BS | C | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | — | Bảng 3 | “Không giảm với nitrate” |
| KN-DN-P04-06@TIM-MV | BS | C | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | — | Bảng 3 | “Có triệu chứng kèm theo (buồn nôn, nôn)” |
| KN-DN-P05-01@TIM-MV | BS | C | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | — | Bảng 3 | “Khởi phát khi gắng sức” |
| KN-DN-P05-02@TIM-MV | BS | C | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | — | Bảng 3 | “Đau vừa phải” |
| KN-DN-P05-03@TIM-MV | BS | C | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | — | Bảng 3 | “Không vã mồ hôi” |
| KN-DN-P05-04@TIM-MV | BS | C | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | — | Bảng 3 | “Không lo lắng hoặc lo lắng ít” |
| KN-DN-P05-05@TIM-MV | BS | C | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | — | Bảng 3 | “Giảm đau với nitrate” |
| KN-DN-P05-06@TIM-MV | BS | C | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | — | Bảng 3 | “Không có triệu chứng kèm theo” |
| KN-DN-P06-01@TIM-MV | BS | C | Bảng 3, nhồi máu cơ tim (so với bóc tách động mạch chủ) | — | Bảng 3 | “Đau giữa ngực” |
| KN-DN-P06-02@TIM-MV | BS | C | Bảng 3, nhồi máu cơ tim (so với bóc tách động mạch chủ) | — | Bảng 3 | “Khởi phát bán cấp (vài phút)” |
| KN-DN-P06-03@TIM-MV | BS | C | Bảng 3, nhồi máu cơ tim (so với bóc tách động mạch chủ) | — | Bảng 3 | “Đau nhiều” |
| KN-DN-P08-01@TIM-MV | BS | C | Bảng 3, thiếu máu cục bộ cơ tim (so với đau thành ngực) | — | Bảng 3 | “Liên quan đến gắng sức” |
| KN-DN-P08-02@TIM-MV | BS | C | Bảng 3, thiếu máu cục bộ cơ tim (so với đau thành ngực) | — | Bảng 3 | “Xảy ra khi gắng sức” |
| KN-DN-P08-03@TIM-MV | BS | C | Bảng 3, thiếu máu cục bộ cơ tim (so với đau thành ngực) | — | Bảng 3 | “Đau từng cơn” |
| KN-DN-P08-04@TIM-MV | BS | C | Bảng 3, thiếu máu cục bộ cơ tim (so với đau thành ngực) | — | Bảng 3 | “Đau lan” |
| KN-DN-B13@TIM-MV | BS | G | Thiếu máu cơ tim: nặng dần vài phút, tăng khi gắng sức, giảm khi nghỉ | DN-01, DN-04, DN-06, DN-07 | 2.3 | “Đau ngực do thiếu máu cục bộ cơ tim thường nặng dần trong vài phút, tăng khi gắng sức, giảm khi nghỉ ngơi.” |
| KN-DN-B17@TIM-MV | BS | G | Thích ngồi nghỉ hoặc dừng đi bộ để giảm đau | DN-07 | 2.4 | “Bệnh nhân đau ngực do thiếu máu cục bộ cơ tim thường thích ngồi nghỉ ngơi hoặc tạm dừng đi bộ để giảm đau.” |
| KN-DN-B24@TIM-MV | BS | G | Giảm trong vài phút khi dùng nitroglycerin | DN-07 | 2.4 | “Đau ngực giảm trong vòng vài phút khi dùng nitroglycerin gợi ý thiếu máu cục bộ cơ tim, tuy nhiên cũng có thể gặp trong co thắt thực quản.” |
| KN-DN-B25@TIM-MV | BS | G | Triệu chứng kèm theo trong thiếu máu cơ tim | DN-10, DN-11, DN-17 | 2.5 | “Các triệu chứng kèm theo trong thiếu máu cục bộ cơ tim bao gồm: vã mồ hôi, khó thở, buồn nôn, mệt mỏi, choáng váng, ợ hơi.” |
| KN-DN-B30@TIM-MV | BS | G | Ngất hoặc tiền ngất | DN-13 | 2.5 | “Sự xuất hiện của ngất hoặc tiền ngất cần nghĩ đến thuyên tắc phổi, bóc tách động mạch chủ, rối loạn nhịp do thiếu máu cục bộ cơ tim.” |
| KN-DN-B08@TIM-MV | BS | IN | Đau khu trú chỉ bằng một đầu ngón tay | DN-02 | 2.2 | “Đau thắt ngực ít khi khu trú chỉ bằng một đầu ngón tay.” |
| KN-DN-B09@TIM-MV | BS | IN | Đau vượt quá hàm dưới hoặc dưới rốn | DN-02, DN-03 | 2.2 | “Đau thắt ngực cũng có thể đau ở thượng vị nhưng hiếm khi đau vượt quá hàm dưới hoặc dưới rốn.” |
| KN-DN-B15@TIM-MV | BS | IN | Đau chỉ vài giây, hoặc hằng định nhiều giờ đến nhiều ngày | DN-04 | 2.3 | “Đau ngực chỉ kéo dài một vài giây hoặc hằng định về cường độ trong một thời gian dài (nhiều giờ đến nhiều ngày) hiếm khi do thiếu máu cục bộ cơ tim.” |
| KN-DN-B18@TIM-MV | BS | IN | Cường độ đổi theo tư thế hoặc cử động chi trên, cổ [mã suy ra: sách ghi chung "cơ xương khớp"] | DN-06 | 2.4 | “Đau ngực có cường độ thay đổi liên quan đến tư thế hoặc cử động chi trên và cổ thường gợi ý đến các nguyên nhân về cơ xương khớp, ít khi do thiếu máu cục bộ cơ tim.” |
| KN-DN-B02@TIM-MV | BS | LY | Bệnh nhân thiếu máu cơ tim có thể than khó thở/lo lắng thay vì đau ngực | DN-11 | 2.1 | “một số bệnh nhân thiếu máu cục bộ cơ tim lại than phiền về triệu chứng khó thở hoặc cảm giác lo lắng mơ hồ hơn là triệu chứng đau ngực” |
| KN-DN-B06@TIM-MV | BS | LY | Đau kiểu nóng rát | DN-05 | 2.1 | “Đau kiểu nóng rát gợi ý bệnh trào ngược dạ dày-thực quản nhưng cũng có thể xảy ra ở bệnh nhân thiếu máu cục bộ cơ tim.” |
| KN-DN-B21@TIM-MV | BS | LY | Đau sau ăn vẫn có thể do bệnh động mạch vành nặng | DN-01 | 2.4 | “ở những bệnh nhân có bệnh động mạch vành nặng, sự tái phân bố máu đến nội tạng sau bữa ăn có thể khởi phát cơn đau thắt ngực sau ăn” |
| KN-DN-B31@TIM-MV | BS | LY | Buồn nôn, nôn: thường gợi ý bệnh tiêu hóa nhưng cũng gặp trong nhồi máu cơ tim (thường thành dưới) | DN-17 | 2.5 | “Mặc dù buồn nôn và nôn thường gợi ý bệnh lý tiêu hóa nhưng cũng có thể xảy ra trong bệnh cảnh nhồi máu cơ tim (thường là nhồi máu cơ tim thành dưới)” |
| KN-DN-B32@TIM-MV | TC | G | Tiền căn: yếu tố nguy cơ bệnh mạch vành | DN-23, DN-31 | 3 | “Tiền căn cần chú ý đánh giá các yếu tố nguy cơ bệnh mạch vành (hút thuốc lá, tăng huyết áp, đái tháo đường, rối loạn lipid máu...)” |
| KN-DN-B35@TIM-MV | TC | LY | Bệnh nhân trẻ: khai thác thêm thuốc gây nghiện (cocaine) | DN-31 | 3 | “Những bệnh nhân trẻ tuổi thường ít có nguy cơ của bệnh lý mạch vành cần khai thác thêm tiền căn sử dụng thuốc gây nghiện (cocaine).” |
| KN-DN-K26@TIM-MV | K | C | Bệnh động mạch vành: gallop T3/T4, hở van hai lá, ran phổi nếu có biến chứng | — | 6.1 | “Khám thực thể có thể nghe được tiếng ngựa phi (gallop) T3, T4, âm thổi của hở van hai lá, ran ở phổi nếu nhồi máu cơ tim có biến chứng.” |
| KN-DN-P08-05@TIM-MV | K | C | Bảng 3, thiếu máu cục bộ cơ tim (so với đau thành ngực) | — | Bảng 3 | “Không điểm đau thành ngực” |
| KN-DN-K01@TIM-MV | K | G | Tổng quát: lo lắng, khó chịu, xanh tím, vã mồ hôi | — | 4.1 | “Bệnh nhân bị nhồi máu cơ tim hoặc bệnh tim phổi cấp tính thường lo lắng, khó chịu, xanh tím, vã mồ hôi.” |
| KN-DN-K03@TIM-MV | K | G | Nhịp tim nhanh và tụt huyết áp: dấu hiệu huyết động quan trọng | — | 4.2 | “Nhịp tim nhanh và tụt huyết áp là những dấu hiệu về huyết động học quan trọng” “nhồi máu cơ tim với biến chứng choáng tim, thuyên tắc phổi diện rộng, viêm màng ngoài tim cấp với tràn dịch màng ngoài tim gây chèn ép tim cấp hoặc tràn khí màng phổi áp lực” |
| KN-DN-K09@TIM-MV | K | G | Phù phổi cấp do suy thất trái hoặc biến chứng cơ học của nhồi máu cơ tim | — | 4.3 | “Suy thất trái và các biến chứng cơ học cấp do nhồi máu cơ tim có thể dẫn đến phù phổi cấp.” |
| KN-DN-K12@TIM-MV | K | G | Âm thổi hở van hai lá hoặc thông liên thất | — | 4.4 | “Âm thổi của hở van hai lá hoặc âm thổi thô ráp của thông liên thất có thể gợi ý đến biến chứng cơ học của nhồi máu cơ tim cấp.” |
| KN-DN-K24@TIM-MV | K | G | U vàng quanh mắt (xanthoma) | — | 4.8 | “cũng cần thăm khám tìm u vàng quanh mắt (xanthoma) gợi ý nguy cơ bệnh mạch vành” |
| KN-DN-K07@TIM-MV | K | LY | Sốt nhẹ: không đặc hiệu | — | 4.2 | “Sốt nhẹ không phải là dấu hiệu đặc hiệu vì có thể gặp trong nhồi máu cơ tim hoặc thuyên tắc huyết khối kèm nhiễm trùng.” |
| KN-DN-K10@TIM-MV | K | LY | Tĩnh mạch cảnh: thường bình thường ở hội chứng vành cấp | — | 4.4 | “Xung động tĩnh mạch cảnh thường bình thường ở bệnh nhân hội chứng vành cấp nhưng cũng có thể bất thường trong chèn ép tim hoặc suy thất phải cấp tính.” |
| KN-DN-K21@TIM-MV | K | LY | Ấn đau thành ngực: gợi ý cơ xương khớp nhưng không loại trừ thiếu máu cơ tim | — | 4.7 | “Mặc dù ấn đau thành ngực giúp gợi ý các nguyên nhân về cơ xương khớp gây đau ngực nhưng không loại trừ hoàn toàn được thiếu máu cục bộ cơ tim.” |
| KN-DN-K25@TIM-MV | K | LY | Khám thực thể có thể bình thường ở hội chứng vành cấp | — | 4 | “khám thực thể có thể bình thường ở những bệnh nhân bị hội chứng vành cấp” |
| KN-DN-C01@TIM-MV | CLS | C | Điện tâm đồ: then chốt xác định thiếu máu cơ tim | — | 5.1 | “Điện tâm đồ đóng vai trò then chốt trong việc xác định bệnh nhân đau ngực do thiếu máu cục bộ cơ tim” |
| KN-DN-C02@TIM-MV | CLS | C | Điện tâm đồ: thời điểm làm và đo lặp lại khi nghi hội chứng vành cấp | — | 5.1 | “Điện tâm đồ cần thực hiện trong vòng 10 phút sau nhập viện và nên đo lặp lại mỗi 30-60 phút ở những bệnh nhân nghi ngờ hội chứng vành cấp.” |
| KN-DN-C03@TIM-MV | CLS | C | Điện tâm đồ: ST chênh xuống hoặc T âm sâu, đối xứng | — | 5.1 | “Hình ảnh đoạn ST chênh xuống hoặc T âm sâu, đối xứng trên điện tâm đồ giúp gợi ý thiếu máu cục bộ cơ tim.” |
| KN-DN-C11@TIM-MV | CLS | C | Siêu âm tim: rối loạn vận động vùng, chèn ép tim cấp | — | 5.3 | “siêu âm tim giúp phát hiện những rối loạn vận động vùng gợi ý đến thiếu máu tim cục bộ cấp tính hoặc chèn ép tim cấp trong tràn dịch màng ngoài tim ở bệnh nhân viêm màng ngoài tim” |
| KN-DN-C15@TIM-MV | CLS | C | CT động mạch vành: độ nhạy cao | — | 5.5 | “Chụp cắt lớp vi tính động mạch vành có độ nhạy cao trong phát hiện bệnh lý động mạch vành.” |
| KN-DN-C17@TIM-MV | CLS | C | MRI tim: nhồi máu cơ tim, bệnh cơ tim, bóc tách | — | 5.6 | “Chụp cộng hưởng từ tim có thể phát hiện sớm nhồi máu cơ tim, xác định chính xác vùng hoại tử cơ tim, chẩn đoán các dạng bệnh cơ tim.” “Chụp cộng hưởng từ cũng cho phép đánh giá chính xác bóc tách động mạch chủ.” |
| KN-DN-C19@TIM-MV | CLS | C | Men tim (troponin ưu tiên hơn CK-MB) | — | 5.7 | “Men tim cần được xét nghiệm ngay lúc nhập viện và lặp lại mỗi 3 – 6 giờ ở tất cả bệnh nhân nghi ngờ hội chứng vành cấp.” “troponin thường được sử dụng nhiều hơn CK-MB trong chẩn đoán nhồi máu cơ tim” |
| KN-DN-C04@TIM-MV | CLS | LY | Điện tâm đồ nghỉ có độ nhạy thấp | — | 5.1 | “độ nhạy của điện tâm đồ đo lúc nghỉ trong chẩn đoán thiếu máu cục bộ cơ tim chỉ đạt khoảng 20%” |
| KN-DN-C09@TIM-MV | CLS | LY | X quang ngực thường bình thường ở hội chứng vành cấp | — | 5.2 | “X quang ngực thường bình thường ở bệnh nhân hội chứng vành cấp nhưng cũng có thể thấy được hình ảnh phù phổi cấp.” |
| KN-DN-C13@TIM-MV | CLS | LY | Điện tâm đồ gắng sức: phân tầng nguy cơ bệnh động mạch vành | — | 5.4 | “Điện tâm đồ gắng sức thường được sử dụng để phân tầng nguy cơ mắc bệnh động mạch vành ở những bệnh nhân đánh giá ban đầu chưa tìm được nguyên nhân gây đau ngực và có nguy cơ thấp mắc hội chứng vành cấp.” |
| KN-DN-C14@TIM-MV | CLS | LY | Đau ngực đang tiến triển: chống chỉ định gắng sức | — | 5.4 | “Vì đau ngực đang tiến triển là chống chỉ định của nghiệm pháp gắng sức nên điện tâm đồ gắng sức thường được dùng để chẩn đoán bệnh lý động mạch vành mạn.” |
| KN-DN-C22@TIM-MV | CLS | LY | BNP hoặc NT-proBNP: vai trò tiên lượng | — | 5.7 | “BNP hoặc NT-proBNP có vai trò tiên lượng ở bệnh nhân hội chứng mạch vành cấp hoặc thuyên tắc phổi.” |

## TIM-MNT — Viêm màng ngoài tim
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B42@TIM-MNT | BS | C | Viêm màng ngoài tim cấp: bệnh cảnh điển hình | DN-02, DN-03, DN-05, DN-07 | 6.2 | “Bệnh nhân có biểu hiện nhiễm siêu vi trước đó, đau sau xương ức hoặc ngực trái, có thể lan lên vai trái, đau nhói hoặc đau kiểu màng phổi, giảm đau khi ngồi cúi người ra trước.” |
| KN-DN-P02-01@TIM-MNT | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Đau nhói” |
| KN-DN-P02-02@TIM-MNT | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Không liên quan gắng sức” |
| KN-DN-P02-03@TIM-MNT | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Không giảm khi nghỉ” |
| KN-DN-P02-04@TIM-MNT | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Không ảnh hưởng bởi nitrate” |
| KN-DN-P02-05@TIM-MNT | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Tăng khi nằm ngửa” |
| KN-DN-P02-06@TIM-MNT | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Tăng khi hít thở” |
| KN-DN-B03@TIM-MNT | BS | G | Đau khi ho, hít thở sâu (kiểu màng phổi) | DN-06 | 2.1 | “Đau ngực khi ho, khi hít thở sâu (đau ngực kiểu màng phổi) gợi ý các bệnh liên quan đến màng phổi như: viêm phổi, thuyên tắc phổi, viêm màng ngoài tim.” |
| KN-DN-B19@TIM-MNT | BS | G | Nặng hơn khi nằm ngửa, giảm khi ngồi cúi ra trước | DN-06, DN-07 | 2.4 | “Đau ngực trong viêm màng ngoài tim thường nặng hơn khi nằm ngửa và giảm đau khi ngồi cúi người ra phía trước.” |
| KN-DN-B04@TIM-MNT | BS | LY | Viêm màng ngoài tim/thuyên tắc phổi lớn có thể đau đè ép, khó phân biệt với đau thắt ngực | DN-05 | 2.1 | “Đau ngực trong viêm màng ngoài tim hoặc thuyên tắc phổi lớn đôi khi lại đau kiểu đè ép và rất khó phân biệt với đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-K27@TIM-MNT | K | C | Viêm màng ngoài tim: tiếng tim mờ, mạch nghịch khi chèn ép tim cấp | — | 6.2 | “Trong giai đoạn tràn dịch màng ngoài tim, có thể nghe tiếng tim mờ, có thể có mạch nghịch khi có chèn ép tim cấp.” |
| KN-DN-P02-07@TIM-MNT | K | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Có tiếng cọ màng tim hoặc màng phổi” |
| KN-DN-K03@TIM-MNT | K | G | Nhịp tim nhanh và tụt huyết áp: dấu hiệu huyết động quan trọng | — | 4.2 | “Nhịp tim nhanh và tụt huyết áp là những dấu hiệu về huyết động học quan trọng” “nhồi máu cơ tim với biến chứng choáng tim, thuyên tắc phổi diện rộng, viêm màng ngoài tim cấp với tràn dịch màng ngoài tim gây chèn ép tim cấp hoặc tràn khí màng phổi áp lực” |
| KN-DN-K15@TIM-MNT | K | G | Tiếng cọ màng ngoài tim | — | 4.4 | “Tiếng cọ màng ngoài tim gặp trong viêm màng ngoài tim giai đoạn đầu khi chưa có tràn dịch màng ngoài tim.” |
| KN-DN-C07@TIM-MNT | CLS | C | Điện tâm đồ phân biệt viêm màng ngoài tim với nhồi máu cơ tim | — | 5.1 | “ST chênh lên lan tỏa không theo giải phẫu mạch vành và đoạn PR chênh lõm xuống giúp phân biệt viêm màng ngoài tim với nhồi máu cơ tim cấp.” |
| KN-DN-C10@TIM-MNT | CLS | C | X quang ngực: trung thất dãn rộng, dấu Hampton/Westermark, vôi hóa màng ngoài tim | — | 5.2 | “trung thất dãn rộng trong bóc tách động mạch chủ, dấu hiệu Hampton hoặc Westermark trong thuyên tắc phổi, vôi hóa màng ngoài tim trong viêm màng ngoài tim mạn” |
| KN-DN-C11@TIM-MNT | CLS | C | Siêu âm tim: rối loạn vận động vùng, chèn ép tim cấp | — | 5.3 | “siêu âm tim giúp phát hiện những rối loạn vận động vùng gợi ý đến thiếu máu tim cục bộ cấp tính hoặc chèn ép tim cấp trong tràn dịch màng ngoài tim ở bệnh nhân viêm màng ngoài tim” |
| KN-DN-C16@TIM-MNT | CLS | C | CT giúp loại trừ bóc tách, tràn dịch màng ngoài tim, thuyên tắc phổi | — | 5.5 | “Chụp cắt lớp vi tính cũng giúp loại trừ bóc tách động mạch chủ, tràn dịch màng ngoài tim, thuyên tắc phổi.” |
| KN-DN-C05@TIM-MNT | CLS | LY | Bất thường ST, T không đặc hiệu, gặp ở nhiều bệnh cảnh | — | 5.1 | “Bất thường về ST, T có thể xảy ra trên nhiều bệnh cảnh khác nhau như: thuyên tắc phổi, phì đại thất trái, viêm màng ngoài tim, viêm cơ tim, rối loạn điện giải, rối loạn chuyển hóa.” “Tình trạng tăng thông khí trong rối loạn hoảng sợ có thể dẫn đến các bất thường về ST, T không đặc hiệu.” |

## TIM-VCT — Viêm cơ tim
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-C05@TIM-VCT | CLS | LY | Bất thường ST, T không đặc hiệu, gặp ở nhiều bệnh cảnh | — | 5.1 | “Bất thường về ST, T có thể xảy ra trên nhiều bệnh cảnh khác nhau như: thuyên tắc phổi, phì đại thất trái, viêm màng ngoài tim, viêm cơ tim, rối loạn điện giải, rối loạn chuyển hóa.” “Tình trạng tăng thông khí trong rối loạn hoảng sợ có thể dẫn đến các bất thường về ST, T không đặc hiệu.” |
| KN-DN-C20@TIM-VCT | CLS | LY | Men tim có thể tăng ngoài nhồi máu cơ tim | — | 5.7 | “men tim có thể tăng trong những bệnh cảnh khác gây tổn thương cơ tim ngoài nhồi máu cơ tim như: viêm cơ tim, suy thận mạn giai đoạn cuối, thuyên tắc phổi” |

## TIM-DMC — Bệnh lý động mạch chủ (vd bóc tách)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B43@TIM-DMC | BS | C | Bóc tách động mạch chủ: đau đột ngột, dữ dội ngay từ đầu, không giảm | DN-01, DN-04, DN-05 | 6.3 | “Bệnh nhân khởi phát đau đột ngột, dữ dội ngay từ đầu và kéo dài không giảm.” |
| KN-DN-B44@TIM-DMC | BS | C | Bóc tách đoạn lên đau trước ngực, đoạn xuống đau giữa hai xương bả vai | DN-02, DN-03 | 6.3 | “Bóc tách đoạn lên của động mạch chủ gây đau vùng trước ngực trong khi bóc tách đoạn xuống gây đau giữa hai xương bả vai.” |
| KN-DN-P07-01@TIM-DMC | BS | C | Bảng 3, bóc tách động mạch chủ (so với nhồi máu cơ tim) | — | Bảng 3 | “Đau lan sau lưng” |
| KN-DN-P07-02@TIM-DMC | BS | C | Bảng 3, bóc tách động mạch chủ (so với nhồi máu cơ tim) | — | Bảng 3 | “Khởi phát cấp tính” |
| KN-DN-P07-03@TIM-DMC | BS | C | Bảng 3, bóc tách động mạch chủ (so với nhồi máu cơ tim) | — | Bảng 3 | “Đau dữ dội, như xé” |
| KN-DN-B05@TIM-DMC | BS | G | Đau kiểu xé, như dao đâm | DN-05 | 2.1 | “Đau kiểu xé, như dao đâm thường gặp ở những bệnh nhân có bóc tách động mạch chủ cấp.” |
| KN-DN-B12@TIM-DMC | BS | G | Đau dữ dội lan sau lưng, giữa hai xương bả vai | DN-03 | 2.2 | “Đau ngực dữ dội lan ra sau lưng, đặc biệt giữa hai xương bả vai, nên nghĩ đến bóc tách động mạch chủ cấp.” |
| KN-DN-B14@TIM-DMC | BS | G | Cường độ đạt đỉnh ngay từ đầu | DN-01 | 2.3 | “đau ngực có cường độ đạt đỉnh ngay từ đầu thường gợi ý bóc tách động mạch chủ, thuyên tắc phổi, tràn khí màng phổi tự phát” |
| KN-DN-B30@TIM-DMC | BS | G | Ngất hoặc tiền ngất | DN-13 | 2.5 | “Sự xuất hiện của ngất hoặc tiền ngất cần nghĩ đến thuyên tắc phổi, bóc tách động mạch chủ, rối loạn nhịp do thiếu máu cục bộ cơ tim.” |
| KN-DN-B34@TIM-DMC | TC | G | Tiền căn tăng huyết áp hoặc bệnh mô liên kết (Marfan) | DN-20 | 6.3 | “Tiền căn tăng huyết áp hoặc bệnh lý mô liên kết như hội chứng Marfan làm tăng nguy cơ bóc tách động mạch chủ.” |
| KN-DN-K28@TIM-DMC | K | C | Bóc tách: tăng huyết áp, hở van động mạch chủ, mất mạch ngoại biên | — | 6.3 | “Khám thực thể có thể thấy tăng huyết áp, âm thổi của hở van động mạch chủ, mất mạch ngoại biên.” |
| KN-DN-K04@TIM-DMC | K | G | Bóc tách: tăng huyết áp nặng, có thể tụt huyết áp | — | 4.2 | “Bóc tách động mạch chủ cấp thường đi kèm tình trạng tăng huyết áp nặng nhưng cũng có thể tụt huyết áp khi có tổn thương động mạch vành hoặc bóc tách vào khoang màng ngoài tim.” |
| KN-DN-K13@TIM-DMC | K | G | Âm thổi hở van động mạch chủ | — | 4.4 | “Âm thổi của hở van động mạch chủ có thể là biến chứng của bóc tách động mạch chủ đoạn lên.” |
| KN-DN-K18@TIM-DMC | K | G | Mất mạch, tím (đặc biệt chi trên) | — | 4.6 | “Biểu hiện của tình trạng thiếu máu nuôi chi cấp tính là mất mạch và tím, đặc biệt là chi trên, có thể gợi ý bóc tách động mạch chủ.” |
| KN-DN-C10@TIM-DMC | CLS | C | X quang ngực: trung thất dãn rộng, dấu Hampton/Westermark, vôi hóa màng ngoài tim | — | 5.2 | “trung thất dãn rộng trong bóc tách động mạch chủ, dấu hiệu Hampton hoặc Westermark trong thuyên tắc phổi, vôi hóa màng ngoài tim trong viêm màng ngoài tim mạn” |
| KN-DN-C16@TIM-DMC | CLS | C | CT giúp loại trừ bóc tách, tràn dịch màng ngoài tim, thuyên tắc phổi | — | 5.5 | “Chụp cắt lớp vi tính cũng giúp loại trừ bóc tách động mạch chủ, tràn dịch màng ngoài tim, thuyên tắc phổi.” |
| KN-DN-C17@TIM-DMC | CLS | C | MRI tim: nhồi máu cơ tim, bệnh cơ tim, bóc tách | — | 5.6 | “Chụp cộng hưởng từ tim có thể phát hiện sớm nhồi máu cơ tim, xác định chính xác vùng hoại tử cơ tim, chẩn đoán các dạng bệnh cơ tim.” “Chụp cộng hưởng từ cũng cho phép đánh giá chính xác bóc tách động mạch chủ.” |
| KN-DN-C12@TIM-DMC | CLS | LY | Siêu âm tim qua thành ngực: độ nhạy thấp với bóc tách | — | 5.3 | “Siêu âm tim qua thành ngực có thể phát hiện dấu hiệu bóc tách động mạch chủ nhưng có độ nhạy thấp.” |

## PHOI-TTP — Thuyên tắc phổi
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B45@PHOI-TTP | BS | C | Thuyên tắc phổi: đau màng phổi đột ngột, thường một bên, kèm khó thở, có thể ho ra máu | DN-01, DN-02, DN-06, DN-11, DN-16 | 6.4 | “Đau ngực kiểu màng phổi khởi phát đột ngột, có thể đau kiểu đè ép trong thuyên tắc phổi diện rộng, thường đau một bên ngực, có thể đau sau xương ức, kèm khó thở.” “Bệnh nhân có thể ho ra máu, vã mồ hôi.” |
| KN-DN-B03@PHOI-TTP | BS | G | Đau khi ho, hít thở sâu (kiểu màng phổi) | DN-06 | 2.1 | “Đau ngực khi ho, khi hít thở sâu (đau ngực kiểu màng phổi) gợi ý các bệnh liên quan đến màng phổi như: viêm phổi, thuyên tắc phổi, viêm màng ngoài tim.” |
| KN-DN-B14@PHOI-TTP | BS | G | Cường độ đạt đỉnh ngay từ đầu | DN-01 | 2.3 | “đau ngực có cường độ đạt đỉnh ngay từ đầu thường gợi ý bóc tách động mạch chủ, thuyên tắc phổi, tràn khí màng phổi tự phát” |
| KN-DN-B27@PHOI-TTP | BS | G | Suy hô hấp khởi phát đột ngột | DN-11 | 2.5 | “Suy hô hấp khởi phát đột ngột cần nghĩ đến thuyên tắc phổi, tràn khí màng phổi tự phát.” |
| KN-DN-B28@PHOI-TTP | BS | G | Ho ra máu | DN-16 | 2.5 | “Ho ra máu có thể xảy ra ở bệnh nhân thuyên tắc phổi” |
| KN-DN-B30@PHOI-TTP | BS | G | Ngất hoặc tiền ngất | DN-13 | 2.5 | “Sự xuất hiện của ngất hoặc tiền ngất cần nghĩ đến thuyên tắc phổi, bóc tách động mạch chủ, rối loạn nhịp do thiếu máu cục bộ cơ tim.” |
| KN-DN-B04@PHOI-TTP | BS | LY | Viêm màng ngoài tim/thuyên tắc phổi lớn có thể đau đè ép, khó phân biệt với đau thắt ngực | DN-05 | 2.1 | “Đau ngực trong viêm màng ngoài tim hoặc thuyên tắc phổi lớn đôi khi lại đau kiểu đè ép và rất khó phân biệt với đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-B33@PHOI-TTP | TC | G | Tiền căn: yếu tố nguy cơ thuyên tắc huyết khối tĩnh mạch [mã suy ra: sách ghi "thuyên tắc huyết khối tĩnh mạch"] | DN-21, DN-30 | 3 | “các yếu tố nguy cơ của thuyên tắc huyết khối tĩnh mạch (ung thư, bất động, nằm lâu, hậu phẫu...)” |
| KN-DN-K29@PHOI-TTP | K | C | Thuyên tắc phổi: thở nhanh nông, nhịp nhanh, tím tái, tụt huyết áp | — | 6.4 | “Khám thực thể có thể thấy thở nhanh nông, nhịp tim nhanh, tím tái, tụt huyết áp.” |
| KN-DN-K03@PHOI-TTP | K | G | Nhịp tim nhanh và tụt huyết áp: dấu hiệu huyết động quan trọng | — | 4.2 | “Nhịp tim nhanh và tụt huyết áp là những dấu hiệu về huyết động học quan trọng” “nhồi máu cơ tim với biến chứng choáng tim, thuyên tắc phổi diện rộng, viêm màng ngoài tim cấp với tràn dịch màng ngoài tim gây chèn ép tim cấp hoặc tràn khí màng phổi áp lực” |
| KN-DN-K05@PHOI-TTP | K | G | Nhịp nhanh xoang | — | 4.2 | “Nhịp nhanh xoang là biểu hiện quan trọng của thuyên tắc phổi diện rộng.” |
| KN-DN-K19@PHOI-TTP | K | G | Sưng phù chỉ một bên chi dưới [mã suy ra: sách ghi "thuyên tắc huyết khối tĩnh mạch"] | — | 4.6 | “Sưng phù chỉ ở một bên chi dưới giúp hướng đến thuyên tắc huyết khối tĩnh mạch.” |
| KN-DN-K07@PHOI-TTP | K | LY | Sốt nhẹ: không đặc hiệu | — | 4.2 | “Sốt nhẹ không phải là dấu hiệu đặc hiệu vì có thể gặp trong nhồi máu cơ tim hoặc thuyên tắc huyết khối kèm nhiễm trùng.” |
| KN-DN-C06@PHOI-TTP | CLS | C | Điện tâm đồ trong thuyên tắc phổi | — | 5.1 | “Thuyên tắc phổi thường có biểu hiện nhịp nhanh xoang, có thể có trục lệch phải, sóng S ở chuyển đạo DI, sóng Q và T ở chuyển đạo DIII.” |
| KN-DN-C10@PHOI-TTP | CLS | C | X quang ngực: trung thất dãn rộng, dấu Hampton/Westermark, vôi hóa màng ngoài tim | — | 5.2 | “trung thất dãn rộng trong bóc tách động mạch chủ, dấu hiệu Hampton hoặc Westermark trong thuyên tắc phổi, vôi hóa màng ngoài tim trong viêm màng ngoài tim mạn” |
| KN-DN-C16@PHOI-TTP | CLS | C | CT giúp loại trừ bóc tách, tràn dịch màng ngoài tim, thuyên tắc phổi | — | 5.5 | “Chụp cắt lớp vi tính cũng giúp loại trừ bóc tách động mạch chủ, tràn dịch màng ngoài tim, thuyên tắc phổi.” |
| KN-DN-C21@PHOI-TTP | CLS | C | D-dimer | — | 5.7 | “D-dimer tăng gợi ý đến thuyên tắc phổi. D-dimer bình thường giúp loại trừ thuyên tắc phổi.” |
| KN-DN-C05@PHOI-TTP | CLS | LY | Bất thường ST, T không đặc hiệu, gặp ở nhiều bệnh cảnh | — | 5.1 | “Bất thường về ST, T có thể xảy ra trên nhiều bệnh cảnh khác nhau như: thuyên tắc phổi, phì đại thất trái, viêm màng ngoài tim, viêm cơ tim, rối loạn điện giải, rối loạn chuyển hóa.” “Tình trạng tăng thông khí trong rối loạn hoảng sợ có thể dẫn đến các bất thường về ST, T không đặc hiệu.” |
| KN-DN-C20@PHOI-TTP | CLS | LY | Men tim có thể tăng ngoài nhồi máu cơ tim | — | 5.7 | “men tim có thể tăng trong những bệnh cảnh khác gây tổn thương cơ tim ngoài nhồi máu cơ tim như: viêm cơ tim, suy thận mạn giai đoạn cuối, thuyên tắc phổi” |
| KN-DN-C22@PHOI-TTP | CLS | LY | BNP hoặc NT-proBNP: vai trò tiên lượng | — | 5.7 | “BNP hoặc NT-proBNP có vai trò tiên lượng ở bệnh nhân hội chứng mạch vành cấp hoặc thuyên tắc phổi.” |

## PHOI-TAP — Tăng áp động mạch phổi
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B46@PHOI-TAP | BS | C | Tăng áp động mạch phổi: đè ép dưới xương ức, khi gắng sức, kèm khó thở | DN-01, DN-02, DN-05, DN-11 | 6.5 | “Đau ngực dưới xương ức kiểu đè ép, thường khởi phát khi gắng sức, kèm khó thở.” |
| KN-DN-K30@PHOI-TAP | K | C | Tăng áp động mạch phổi: dấu hiệu suy tim phải | — | 6.5 | “Khám có thể thấy các dấu hiệu của suy tim phải.” |

## PHOI-MP — Bệnh màng phổi (vd lao màng phổi)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B47@PHOI-MP | BS | C | Viêm phổi, màng phổi: đau màng phổi một bên, khó thở, ho, sốt | DN-06, DN-11, DN-14, DN-15 | 6.6 | “Đau ngực kiểu màng phổi, đau một bên kèm theo khó thở, ho, sốt.” |
| KN-DN-P02-01@PHOI-MP | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Đau nhói” |
| KN-DN-P02-02@PHOI-MP | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Không liên quan gắng sức” |
| KN-DN-P02-03@PHOI-MP | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Không giảm khi nghỉ” |
| KN-DN-P02-04@PHOI-MP | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Không ảnh hưởng bởi nitrate” |
| KN-DN-P02-05@PHOI-MP | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Tăng khi nằm ngửa” |
| KN-DN-P02-06@PHOI-MP | BS | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Tăng khi hít thở” |
| KN-DN-K31@PHOI-MP | K | C | Viêm phổi, màng phổi: ran nổ, tiếng cọ màng phổi | — | 6.6 | “Khám phổi ghi nhận có ran nổ, có thể có tiếng cọ màng phổi.” |
| KN-DN-P02-07@PHOI-MP | K | C | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | — | Bảng 2 | “Có tiếng cọ màng tim hoặc màng phổi” |

## PHOI-VP — Viêm phổi
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B47@PHOI-VP | BS | C | Viêm phổi, màng phổi: đau màng phổi một bên, khó thở, ho, sốt | DN-06, DN-11, DN-14, DN-15 | 6.6 | “Đau ngực kiểu màng phổi, đau một bên kèm theo khó thở, ho, sốt.” |
| KN-DN-B03@PHOI-VP | BS | G | Đau khi ho, hít thở sâu (kiểu màng phổi) | DN-06 | 2.1 | “Đau ngực khi ho, khi hít thở sâu (đau ngực kiểu màng phổi) gợi ý các bệnh liên quan đến màng phổi như: viêm phổi, thuyên tắc phổi, viêm màng ngoài tim.” |
| KN-DN-K31@PHOI-VP | K | C | Viêm phổi, màng phổi: ran nổ, tiếng cọ màng phổi | — | 6.6 | “Khám phổi ghi nhận có ran nổ, có thể có tiếng cọ màng phổi.” |
| KN-DN-K08@PHOI-VP | K | G | Khám phổi tìm nguyên nhân về phổi | — | 4.3 | “Khám phổi giúp xác định các nguyên nhân đau ngực liên quan đến phổi như: viêm phổi, tràn khí màng phổi.” |
| KN-DN-C08@PHOI-VP | CLS | C | X quang ngực: phát hiện bất thường về phổi | — | 5.2 | “X quang ngực đóng vai trò quan trọng trong việc phát hiện các bất thường về phổi như viêm phổi, áp-xe phổi, tràn khí màng phổi hay u phổi.” |

## PHOI-KPQ — Viêm khí phế quản
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|

## PHOI-TKMP — Tràn khí màng phổi
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B48@PHOI-TKMP | BS | C | Tràn khí màng phổi: đau màng phổi một bên, khởi phát đột ngột, khó thở | DN-01, DN-06, DN-11 | 6.7 | “Đau ngực kiểu màng phổi một bên khởi phát đột ngột kèm khó thở.” |
| KN-DN-B14@PHOI-TKMP | BS | G | Cường độ đạt đỉnh ngay từ đầu | DN-01 | 2.3 | “đau ngực có cường độ đạt đỉnh ngay từ đầu thường gợi ý bóc tách động mạch chủ, thuyên tắc phổi, tràn khí màng phổi tự phát” |
| KN-DN-B27@PHOI-TKMP | BS | G | Suy hô hấp khởi phát đột ngột | DN-11 | 2.5 | “Suy hô hấp khởi phát đột ngột cần nghĩ đến thuyên tắc phổi, tràn khí màng phổi tự phát.” |
| KN-DN-K32@PHOI-TKMP | K | C | Tràn khí màng phổi: âm phế bào giảm | — | 6.7 | “Khám thấy âm phế bào giảm ở bên có tràn khí màng phổi.” |
| KN-DN-K02@PHOI-TKMP | K | G | Thể trạng: nam trẻ, cao, gầy (Marfan) với tràn khí màng phổi | — | 4.1 | “Bệnh nhân hội chứng Marfan thường là nam giới, trẻ tuổi, cao, gầy với tràn khí màng phổi tự phát.” |
| KN-DN-K03@PHOI-TKMP | K | G | Nhịp tim nhanh và tụt huyết áp: dấu hiệu huyết động quan trọng | — | 4.2 | “Nhịp tim nhanh và tụt huyết áp là những dấu hiệu về huyết động học quan trọng” “nhồi máu cơ tim với biến chứng choáng tim, thuyên tắc phổi diện rộng, viêm màng ngoài tim cấp với tràn dịch màng ngoài tim gây chèn ép tim cấp hoặc tràn khí màng phổi áp lực” |
| KN-DN-K08@PHOI-TKMP | K | G | Khám phổi tìm nguyên nhân về phổi | — | 4.3 | “Khám phổi giúp xác định các nguyên nhân đau ngực liên quan đến phổi như: viêm phổi, tràn khí màng phổi.” |
| KN-DN-C08@PHOI-TKMP | CLS | C | X quang ngực: phát hiện bất thường về phổi | — | 5.2 | “X quang ngực đóng vai trò quan trọng trong việc phát hiện các bất thường về phổi như viêm phổi, áp-xe phổi, tràn khí màng phổi hay u phổi.” |

## PHOI-UNG — Ung thư phổi
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|

## TH-GERD — Trào ngược dạ dày–thực quản
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B50@TH-GERD | BS | C | Trào ngược dạ dày-thực quản: nóng rát, sau ăn, nằm ngửa, ợ hơi, ợ chua, khó tiêu | DN-01, DN-02, DN-05, DN-06, DN-07, DN-17 | 6.9 | “đau sau xương ức hoặc thượng vị kiểu nóng rát, xảy ra sau khi ăn và khi nằm ngửa, kèm ợ hơi, ợ chua, khó tiêu” “giảm đau khi sử dụng antacid hoặc nitroglycerin (nếu có co thắt thực quản)” |
| KN-DN-P03-01@TH-GERD | BS | C | Bảng 2, cột Trào ngược dạ dày thực quản | — | Bảng 2 | “Đau nóng rát” |
| KN-DN-P03-02@TH-GERD | BS | C | Bảng 2, cột Trào ngược dạ dày thực quản | — | Bảng 2 | “Không liên quan gắng sức” |
| KN-DN-P03-03@TH-GERD | BS | C | Bảng 2, cột Trào ngược dạ dày thực quản | — | Bảng 2 | “Không giảm khi nghỉ” |
| KN-DN-P03-04@TH-GERD | BS | C | Bảng 2, cột Trào ngược dạ dày thực quản | — | Bảng 2 | “Không ảnh hưởng bởi nitrate (trừ khi kèm co thắt thực quản)” |
| KN-DN-P03-05@TH-GERD | BS | C | Bảng 2, cột Trào ngược dạ dày thực quản | — | Bảng 2 | “Có thể khởi phát khi nằm ngửa” |
| KN-DN-P03-06@TH-GERD | BS | C | Bảng 2, cột Trào ngược dạ dày thực quản | — | Bảng 2 | “Không ảnh hưởng bởi hô hấp” |
| KN-DN-B06@TH-GERD | BS | G | Đau kiểu nóng rát | DN-05 | 2.1 | “Đau kiểu nóng rát gợi ý bệnh trào ngược dạ dày-thực quản nhưng cũng có thể xảy ra ở bệnh nhân thiếu máu cục bộ cơ tim.” |
| KN-DN-B10@TH-GERD | BS | G | Bệnh thực quản: đau sau xương ức | DN-02 | 2.2 | “Đau ngực do bệnh thực quản thường đau sau xương ức” |
| KN-DN-B16@TH-GERD | BS | G | Đau vào sáng sớm | DN-01 | 2.3 | “Đau ngực do bệnh trào ngược dạ dày-thực quản thường xảy ra vào sáng sớm” |
| KN-DN-B22@TH-GERD | BS | G | Khởi phát do rượu, một số thức ăn, nằm ngửa | DN-01, DN-06 | 2.4 | “Đau do bệnh trào ngược dạ dày-thực quản có thể khởi phát do rượu, một số loại thức ăn hoặc tư thế nằm ngửa.” |
| KN-DN-B23@TH-GERD | BS | G | Giảm khi dùng thuốc giảm tiết acid, thường không liên quan gắng sức | DN-06, DN-07 | 2.4 | “Đau ngực do bệnh trào ngược dạ dày-thực quản hoặc loét dạ dày thường giảm khi dùng thuốc giảm tiết acid dạ dày và thường không liên quan đến gắng sức.” |

## TH-LOET — Viêm loét dạ dày – tá tràng
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B49@TH-LOET | BS | C | Loét dạ dày - tá tràng: nóng rát, liên quan bữa ăn, giảm khi ăn hoặc antacid | DN-01, DN-02, DN-05, DN-07 | 6.8 | “Đau thượng vị hoặc sau xương ức kiểu nóng rát, liên quan đến bữa ăn, giảm đau khi ăn hoặc dùng antacid.” |
| KN-DN-B11@TH-LOET | BS | G | Bệnh tiêu hóa khác: đau nhiều nhất ở bụng/thượng vị lan lên ngực [mã suy ra: sách ghi chung "bệnh lý tiêu hóa khác"] | DN-02 | 2.2 | “các bệnh lý tiêu hóa khác lại thường đau nhiều nhất ở bụng hoặc thượng vị lan lên ngực” |
| KN-DN-B20@TH-LOET | BS | G | Đau khởi phát do ăn uống | DN-01 | 2.4 | “Đau khởi phát do ăn uống thường do các nguyên nhân tiêu hóa như loét dạ dày, viêm túi mật, viêm tụy.” |
| KN-DN-B23@TH-LOET | BS | G | Giảm khi dùng thuốc giảm tiết acid, thường không liên quan gắng sức | DN-06, DN-07 | 2.4 | “Đau ngực do bệnh trào ngược dạ dày-thực quản hoặc loét dạ dày thường giảm khi dùng thuốc giảm tiết acid dạ dày và thường không liên quan đến gắng sức.” |
| KN-DN-K16@TH-LOET | K | G | Bụng: xác định điểm đau [mã suy ra: sách ghi chung "nguyên nhân về tiêu hóa"] | — | 4.5 | “Xác định được điểm đau khi khám bụng giúp hướng đến các nguyên nhân về tiêu hóa gây đau ngực.” |

## TH-TUIMAT — Bệnh túi mật
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B51@TH-TUIMAT | BS | C | Bệnh túi mật: đau quặn thượng vị hoặc hạ sườn phải sau ăn | DN-01, DN-02, DN-05 | 6.10 | “Thường đau quặn bụng vùng thượng vị hoặc hạ sườn phải xảy ra sau ăn.” |
| KN-DN-B11@TH-TUIMAT | BS | G | Bệnh tiêu hóa khác: đau nhiều nhất ở bụng/thượng vị lan lên ngực [mã suy ra: sách ghi chung "bệnh lý tiêu hóa khác"] | DN-02 | 2.2 | “các bệnh lý tiêu hóa khác lại thường đau nhiều nhất ở bụng hoặc thượng vị lan lên ngực” |
| KN-DN-B20@TH-TUIMAT | BS | G | Đau khởi phát do ăn uống | DN-01 | 2.4 | “Đau khởi phát do ăn uống thường do các nguyên nhân tiêu hóa như loét dạ dày, viêm túi mật, viêm tụy.” |
| KN-DN-K16@TH-TUIMAT | K | G | Bụng: xác định điểm đau [mã suy ra: sách ghi chung "nguyên nhân về tiêu hóa"] | — | 4.5 | “Xác định được điểm đau khi khám bụng giúp hướng đến các nguyên nhân về tiêu hóa gây đau ngực.” |

## TH-TUY — Viêm tụy
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B11@TH-TUY | BS | G | Bệnh tiêu hóa khác: đau nhiều nhất ở bụng/thượng vị lan lên ngực [mã suy ra: sách ghi chung "bệnh lý tiêu hóa khác"] | DN-02 | 2.2 | “các bệnh lý tiêu hóa khác lại thường đau nhiều nhất ở bụng hoặc thượng vị lan lên ngực” |
| KN-DN-B20@TH-TUY | BS | G | Đau khởi phát do ăn uống | DN-01 | 2.4 | “Đau khởi phát do ăn uống thường do các nguyên nhân tiêu hóa như loét dạ dày, viêm túi mật, viêm tụy.” |
| KN-DN-K16@TH-TUY | K | G | Bụng: xác định điểm đau [mã suy ra: sách ghi chung "nguyên nhân về tiêu hóa"] | — | 4.5 | “Xác định được điểm đau khi khám bụng giúp hướng đến các nguyên nhân về tiêu hóa gây đau ngực.” |

## TT-THANH — Đau thành ngực (cơ–xương–sụn)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B52@TT-THANH | BS | C | Đau thành ngực: đau nhói, khu trú, tăng khi ấn, ho, hít thở, cử động | DN-02, DN-05, DN-06, DN-18 | 6.11 | “Thường đau nhói, khu trú tại một vùng nhỏ trên thành ngực, đau tăng khi ấn vào, khi ho, hít thở hoặc cử động.” |
| KN-DN-P09-01@TT-THANH | BS | C | Bảng 3, đau thành ngực (so với thiếu máu cục bộ cơ tim) | — | Bảng 3 | “Liên quan đến tư thế” |
| KN-DN-P09-02@TT-THANH | BS | C | Bảng 3, đau thành ngực (so với thiếu máu cục bộ cơ tim) | — | Bảng 3 | “Thường đau nhiều hơn khi nghỉ” |
| KN-DN-P09-03@TT-THANH | BS | C | Bảng 3, đau thành ngực (so với thiếu máu cục bộ cơ tim) | — | Bảng 3 | “Đau kéo dài liên tục” |
| KN-DN-P09-04@TT-THANH | BS | C | Bảng 3, đau thành ngực (so với thiếu máu cục bộ cơ tim) | — | Bảng 3 | “Đau khu trú” |
| KN-DN-B18@TT-THANH | BS | G | Cường độ đổi theo tư thế hoặc cử động chi trên, cổ [mã suy ra: sách ghi chung "cơ xương khớp"] | DN-06 | 2.4 | “Đau ngực có cường độ thay đổi liên quan đến tư thế hoặc cử động chi trên và cổ thường gợi ý đến các nguyên nhân về cơ xương khớp, ít khi do thiếu máu cục bộ cơ tim.” |
| KN-DN-P09-05@TT-THANH | K | C | Bảng 3, đau thành ngực (so với thiếu máu cục bộ cơ tim) | — | Bảng 3 | “Có điểm đau thành ngực” |
| KN-DN-K20@TT-THANH | K | G | Sưng, đỏ, đau khu trú tại khớp sụn sườn, sụn ức | — | 4.7 | “Khám cơ xương khớp có thể phát hiện sưng, đỏ, đau khu trú tại các khớp sụn sườn, sụn ức.” |
| KN-DN-K21@TT-THANH | K | G | Ấn đau thành ngực: gợi ý cơ xương khớp nhưng không loại trừ thiếu máu cơ tim | — | 4.7 | “Mặc dù ấn đau thành ngực giúp gợi ý các nguyên nhân về cơ xương khớp gây đau ngực nhưng không loại trừ hoàn toàn được thiếu máu cục bộ cơ tim.” |

## TT-DIADEM — Bệnh đĩa đệm cột sống cổ
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B18@TT-DIADEM | BS | G | Cường độ đổi theo tư thế hoặc cử động chi trên, cổ [mã suy ra: sách ghi chung "cơ xương khớp"] | DN-06 | 2.4 | “Đau ngực có cường độ thay đổi liên quan đến tư thế hoặc cử động chi trên và cổ thường gợi ý đến các nguyên nhân về cơ xương khớp, ít khi do thiếu máu cục bộ cơ tim.” |
| KN-DN-K22@TT-DIADEM | K | G | Giảm cảm giác ở chi trên | — | 4.7 | “Giảm cảm giác ở chi trên có thể nghĩ đến bệnh lý liên quan đĩa đệm cột sống cổ.” |

## TT-HZ — Herpes Zoster
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B53@TT-HZ | BS | C | Herpes zoster: tăng cảm, đau theo khoanh da, bóng nước | DN-19 | 6.11 | “Viêm dây thần kinh liên sườn do Herpes zoster gây tăng cảm và đau theo khoanh da, lan theo rễ thần kinh, xuất hiện bóng nước tại chỗ viêm.” |
| KN-DN-K23@TT-HZ | K | G | Sang thương da vùng ngực (Herpes zoster, viêm da) | — | 4.8 | “Bệnh nhân đau ngực có thể có sang thương Herpes zoster hay sang thương viêm da có thể giúp gợi ý nguyên nhân đau ngực.” |

## TAMLY — Nguyên nhân tâm lý (rối loạn hoảng sợ, lo âu)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B54@TAMLY | BS | C | Tâm lý: nữ dưới 40 tuổi, lo lắng, ê ẩm kéo dài hàng giờ, mệt, hồi hộp, khó thở | DN-04, DN-31 | 6.12 | “Thường gặp ở bệnh nhân nữ dưới 40 tuổi, có tình trạng lo lắng căng thẳng, tiền căn trầm cảm hoặc cơn hoảng loạn.” “Cảm giác ê ẩm vùng mỏm tim hoặc sau xương ức kéo dài hàng giờ” “Bệnh nhân còn cảm thấy mệt, hồi hộp, khó thở, thở nhanh, chóng mặt, tê đầu chi.” |
| KN-DN-C05@TAMLY | CLS | LY | Bất thường ST, T không đặc hiệu, gặp ở nhiều bệnh cảnh | — | 5.1 | “Bất thường về ST, T có thể xảy ra trên nhiều bệnh cảnh khác nhau như: thuyên tắc phổi, phì đại thất trái, viêm màng ngoài tim, viêm cơ tim, rối loạn điện giải, rối loạn chuyển hóa.” “Tình trạng tăng thông khí trong rối loạn hoảng sợ có thể dẫn đến các bất thường về ST, T không đặc hiệu.” |

## Nguyên nhân hoặc bệnh nền được nhắc ngoài Bảng 1
Các khối dưới đây gồm những bệnh sách nhắc trong lúc mô tả dấu hiệu, không nằm trong Bảng 1.

## TH-TQ — Co thắt thực quản
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B10@TH-TQ | BS | G | Bệnh thực quản: đau sau xương ức | DN-02 | 2.2 | “Đau ngực do bệnh thực quản thường đau sau xương ức” |
| KN-DN-B24@TH-TQ | BS | LY | Giảm trong vài phút khi dùng nitroglycerin | DN-07 | 2.4 | “Đau ngực giảm trong vòng vài phút khi dùng nitroglycerin gợi ý thiếu máu cục bộ cơ tim, tuy nhiên cũng có thể gặp trong co thắt thực quản.” |

## TIM-ST — Suy tim
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B29@TIM-ST | BS | G | Ho khạc đàm bọt hồng | DN-15 | 2.5 | “ho khạc đàm bọt hồng thường gặp trong suy tim nặng” |
| KN-DN-K11@TIM-ST | K | G | Tiếng T3, T4 | — | 4.4 | “Khám tim có thể nghe được tiếng T3, T4 trong suy tim.” |
| KN-DN-K17@TIM-ST | K | G | Gan to do sung huyết [mã suy ra: sách ghi "suy thất phải nặng"] | — | 4.5 | “có thể khám thấy gan to do sung huyết” |

## TIM-VAN — Bệnh van tim (vd hẹp van 2 lá)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-K14@TIM-VAN | K | G | Âm thổi gợi ý bệnh tim nền (hẹp van động mạch chủ, bệnh cơ tim phì đại) | — | 4.4 | “Các âm thổi khác giúp gợi ý bệnh tim nền làm nặng thêm tình trạng thiếu máu cục bộ cơ tim như hẹp van động mạch chủ, bệnh cơ tim phì đại...” |

## TIM-BCT — Bệnh cơ tim (vd bệnh cơ tim phì đại)
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-K14@TIM-BCT | K | G | Âm thổi gợi ý bệnh tim nền (hẹp van động mạch chủ, bệnh cơ tim phì đại) | — | 4.4 | “Các âm thổi khác giúp gợi ý bệnh tim nền làm nặng thêm tình trạng thiếu máu cục bộ cơ tim như hẹp van động mạch chủ, bệnh cơ tim phì đại...” |
| KN-DN-C17@TIM-BCT | CLS | C | MRI tim: nhồi máu cơ tim, bệnh cơ tim, bóc tách | — | 5.6 | “Chụp cộng hưởng từ tim có thể phát hiện sớm nhồi máu cơ tim, xác định chính xác vùng hoại tử cơ tim, chẩn đoán các dạng bệnh cơ tim.” “Chụp cộng hưởng từ cũng cho phép đánh giá chính xác bóc tách động mạch chủ.” |

## THAN-PHU — Suy thận mạn / phù – thận
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-C20@THAN-PHU | CLS | LY | Men tim có thể tăng ngoài nhồi máu cơ tim | — | 5.7 | “men tim có thể tăng trong những bệnh cảnh khác gây tổn thương cơ tim ngoài nhồi máu cơ tim như: viêm cơ tim, suy thận mạn giai đoạn cuối, thuyên tắc phổi” |

## (Chưa gắn nguyên nhân) Dấu hiệu sách nói chung, không nêu nguyên nhân cụ thể
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-DN-B26@KHAC | BS | LY | Khó thở không giúp phân biệt nhưng gợi ý nguyên nhân tim phổi | DN-11 | 2.5 | “Khó thở có thể gặp trong nhiều bệnh cảnh khác nhau gây đau ngực nên không giúp chẩn đoán phân biệt, tuy nhiên khó thở là dấu hiệu gợi ý các nguyên nhân đau ngực do bệnh tim phổi.” |
| KN-DN-K06@KHAC | K | LY | Nhịp tim nhanh và giảm oxy | — | 4.2 | “Nhịp tim nhanh và giảm oxy gợi ý nguyên nhân về phổi.” |
| KN-DN-C18@KHAC | CLS | LY | Tổng phân tích tế bào máu | — | 5.7 | “Tổng phân tích tế bào máu cần thực hiện ngay lúc nhập viện.” “Tăng bạch cầu đa nhân trung tính hay bạch cầu lympho có thể gợi ý các nguyên nhân viêm nhiễm.” |

## Phụ lục: Sơ đồ tiếp cận của sách (mục 7)
| ID | Nhóm | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-DN-S01 | Do tim, thiếu máu cục bộ cơ tim | +TIM-MV | 7 | “Thiếu máu cục bộ cơ tim --> Hội chứng vành cấp, Cơn đau thắt ngực ổn định” |
| KN-DN-S02 | Do tim, không thiếu máu cục bộ cơ tim | +TIM-MNT, +TIM-VCT | 7 | “Không thiếu máu cục bộ cơ tim --> Viêm màng ngoài tim, Viêm cơ tim” |
| KN-DN-S03 | Không do tim, mạch máu | +TIM-DMC, +PHOI-TTP | 7 | “Mạch máu --> Bóc tách động mạch chủ, Thuyên tắc phổi” |
| KN-DN-S04 | Không do tim, phổi | +PHOI-VP, +PHOI-MP, +PHOI-TKMP | 7 | “Phổi --> Viêm phổi, Viêm màng phổi, Tràn khí màng phổi” |
| KN-DN-S05 | Không do tim, nhóm khác | — | 7 | “Khác --> Dạ dày – ruột, Thần kinh, cơ xương khớp, Tâm lý” |

## Bộ tiêu chuẩn / thang điểm (chưa có nguồn)
Bài 1 không có bộ tiêu chuẩn có quy tắc điểm (ví dụ Wells cho thuyên tắc phổi, Framingham cho suy tim). Khi bạn đưa nguồn, thêm mỗi bộ vào bảng này: mỗi tiêu chí là một dòng gắn Nguồn dữ kiện (BS/TC/K/CLS) và điểm, kèm quy tắc kết luận và trích nguyên văn.

| ID | Bộ tiêu chuẩn | Tiêu chí | Nguồn dữ kiện | Điểm | Quy tắc kết luận | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|---|

