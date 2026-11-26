---
trieu_chung: Đau ngực
tien_to_id: DN
nguon: Bài 1. Tiếp cận bệnh nhân đau ngực — ThS.BS. Nguyễn Đình Quốc Anh, TS.BS. Hoàng Văn Sỹ
trang_thai: NHAP   # chỉ người dùng được đổi thành DA_RA_SOAT
nguoi_tao: Claude (trích từ văn bản chương do người dùng cung cấp)
---

# Kiến thức đau ngực (từ Bài 1 Tiếp cận bệnh nhân đau ngực)

## Quy ước
- Cột "Trích nguyên văn" chép y nguyên từ sách, trong “ ”; nhiều trích dẫn đặt liền nhau, mỗi cái trong “ ”. Đã kiểm tra bằng tools/kiem_tra_kien_thuc.py.
- Mã nguyên nhân: `+` sách gợi ý/điển hình/giúp xác định; `-` sách nói hiếm/ít khi; `~` có thể gặp/không đặc hiệu/không loại trừ; "—" sách không nêu nguyên nhân cụ thể.
- "[mã suy ra]" nghĩa là sách nói chung chung, mã cụ thể do người soạn gán: bạn cần duyệt.

## N. Nguyên nhân
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

## B. Đặc điểm bệnh sử
| ID | Đặc điểm bệnh sử | Mã nguyên nhân | Mục checklist | Nguồn | Trích nguyên văn |
|---|---|---|---|---|---|
| KN-DN-B01 | Đau kiểu siết chặt, đè ép | +TIM-MV | DN-05 | 2.1 | “Đau kiểu siết chặt, đè ép được xem là biểu hiện điển hình của cơn đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-B02 | Bệnh nhân thiếu máu cơ tim có thể than khó thở/lo lắng thay vì đau ngực | ~TIM-MV | DN-11 | 2.1 | “một số bệnh nhân thiếu máu cục bộ cơ tim lại than phiền về triệu chứng khó thở hoặc cảm giác lo lắng mơ hồ hơn là triệu chứng đau ngực” |
| KN-DN-B03 | Đau khi ho, hít thở sâu (kiểu màng phổi) | +PHOI-VP, +PHOI-TTP, +TIM-MNT | DN-06 | 2.1 | “Đau ngực khi ho, khi hít thở sâu (đau ngực kiểu màng phổi) gợi ý các bệnh liên quan đến màng phổi như: viêm phổi, thuyên tắc phổi, viêm màng ngoài tim.” |
| KN-DN-B04 | Viêm màng ngoài tim/thuyên tắc phổi lớn có thể đau đè ép, khó phân biệt với đau thắt ngực | ~TIM-MNT, ~PHOI-TTP | DN-05 | 2.1 | “Đau ngực trong viêm màng ngoài tim hoặc thuyên tắc phổi lớn đôi khi lại đau kiểu đè ép và rất khó phân biệt với đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-B05 | Đau kiểu xé, như dao đâm | +TIM-DMC | DN-05 | 2.1 | “Đau kiểu xé, như dao đâm thường gặp ở những bệnh nhân có bóc tách động mạch chủ cấp.” |
| KN-DN-B06 | Đau kiểu nóng rát | +TH-GERD, ~TIM-MV | DN-05 | 2.1 | “Đau kiểu nóng rát gợi ý bệnh trào ngược dạ dày-thực quản nhưng cũng có thể xảy ra ở bệnh nhân thiếu máu cục bộ cơ tim.” |
| KN-DN-B07 | Đau sau xương ức lan lên cổ, hàm, vai hoặc cánh tay | +TIM-MV | DN-02, DN-03 | 2.2 | “Đau sau xương ức lan lên cổ, hàm, vai hoặc cánh tay điển hình cho đau thắt ngực do thiếu máu cục bộ cơ tim.” |
| KN-DN-B08 | Đau khu trú chỉ bằng một đầu ngón tay | -TIM-MV | DN-02 | 2.2 | “Đau thắt ngực ít khi khu trú chỉ bằng một đầu ngón tay.” |
| KN-DN-B09 | Đau vượt quá hàm dưới hoặc dưới rốn | -TIM-MV | DN-02, DN-03 | 2.2 | “Đau thắt ngực cũng có thể đau ở thượng vị nhưng hiếm khi đau vượt quá hàm dưới hoặc dưới rốn.” |
| KN-DN-B10 | Bệnh thực quản: đau sau xương ức | +TH-GERD, +TH-TQ | DN-02 | 2.2 | “Đau ngực do bệnh thực quản thường đau sau xương ức” |
| KN-DN-B11 | Bệnh tiêu hóa khác: đau nhiều nhất ở bụng/thượng vị lan lên ngực [mã suy ra: sách ghi chung "bệnh lý tiêu hóa khác"] | +TH-LOET, +TH-TUIMAT, +TH-TUY | DN-02 | 2.2 | “các bệnh lý tiêu hóa khác lại thường đau nhiều nhất ở bụng hoặc thượng vị lan lên ngực” |
| KN-DN-B12 | Đau dữ dội lan sau lưng, giữa hai xương bả vai | +TIM-DMC | DN-03 | 2.2 | “Đau ngực dữ dội lan ra sau lưng, đặc biệt giữa hai xương bả vai, nên nghĩ đến bóc tách động mạch chủ cấp.” |
| KN-DN-B13 | Thiếu máu cơ tim: nặng dần vài phút, tăng khi gắng sức, giảm khi nghỉ | +TIM-MV | DN-01, DN-04, DN-06, DN-07 | 2.3 | “Đau ngực do thiếu máu cục bộ cơ tim thường nặng dần trong vài phút, tăng khi gắng sức, giảm khi nghỉ ngơi.” |
| KN-DN-B14 | Cường độ đạt đỉnh ngay từ đầu | +TIM-DMC, +PHOI-TTP, +PHOI-TKMP | DN-01 | 2.3 | “đau ngực có cường độ đạt đỉnh ngay từ đầu thường gợi ý bóc tách động mạch chủ, thuyên tắc phổi, tràn khí màng phổi tự phát” |
| KN-DN-B15 | Đau chỉ vài giây, hoặc hằng định nhiều giờ đến nhiều ngày | -TIM-MV | DN-04 | 2.3 | “Đau ngực chỉ kéo dài một vài giây hoặc hằng định về cường độ trong một thời gian dài (nhiều giờ đến nhiều ngày) hiếm khi do thiếu máu cục bộ cơ tim.” |
| KN-DN-B16 | Đau vào sáng sớm | +TH-GERD | DN-01 | 2.3 | “Đau ngực do bệnh trào ngược dạ dày-thực quản thường xảy ra vào sáng sớm” |
| KN-DN-B17 | Thích ngồi nghỉ hoặc dừng đi bộ để giảm đau | +TIM-MV | DN-07 | 2.4 | “Bệnh nhân đau ngực do thiếu máu cục bộ cơ tim thường thích ngồi nghỉ ngơi hoặc tạm dừng đi bộ để giảm đau.” |
| KN-DN-B18 | Cường độ đổi theo tư thế hoặc cử động chi trên, cổ [mã suy ra: sách ghi chung "cơ xương khớp"] | +TT-THANH, +TT-DIADEM, -TIM-MV | DN-06 | 2.4 | “Đau ngực có cường độ thay đổi liên quan đến tư thế hoặc cử động chi trên và cổ thường gợi ý đến các nguyên nhân về cơ xương khớp, ít khi do thiếu máu cục bộ cơ tim.” |
| KN-DN-B19 | Nặng hơn khi nằm ngửa, giảm khi ngồi cúi ra trước | +TIM-MNT | DN-06, DN-07 | 2.4 | “Đau ngực trong viêm màng ngoài tim thường nặng hơn khi nằm ngửa và giảm đau khi ngồi cúi người ra phía trước.” |
| KN-DN-B20 | Đau khởi phát do ăn uống | +TH-LOET, +TH-TUIMAT, +TH-TUY | DN-01 | 2.4 | “Đau khởi phát do ăn uống thường do các nguyên nhân tiêu hóa như loét dạ dày, viêm túi mật, viêm tụy.” |
| KN-DN-B21 | Đau sau ăn vẫn có thể do bệnh động mạch vành nặng | ~TIM-MV | DN-01 | 2.4 | “ở những bệnh nhân có bệnh động mạch vành nặng, sự tái phân bố máu đến nội tạng sau bữa ăn có thể khởi phát cơn đau thắt ngực sau ăn” |
| KN-DN-B22 | Khởi phát do rượu, một số thức ăn, nằm ngửa | +TH-GERD | DN-01, DN-06 | 2.4 | “Đau do bệnh trào ngược dạ dày-thực quản có thể khởi phát do rượu, một số loại thức ăn hoặc tư thế nằm ngửa.” |
| KN-DN-B23 | Giảm khi dùng thuốc giảm tiết acid, thường không liên quan gắng sức | +TH-GERD, +TH-LOET | DN-06, DN-07 | 2.4 | “Đau ngực do bệnh trào ngược dạ dày-thực quản hoặc loét dạ dày thường giảm khi dùng thuốc giảm tiết acid dạ dày và thường không liên quan đến gắng sức.” |
| KN-DN-B24 | Giảm trong vài phút khi dùng nitroglycerin | +TIM-MV, ~TH-TQ | DN-07 | 2.4 | “Đau ngực giảm trong vòng vài phút khi dùng nitroglycerin gợi ý thiếu máu cục bộ cơ tim, tuy nhiên cũng có thể gặp trong co thắt thực quản.” |
| KN-DN-B25 | Triệu chứng kèm theo trong thiếu máu cơ tim | +TIM-MV | DN-10, DN-11, DN-17 | 2.5 | “Các triệu chứng kèm theo trong thiếu máu cục bộ cơ tim bao gồm: vã mồ hôi, khó thở, buồn nôn, mệt mỏi, choáng váng, ợ hơi.” |
| KN-DN-B26 | Khó thở không giúp phân biệt nhưng gợi ý nguyên nhân tim phổi | — | DN-11 | 2.5 | “Khó thở có thể gặp trong nhiều bệnh cảnh khác nhau gây đau ngực nên không giúp chẩn đoán phân biệt, tuy nhiên khó thở là dấu hiệu gợi ý các nguyên nhân đau ngực do bệnh tim phổi.” |
| KN-DN-B27 | Suy hô hấp khởi phát đột ngột | +PHOI-TTP, +PHOI-TKMP | DN-11 | 2.5 | “Suy hô hấp khởi phát đột ngột cần nghĩ đến thuyên tắc phổi, tràn khí màng phổi tự phát.” |
| KN-DN-B28 | Ho ra máu | +PHOI-TTP | DN-16 | 2.5 | “Ho ra máu có thể xảy ra ở bệnh nhân thuyên tắc phổi” |
| KN-DN-B29 | Ho khạc đàm bọt hồng | +TIM-ST | DN-15 | 2.5 | “ho khạc đàm bọt hồng thường gặp trong suy tim nặng” |
| KN-DN-B30 | Ngất hoặc tiền ngất | +PHOI-TTP, +TIM-DMC, +TIM-MV | DN-13 | 2.5 | “Sự xuất hiện của ngất hoặc tiền ngất cần nghĩ đến thuyên tắc phổi, bóc tách động mạch chủ, rối loạn nhịp do thiếu máu cục bộ cơ tim.” |
| KN-DN-B31 | Buồn nôn, nôn: thường gợi ý bệnh tiêu hóa nhưng cũng gặp trong nhồi máu cơ tim (thường thành dưới) | ~TIM-MV | DN-17 | 2.5 | “Mặc dù buồn nôn và nôn thường gợi ý bệnh lý tiêu hóa nhưng cũng có thể xảy ra trong bệnh cảnh nhồi máu cơ tim (thường là nhồi máu cơ tim thành dưới)” |
| KN-DN-B32 | Tiền căn: yếu tố nguy cơ bệnh mạch vành | +TIM-MV, +CH-LIPID, +CH-DTD, +TIM-THA | DN-23, DN-31 | 3 | “Tiền căn cần chú ý đánh giá các yếu tố nguy cơ bệnh mạch vành (hút thuốc lá, tăng huyết áp, đái tháo đường, rối loạn lipid máu...)” |
| KN-DN-B33 | Tiền căn: yếu tố nguy cơ thuyên tắc huyết khối tĩnh mạch [mã suy ra: sách ghi "thuyên tắc huyết khối tĩnh mạch"] | +PHOI-TTP | DN-21, DN-30 | 3 | “các yếu tố nguy cơ của thuyên tắc huyết khối tĩnh mạch (ung thư, bất động, nằm lâu, hậu phẫu...)” |
| KN-DN-B34 | Tiền căn tăng huyết áp hoặc bệnh mô liên kết (Marfan) | +TIM-DMC, +TIM-THA | DN-20 | 6.3 | “Tiền căn tăng huyết áp hoặc bệnh lý mô liên kết như hội chứng Marfan làm tăng nguy cơ bóc tách động mạch chủ.” |
| KN-DN-B35 | Bệnh nhân trẻ: khai thác thêm thuốc gây nghiện (cocaine) | ~TIM-MV | DN-31 | 3 | “Những bệnh nhân trẻ tuổi thường ít có nguy cơ của bệnh lý mạch vành cần khai thác thêm tiền căn sử dụng thuốc gây nghiện (cocaine).” |
| KN-DN-B36 | Đau thắt ngực ổn định: xảy ra sau gắng sức, gặp lạnh, stress | +TIM-MV | DN-01 | 6.1 | “Cơn đau xảy ra sau gắng sức, gặp lạnh hoặc stress.” |
| KN-DN-B37 | Đau thắt ngực ổn định: kéo dài 20 giây đến 20 phút | +TIM-MV | DN-04 | 6.1 | “Đau kéo dài 20 giây đến 20 phút.” |
| KN-DN-B38 | Đau thắt ngực ổn định: giảm nhanh khi ngưng hoạt động hoặc ngậm nitroglycerin | +TIM-MV | DN-07 | 6.1 | “Đau giảm nhanh khi bệnh nhân ngưng mọi hoạt động hoặc ngậm nitroglycerin.” |
| KN-DN-B39 | Đau thắt ngực ổn định: sau xương ức, siết chặt, nghiền nát | +TIM-MV | DN-02, DN-05 | 6.1 | “Đau ngay sau xương ức.” “Cảm giác như siết chặt, nghiền nát.” |
| KN-DN-B40 | Hội chứng vành cấp: đau khi nghỉ, kéo dài trên 20 phút, không giảm với nitroglycerin | +TIM-MV | DN-01, DN-04, DN-07 | 6.1 | “Cơn đau thường xảy ra khi nghỉ ngơi, lan rộng hơn, kéo dài hơn 20 phút và không giảm đau với nitroglycerin.” |
| KN-DN-B41 | Hội chứng vành cấp: rất mệt, khó thở, vã mồ hôi, buồn nôn, nôn | +TIM-MV | DN-10, DN-11, DN-17 | 6.1 | “Tình trạng này khiến cho bệnh nhân rất mệt, khó thở, vã mồ hôi, có thể buồn nôn và nôn.” |
| KN-DN-B42 | Viêm màng ngoài tim cấp: bệnh cảnh điển hình | +TIM-MNT | DN-02, DN-03, DN-05, DN-07 | 6.2 | “Bệnh nhân có biểu hiện nhiễm siêu vi trước đó, đau sau xương ức hoặc ngực trái, có thể lan lên vai trái, đau nhói hoặc đau kiểu màng phổi, giảm đau khi ngồi cúi người ra trước.” |
| KN-DN-B43 | Bóc tách động mạch chủ: đau đột ngột, dữ dội ngay từ đầu, không giảm | +TIM-DMC | DN-01, DN-04, DN-05 | 6.3 | “Bệnh nhân khởi phát đau đột ngột, dữ dội ngay từ đầu và kéo dài không giảm.” |
| KN-DN-B44 | Bóc tách đoạn lên đau trước ngực, đoạn xuống đau giữa hai xương bả vai | +TIM-DMC | DN-02, DN-03 | 6.3 | “Bóc tách đoạn lên của động mạch chủ gây đau vùng trước ngực trong khi bóc tách đoạn xuống gây đau giữa hai xương bả vai.” |
| KN-DN-B45 | Thuyên tắc phổi: đau màng phổi đột ngột, thường một bên, kèm khó thở, có thể ho ra máu | +PHOI-TTP | DN-01, DN-02, DN-06, DN-11, DN-16 | 6.4 | “Đau ngực kiểu màng phổi khởi phát đột ngột, có thể đau kiểu đè ép trong thuyên tắc phổi diện rộng, thường đau một bên ngực, có thể đau sau xương ức, kèm khó thở.” “Bệnh nhân có thể ho ra máu, vã mồ hôi.” |
| KN-DN-B46 | Tăng áp động mạch phổi: đè ép dưới xương ức, khi gắng sức, kèm khó thở | +PHOI-TAP | DN-01, DN-02, DN-05, DN-11 | 6.5 | “Đau ngực dưới xương ức kiểu đè ép, thường khởi phát khi gắng sức, kèm khó thở.” |
| KN-DN-B47 | Viêm phổi, màng phổi: đau màng phổi một bên, khó thở, ho, sốt | +PHOI-VP, +PHOI-MP | DN-06, DN-11, DN-14, DN-15 | 6.6 | “Đau ngực kiểu màng phổi, đau một bên kèm theo khó thở, ho, sốt.” |
| KN-DN-B48 | Tràn khí màng phổi: đau màng phổi một bên, khởi phát đột ngột, khó thở | +PHOI-TKMP | DN-01, DN-06, DN-11 | 6.7 | “Đau ngực kiểu màng phổi một bên khởi phát đột ngột kèm khó thở.” |
| KN-DN-B49 | Loét dạ dày - tá tràng: nóng rát, liên quan bữa ăn, giảm khi ăn hoặc antacid | +TH-LOET | DN-01, DN-02, DN-05, DN-07 | 6.8 | “Đau thượng vị hoặc sau xương ức kiểu nóng rát, liên quan đến bữa ăn, giảm đau khi ăn hoặc dùng antacid.” |
| KN-DN-B50 | Trào ngược dạ dày-thực quản: nóng rát, sau ăn, nằm ngửa, ợ hơi, ợ chua, khó tiêu | +TH-GERD | DN-01, DN-02, DN-05, DN-06, DN-07, DN-17 | 6.9 | “đau sau xương ức hoặc thượng vị kiểu nóng rát, xảy ra sau khi ăn và khi nằm ngửa, kèm ợ hơi, ợ chua, khó tiêu” “giảm đau khi sử dụng antacid hoặc nitroglycerin (nếu có co thắt thực quản)” |
| KN-DN-B51 | Bệnh túi mật: đau quặn thượng vị hoặc hạ sườn phải sau ăn | +TH-TUIMAT | DN-01, DN-02, DN-05 | 6.10 | “Thường đau quặn bụng vùng thượng vị hoặc hạ sườn phải xảy ra sau ăn.” |
| KN-DN-B52 | Đau thành ngực: đau nhói, khu trú, tăng khi ấn, ho, hít thở, cử động | +TT-THANH | DN-02, DN-05, DN-06, DN-18 | 6.11 | “Thường đau nhói, khu trú tại một vùng nhỏ trên thành ngực, đau tăng khi ấn vào, khi ho, hít thở hoặc cử động.” |
| KN-DN-B53 | Herpes zoster: tăng cảm, đau theo khoanh da, bóng nước | +TT-HZ | DN-19 | 6.11 | “Viêm dây thần kinh liên sườn do Herpes zoster gây tăng cảm và đau theo khoanh da, lan theo rễ thần kinh, xuất hiện bóng nước tại chỗ viêm.” |
| KN-DN-B54 | Tâm lý: nữ dưới 40 tuổi, lo lắng, ê ẩm kéo dài hàng giờ, mệt, hồi hộp, khó thở | +TAMLY | DN-04, DN-31 | 6.12 | “Thường gặp ở bệnh nhân nữ dưới 40 tuổi, có tình trạng lo lắng căng thẳng, tiền căn trầm cảm hoặc cơn hoảng loạn.” “Cảm giác ê ẩm vùng mỏm tim hoặc sau xương ức kéo dài hàng giờ” “Bệnh nhân còn cảm thấy mệt, hồi hộp, khó thở, thở nhanh, chóng mặt, tê đầu chi.” |

## K. Dấu hiệu khám lâm sàng
| ID | Dấu hiệu khám | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-DN-K01 | Tổng quát: lo lắng, khó chịu, xanh tím, vã mồ hôi | +TIM-MV | 4.1 | “Bệnh nhân bị nhồi máu cơ tim hoặc bệnh tim phổi cấp tính thường lo lắng, khó chịu, xanh tím, vã mồ hôi.” |
| KN-DN-K02 | Thể trạng: nam trẻ, cao, gầy (Marfan) với tràn khí màng phổi | +PHOI-TKMP | 4.1 | “Bệnh nhân hội chứng Marfan thường là nam giới, trẻ tuổi, cao, gầy với tràn khí màng phổi tự phát.” |
| KN-DN-K03 | Nhịp tim nhanh và tụt huyết áp: dấu hiệu huyết động quan trọng | +TIM-MV, +PHOI-TTP, +TIM-MNT, +PHOI-TKMP | 4.2 | “Nhịp tim nhanh và tụt huyết áp là những dấu hiệu về huyết động học quan trọng” “nhồi máu cơ tim với biến chứng choáng tim, thuyên tắc phổi diện rộng, viêm màng ngoài tim cấp với tràn dịch màng ngoài tim gây chèn ép tim cấp hoặc tràn khí màng phổi áp lực” |
| KN-DN-K04 | Bóc tách: tăng huyết áp nặng, có thể tụt huyết áp | +TIM-DMC | 4.2 | “Bóc tách động mạch chủ cấp thường đi kèm tình trạng tăng huyết áp nặng nhưng cũng có thể tụt huyết áp khi có tổn thương động mạch vành hoặc bóc tách vào khoang màng ngoài tim.” |
| KN-DN-K05 | Nhịp nhanh xoang | +PHOI-TTP | 4.2 | “Nhịp nhanh xoang là biểu hiện quan trọng của thuyên tắc phổi diện rộng.” |
| KN-DN-K06 | Nhịp tim nhanh và giảm oxy | — | 4.2 | “Nhịp tim nhanh và giảm oxy gợi ý nguyên nhân về phổi.” |
| KN-DN-K07 | Sốt nhẹ: không đặc hiệu | ~TIM-MV, ~PHOI-TTP | 4.2 | “Sốt nhẹ không phải là dấu hiệu đặc hiệu vì có thể gặp trong nhồi máu cơ tim hoặc thuyên tắc huyết khối kèm nhiễm trùng.” |
| KN-DN-K08 | Khám phổi tìm nguyên nhân về phổi | +PHOI-VP, +PHOI-TKMP | 4.3 | “Khám phổi giúp xác định các nguyên nhân đau ngực liên quan đến phổi như: viêm phổi, tràn khí màng phổi.” |
| KN-DN-K09 | Phù phổi cấp do suy thất trái hoặc biến chứng cơ học của nhồi máu cơ tim | +TIM-MV | 4.3 | “Suy thất trái và các biến chứng cơ học cấp do nhồi máu cơ tim có thể dẫn đến phù phổi cấp.” |
| KN-DN-K10 | Tĩnh mạch cảnh: thường bình thường ở hội chứng vành cấp | ~TIM-MV | 4.4 | “Xung động tĩnh mạch cảnh thường bình thường ở bệnh nhân hội chứng vành cấp nhưng cũng có thể bất thường trong chèn ép tim hoặc suy thất phải cấp tính.” |
| KN-DN-K11 | Tiếng T3, T4 | +TIM-ST | 4.4 | “Khám tim có thể nghe được tiếng T3, T4 trong suy tim.” |
| KN-DN-K12 | Âm thổi hở van hai lá hoặc thông liên thất | +TIM-MV | 4.4 | “Âm thổi của hở van hai lá hoặc âm thổi thô ráp của thông liên thất có thể gợi ý đến biến chứng cơ học của nhồi máu cơ tim cấp.” |
| KN-DN-K13 | Âm thổi hở van động mạch chủ | +TIM-DMC | 4.4 | “Âm thổi của hở van động mạch chủ có thể là biến chứng của bóc tách động mạch chủ đoạn lên.” |
| KN-DN-K14 | Âm thổi gợi ý bệnh tim nền (hẹp van động mạch chủ, bệnh cơ tim phì đại) | +TIM-VAN, +TIM-BCT | 4.4 | “Các âm thổi khác giúp gợi ý bệnh tim nền làm nặng thêm tình trạng thiếu máu cục bộ cơ tim như hẹp van động mạch chủ, bệnh cơ tim phì đại...” |
| KN-DN-K15 | Tiếng cọ màng ngoài tim | +TIM-MNT | 4.4 | “Tiếng cọ màng ngoài tim gặp trong viêm màng ngoài tim giai đoạn đầu khi chưa có tràn dịch màng ngoài tim.” |
| KN-DN-K16 | Bụng: xác định điểm đau [mã suy ra: sách ghi chung "nguyên nhân về tiêu hóa"] | +TH-LOET, +TH-TUIMAT, +TH-TUY | 4.5 | “Xác định được điểm đau khi khám bụng giúp hướng đến các nguyên nhân về tiêu hóa gây đau ngực.” |
| KN-DN-K17 | Gan to do sung huyết [mã suy ra: sách ghi "suy thất phải nặng"] | +TIM-ST | 4.5 | “có thể khám thấy gan to do sung huyết” |
| KN-DN-K18 | Mất mạch, tím (đặc biệt chi trên) | +TIM-DMC | 4.6 | “Biểu hiện của tình trạng thiếu máu nuôi chi cấp tính là mất mạch và tím, đặc biệt là chi trên, có thể gợi ý bóc tách động mạch chủ.” |
| KN-DN-K19 | Sưng phù chỉ một bên chi dưới [mã suy ra: sách ghi "thuyên tắc huyết khối tĩnh mạch"] | +PHOI-TTP | 4.6 | “Sưng phù chỉ ở một bên chi dưới giúp hướng đến thuyên tắc huyết khối tĩnh mạch.” |
| KN-DN-K20 | Sưng, đỏ, đau khu trú tại khớp sụn sườn, sụn ức | +TT-THANH | 4.7 | “Khám cơ xương khớp có thể phát hiện sưng, đỏ, đau khu trú tại các khớp sụn sườn, sụn ức.” |
| KN-DN-K21 | Ấn đau thành ngực: gợi ý cơ xương khớp nhưng không loại trừ thiếu máu cơ tim | +TT-THANH, ~TIM-MV | 4.7 | “Mặc dù ấn đau thành ngực giúp gợi ý các nguyên nhân về cơ xương khớp gây đau ngực nhưng không loại trừ hoàn toàn được thiếu máu cục bộ cơ tim.” |
| KN-DN-K22 | Giảm cảm giác ở chi trên | +TT-DIADEM | 4.7 | “Giảm cảm giác ở chi trên có thể nghĩ đến bệnh lý liên quan đĩa đệm cột sống cổ.” |
| KN-DN-K23 | Sang thương da vùng ngực (Herpes zoster, viêm da) | +TT-HZ | 4.8 | “Bệnh nhân đau ngực có thể có sang thương Herpes zoster hay sang thương viêm da có thể giúp gợi ý nguyên nhân đau ngực.” |
| KN-DN-K24 | U vàng quanh mắt (xanthoma) | +TIM-MV | 4.8 | “cũng cần thăm khám tìm u vàng quanh mắt (xanthoma) gợi ý nguy cơ bệnh mạch vành” |
| KN-DN-K25 | Khám thực thể có thể bình thường ở hội chứng vành cấp | ~TIM-MV | 4 | “khám thực thể có thể bình thường ở những bệnh nhân bị hội chứng vành cấp” |
| KN-DN-K26 | Bệnh động mạch vành: gallop T3/T4, hở van hai lá, ran phổi nếu có biến chứng | +TIM-MV | 6.1 | “Khám thực thể có thể nghe được tiếng ngựa phi (gallop) T3, T4, âm thổi của hở van hai lá, ran ở phổi nếu nhồi máu cơ tim có biến chứng.” |
| KN-DN-K27 | Viêm màng ngoài tim: tiếng tim mờ, mạch nghịch khi chèn ép tim cấp | +TIM-MNT | 6.2 | “Trong giai đoạn tràn dịch màng ngoài tim, có thể nghe tiếng tim mờ, có thể có mạch nghịch khi có chèn ép tim cấp.” |
| KN-DN-K28 | Bóc tách: tăng huyết áp, hở van động mạch chủ, mất mạch ngoại biên | +TIM-DMC | 6.3 | “Khám thực thể có thể thấy tăng huyết áp, âm thổi của hở van động mạch chủ, mất mạch ngoại biên.” |
| KN-DN-K29 | Thuyên tắc phổi: thở nhanh nông, nhịp nhanh, tím tái, tụt huyết áp | +PHOI-TTP | 6.4 | “Khám thực thể có thể thấy thở nhanh nông, nhịp tim nhanh, tím tái, tụt huyết áp.” |
| KN-DN-K30 | Tăng áp động mạch phổi: dấu hiệu suy tim phải | +PHOI-TAP | 6.5 | “Khám có thể thấy các dấu hiệu của suy tim phải.” |
| KN-DN-K31 | Viêm phổi, màng phổi: ran nổ, tiếng cọ màng phổi | +PHOI-VP, +PHOI-MP | 6.6 | “Khám phổi ghi nhận có ran nổ, có thể có tiếng cọ màng phổi.” |
| KN-DN-K32 | Tràn khí màng phổi: âm phế bào giảm | +PHOI-TKMP | 6.7 | “Khám thấy âm phế bào giảm ở bên có tràn khí màng phổi.” |

## C. Cận lâm sàng (`+` giúp phát hiện/xác định/loại trừ nguyên nhân đó; `~` kết quả không đặc hiệu)
| ID | Cận lâm sàng | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-DN-C01 | Điện tâm đồ: then chốt xác định thiếu máu cơ tim | +TIM-MV | 5.1 | “Điện tâm đồ đóng vai trò then chốt trong việc xác định bệnh nhân đau ngực do thiếu máu cục bộ cơ tim” |
| KN-DN-C02 | Điện tâm đồ: thời điểm làm và đo lặp lại khi nghi hội chứng vành cấp | +TIM-MV | 5.1 | “Điện tâm đồ cần thực hiện trong vòng 10 phút sau nhập viện và nên đo lặp lại mỗi 30-60 phút ở những bệnh nhân nghi ngờ hội chứng vành cấp.” |
| KN-DN-C03 | Điện tâm đồ: ST chênh xuống hoặc T âm sâu, đối xứng | +TIM-MV | 5.1 | “Hình ảnh đoạn ST chênh xuống hoặc T âm sâu, đối xứng trên điện tâm đồ giúp gợi ý thiếu máu cục bộ cơ tim.” |
| KN-DN-C04 | Điện tâm đồ nghỉ có độ nhạy thấp | ~TIM-MV | 5.1 | “độ nhạy của điện tâm đồ đo lúc nghỉ trong chẩn đoán thiếu máu cục bộ cơ tim chỉ đạt khoảng 20%” |
| KN-DN-C05 | Bất thường ST, T không đặc hiệu, gặp ở nhiều bệnh cảnh | ~PHOI-TTP, ~TIM-MNT, ~TIM-VCT, ~TAMLY | 5.1 | “Bất thường về ST, T có thể xảy ra trên nhiều bệnh cảnh khác nhau như: thuyên tắc phổi, phì đại thất trái, viêm màng ngoài tim, viêm cơ tim, rối loạn điện giải, rối loạn chuyển hóa.” “Tình trạng tăng thông khí trong rối loạn hoảng sợ có thể dẫn đến các bất thường về ST, T không đặc hiệu.” |
| KN-DN-C06 | Điện tâm đồ trong thuyên tắc phổi | +PHOI-TTP | 5.1 | “Thuyên tắc phổi thường có biểu hiện nhịp nhanh xoang, có thể có trục lệch phải, sóng S ở chuyển đạo DI, sóng Q và T ở chuyển đạo DIII.” |
| KN-DN-C07 | Điện tâm đồ phân biệt viêm màng ngoài tim với nhồi máu cơ tim | +TIM-MNT | 5.1 | “ST chênh lên lan tỏa không theo giải phẫu mạch vành và đoạn PR chênh lõm xuống giúp phân biệt viêm màng ngoài tim với nhồi máu cơ tim cấp.” |
| KN-DN-C08 | X quang ngực: phát hiện bất thường về phổi | +PHOI-VP, +PHOI-TKMP | 5.2 | “X quang ngực đóng vai trò quan trọng trong việc phát hiện các bất thường về phổi như viêm phổi, áp-xe phổi, tràn khí màng phổi hay u phổi.” |
| KN-DN-C09 | X quang ngực thường bình thường ở hội chứng vành cấp | ~TIM-MV | 5.2 | “X quang ngực thường bình thường ở bệnh nhân hội chứng vành cấp nhưng cũng có thể thấy được hình ảnh phù phổi cấp.” |
| KN-DN-C10 | X quang ngực: trung thất dãn rộng, dấu Hampton/Westermark, vôi hóa màng ngoài tim | +TIM-DMC, +PHOI-TTP, +TIM-MNT | 5.2 | “trung thất dãn rộng trong bóc tách động mạch chủ, dấu hiệu Hampton hoặc Westermark trong thuyên tắc phổi, vôi hóa màng ngoài tim trong viêm màng ngoài tim mạn” |
| KN-DN-C11 | Siêu âm tim: rối loạn vận động vùng, chèn ép tim cấp | +TIM-MV, +TIM-MNT | 5.3 | “siêu âm tim giúp phát hiện những rối loạn vận động vùng gợi ý đến thiếu máu tim cục bộ cấp tính hoặc chèn ép tim cấp trong tràn dịch màng ngoài tim ở bệnh nhân viêm màng ngoài tim” |
| KN-DN-C12 | Siêu âm tim qua thành ngực: độ nhạy thấp với bóc tách | ~TIM-DMC | 5.3 | “Siêu âm tim qua thành ngực có thể phát hiện dấu hiệu bóc tách động mạch chủ nhưng có độ nhạy thấp.” |
| KN-DN-C13 | Điện tâm đồ gắng sức: phân tầng nguy cơ bệnh động mạch vành | ~TIM-MV | 5.4 | “Điện tâm đồ gắng sức thường được sử dụng để phân tầng nguy cơ mắc bệnh động mạch vành ở những bệnh nhân đánh giá ban đầu chưa tìm được nguyên nhân gây đau ngực và có nguy cơ thấp mắc hội chứng vành cấp.” |
| KN-DN-C14 | Đau ngực đang tiến triển: chống chỉ định gắng sức | ~TIM-MV | 5.4 | “Vì đau ngực đang tiến triển là chống chỉ định của nghiệm pháp gắng sức nên điện tâm đồ gắng sức thường được dùng để chẩn đoán bệnh lý động mạch vành mạn.” |
| KN-DN-C15 | CT động mạch vành: độ nhạy cao | +TIM-MV | 5.5 | “Chụp cắt lớp vi tính động mạch vành có độ nhạy cao trong phát hiện bệnh lý động mạch vành.” |
| KN-DN-C16 | CT giúp loại trừ bóc tách, tràn dịch màng ngoài tim, thuyên tắc phổi | +TIM-DMC, +TIM-MNT, +PHOI-TTP | 5.5 | “Chụp cắt lớp vi tính cũng giúp loại trừ bóc tách động mạch chủ, tràn dịch màng ngoài tim, thuyên tắc phổi.” |
| KN-DN-C17 | MRI tim: nhồi máu cơ tim, bệnh cơ tim, bóc tách | +TIM-MV, +TIM-BCT, +TIM-DMC | 5.6 | “Chụp cộng hưởng từ tim có thể phát hiện sớm nhồi máu cơ tim, xác định chính xác vùng hoại tử cơ tim, chẩn đoán các dạng bệnh cơ tim.” “Chụp cộng hưởng từ cũng cho phép đánh giá chính xác bóc tách động mạch chủ.” |
| KN-DN-C18 | Tổng phân tích tế bào máu | — | 5.7 | “Tổng phân tích tế bào máu cần thực hiện ngay lúc nhập viện.” “Tăng bạch cầu đa nhân trung tính hay bạch cầu lympho có thể gợi ý các nguyên nhân viêm nhiễm.” |
| KN-DN-C19 | Men tim (troponin ưu tiên hơn CK-MB) | +TIM-MV | 5.7 | “Men tim cần được xét nghiệm ngay lúc nhập viện và lặp lại mỗi 3 – 6 giờ ở tất cả bệnh nhân nghi ngờ hội chứng vành cấp.” “troponin thường được sử dụng nhiều hơn CK-MB trong chẩn đoán nhồi máu cơ tim” |
| KN-DN-C20 | Men tim có thể tăng ngoài nhồi máu cơ tim | ~TIM-VCT, ~THAN-PHU, ~PHOI-TTP | 5.7 | “men tim có thể tăng trong những bệnh cảnh khác gây tổn thương cơ tim ngoài nhồi máu cơ tim như: viêm cơ tim, suy thận mạn giai đoạn cuối, thuyên tắc phổi” |
| KN-DN-C21 | D-dimer | +PHOI-TTP | 5.7 | “D-dimer tăng gợi ý đến thuyên tắc phổi. D-dimer bình thường giúp loại trừ thuyên tắc phổi.” |
| KN-DN-C22 | BNP hoặc NT-proBNP: vai trò tiên lượng | ~TIM-MV, ~PHOI-TTP | 5.7 | “BNP hoặc NT-proBNP có vai trò tiên lượng ở bệnh nhân hội chứng mạch vành cấp hoặc thuyên tắc phổi.” |

## P. Bảng so sánh / chẩn đoán phân biệt (chép nguyên dạng từ Bảng 2 và Bảng 3)
| ID | Nội dung so sánh | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-DN-P01 | Bảng 2, cột Đau thắt ngực | +TIM-MV | Bảng 2 | “Siết chặt hoặc đè ép” “Khởi phát khi gắng sức” “Giảm khi nghỉ” “Giảm khi dùng nitrate” “Không liên quan đến tư thế” “Không ảnh hưởng bởi hô hấp” |
| KN-DN-P02 | Bảng 2, cột Viêm màng ngoài tim hoặc màng phổi | +TIM-MNT, +PHOI-MP | Bảng 2 | “Đau nhói” “Không liên quan gắng sức” “Không giảm khi nghỉ” “Không ảnh hưởng bởi nitrate” “Tăng khi nằm ngửa” “Tăng khi hít thở” “Có tiếng cọ màng tim hoặc màng phổi” |
| KN-DN-P03 | Bảng 2, cột Trào ngược dạ dày thực quản | +TH-GERD | Bảng 2 | “Đau nóng rát” “Không liên quan gắng sức” “Không giảm khi nghỉ” “Không ảnh hưởng bởi nitrate (trừ khi kèm co thắt thực quản)” “Có thể khởi phát khi nằm ngửa” “Không ảnh hưởng bởi hô hấp” |
| KN-DN-P04 | Bảng 3, hội chứng vành cấp (so với đau thắt ngực) | +TIM-MV | Bảng 3 | “Khởi phát khi nghỉ” “Đau nhiều” “Vã mồ hôi” “Lo lắng nhiều” “Không giảm với nitrate” “Có triệu chứng kèm theo (buồn nôn, nôn)” |
| KN-DN-P05 | Bảng 3, đau thắt ngực (so với hội chứng vành cấp) | +TIM-MV | Bảng 3 | “Khởi phát khi gắng sức” “Đau vừa phải” “Không vã mồ hôi” “Không lo lắng hoặc lo lắng ít” “Giảm đau với nitrate” “Không có triệu chứng kèm theo” |
| KN-DN-P06 | Bảng 3, nhồi máu cơ tim (so với bóc tách động mạch chủ) | +TIM-MV | Bảng 3 | “Đau giữa ngực” “Khởi phát bán cấp (vài phút)” “Đau nhiều” |
| KN-DN-P07 | Bảng 3, bóc tách động mạch chủ (so với nhồi máu cơ tim) | +TIM-DMC | Bảng 3 | “Đau lan sau lưng” “Khởi phát cấp tính” “Đau dữ dội, như xé” |
| KN-DN-P08 | Bảng 3, thiếu máu cục bộ cơ tim (so với đau thành ngực) | +TIM-MV | Bảng 3 | “Liên quan đến gắng sức” “Xảy ra khi gắng sức” “Đau từng cơn” “Đau lan” “Không điểm đau thành ngực” |
| KN-DN-P09 | Bảng 3, đau thành ngực (so với thiếu máu cục bộ cơ tim) | +TT-THANH | Bảng 3 | “Liên quan đến tư thế” “Thường đau nhiều hơn khi nghỉ” “Đau kéo dài liên tục” “Đau khu trú” “Có điểm đau thành ngực” |

## S. Sơ đồ tiếp cận của sách (mục 7)
| ID | Nhóm | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-DN-S01 | Do tim, thiếu máu cục bộ cơ tim | +TIM-MV | 7 | “Thiếu máu cục bộ cơ tim --> Hội chứng vành cấp, Cơn đau thắt ngực ổn định” |
| KN-DN-S02 | Do tim, không thiếu máu cục bộ cơ tim | +TIM-MNT, +TIM-VCT | 7 | “Không thiếu máu cục bộ cơ tim --> Viêm màng ngoài tim, Viêm cơ tim” |
| KN-DN-S03 | Không do tim, mạch máu | +TIM-DMC, +PHOI-TTP | 7 | “Mạch máu --> Bóc tách động mạch chủ, Thuyên tắc phổi” |
| KN-DN-S04 | Không do tim, phổi | +PHOI-VP, +PHOI-MP, +PHOI-TKMP | 7 | “Phổi --> Viêm phổi, Viêm màng phổi, Tràn khí màng phổi” |
| KN-DN-S05 | Không do tim, nhóm khác | — | 7 | “Khác --> Dạ dày – ruột, Thần kinh, cơ xương khớp, Tâm lý” |
