# Nghiên cứu nghĩa vụ license cho bản web public

- Ngày chốt dữ liệu: 2026-08-22
- Snapshot repo: [`81377589f902a032899b018b589c8debdce705a2`](https://github.com/tdhcoding/DigitCode-EscapeRoom/tree/81377589f902a032899b018b589c8debdce705a2)
- Issue: [#5 - Nghiên cứu nghĩa vụ license cho bản web public](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/5)
- Phạm vi: source hiện tại, ranh giới Qt/Arduino với web, dependency web, font/asset và mô tả `Decorum-inspired`

> Tài liệu này là nghiên cứu kỹ thuật dựa trên các nguồn sơ cấp được dẫn, không phải tư vấn pháp lý. Luật áp dụng, hợp đồng, tư cách chủ sở hữu và cách một tòa án phân loại một sản phẩm cụ thể đều chưa được xác định. Các nguồn luật Hoa Kỳ bên dưới chỉ cung cấp một khung tham chiếu; chủ dự án cần hỏi luật sư tại các khu vực pháp lý nơi sản phẩm được sở hữu, vận hành và phát hành.

## Kết luận điều hành

**Khuyến nghị release:** chưa phát hành web app public production cho đến khi đóng được các gate trong [checklist](#checklist-trước-khi-release). Đây là khuyến nghị quản trị release, không phải kết luận rằng việc phát hành hiện tại chắc chắn vi phạm pháp luật.

Bốn điểm quyết định:

1. Repo đang public nhưng không có `LICENSE`. Điều này không tự động cấm người có quyền tự deploy sản phẩm của mình, nhưng cũng không trao một open-source license rộng rãi cho người khác. GitHub nói rõ rằng khi không có license thì quyền tác giả mặc định áp dụng; Terms of Service chỉ trao các quyền cần thiết để xem và fork qua chức năng GitHub ([GitHub Docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository), [GitHub ToS D.3-D.6](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#d-user-generated-content)).
2. Lịch sử Git chỉ hiện một danh tính tác giả, nhưng repo có tài liệu nhị phân, ảnh nhúng và cả bộ skill lấy từ repo khác. Metadata commit không đủ để chứng minh chain of title cho mọi file. Theo khung Hoa Kỳ, quyền ban đầu thường thuộc tác giả, có quy tắc riêng cho work made for hire, và chuyển giao ownership thường phải bằng văn bản có chữ ký ([17 U.S.C. §§ 201, 204](https://www.copyright.gov/title17/92chap2.html#201)).
3. Một browser build HTML/CSS/JS độc lập, không chứa Qt, QML đã biên dịch, Qt for WebAssembly, firmware hay thư viện Arduino, có thể tạo một ranh giới phân phối sạch về mặt kỹ thuật. Ranh giới đó chưa tồn tại trong repo vì chưa có web manifest, lockfile hoặc deploy artifact để kiểm chứng.
4. Cụm `Decorum-inspired` không tự nó cho biết có vi phạm hay không. Copyright không bảo hộ ý tưởng, hệ thống hay phương pháp vận hành, nhưng có thể bảo hộ cách thể hiện như text, artwork, photo và software ([17 U.S.C. § 102](https://www.copyright.gov/title17/92chap1.html#102), [U.S. Copyright Office FAQ](https://www.copyright.gov/help/faq/faq-protect.html)). `Décorum` đồng thời đang được dùng làm tên một board game trên kênh của Floodgate Games, nên cần tách riêng đánh giá trademark và khả năng gây nhầm lẫn ([Floodgate Games](https://floodgate.games/products/decorum), [USPTO](https://www.uspto.gov/trademarks/search/likelihood-confusion)).

## Cách đọc tài liệu

- **Dữ kiện nguồn:** nội dung mà repo, license hoặc cơ quan chính thức trực tiếp cho biết.
- **Rủi ro:** điểm chưa đủ dữ liệu hoặc có thể làm phát sinh nghĩa vụ; không phải kết luận pháp lý.
- **Quyết định:** việc chủ dự án, kỹ sư release hoặc luật sư phải chốt và lưu bằng chứng.

License upstream trong tài liệu này là license quan sát trên nhánh upstream vào ngày chốt dữ liệu. Vì firmware không khóa version, các license đó **không thay thế** việc kiểm tra đúng artifact sẽ build và phát hành.

## Kiểm kê hiện trạng

| Nhóm | Dữ kiện nguồn tại snapshot | License/provenance quan sát | Ý nghĩa đối với web release |
|---|---|---|---|
| Source DigitCode | Repo GitHub public; không có `LICENSE*`/`COPYING*`; GitHub API trả `license: null` ([API](https://api.github.com/repos/tdhcoding/DigitCode-EscapeRoom), [snapshot](https://github.com/tdhcoding/DigitCode-EscapeRoom/tree/81377589f902a032899b018b589c8debdce705a2)) | Chưa có license first-party được công bố | Chủ dự án phải chốt all-rights-reserved hay một license cụ thể; không dùng license first-party để che lên third-party material |
| Tác giả/contributor | `git shortlog -sne --all` cho thấy 17 commit của `Haven <taduchieu123@gmail.com>` tại snapshot | Chỉ là metadata Git, không phải bằng chứng đầy đủ về ownership, employment, assignment, asset source hay AI/tool terms | Cần lập chain of title trước khi cấp license hoặc deploy code |
| Native desktop | [`CMakeLists.txt`](../../CMakeLists.txt) yêu cầu Qt 6.10 và các component Core, Gui, Qml, Quick, WebSockets, Network; QML còn import `QtQuick.Controls` | Qt commercial hoặc các lựa chọn open-source theo từng module; có third-party code bên trong Qt | Không đưa Qt/QML/runtime/WASM vào browser artifact nếu mục tiêu là tách web khỏi Qt |
| Firmware | [Sketch](../../firmware/DigitCodeFirmware/DigitCodeFirmware.ino) dùng ESP32 Arduino core, WebSockets, ArduinoJson, PCF8574, LedControl, GFX, SSD1306 | Hỗn hợp LGPL-2.1, MIT và BSD; không khóa exact version | Không bundle firmware binary, core hay library vào web release nếu chưa có compliance plan riêng |
| Web | Không có `package.json`, lockfile, Deno manifest hay web source tree tại snapshot | Chưa có dependency để đánh giá | Không thể phê duyệt license của stack chưa được chọn; audit lại sau khi có lockfile và artifact |
| Font và media rời | Không có file tracked mang đuôi `.woff`, `.woff2`, `.ttf`, `.otf`, `.png`, `.jpg`, `.jpeg` hoặc `.svg`; QML gọi Menlo/Courier New từ hệ điều hành, ví dụ [`ScreenMenu.qml`](../../UI/ScreenMenu.qml) | Không thấy font/media rời được bundle | Web không được tự ý copy/self-host các font hệ thống; font/icon/asset mới phải có provenance và điều khoản embedding/redistribution |
| Tài liệu DOCX | [`DigitCode_BaoCao_v6.docx`](../../DigitCode_BaoCao_v6.docx) là gói OOXML có `word/media/image1.jpeg` | Nguồn, tác giả và quyền với ảnh chưa được ghi nhận | Không đưa ảnh này vào web; xem xét cả việc tiếp tục phân phối nó trong repo public |
| Agent skills | [`skills-lock.json`](../../skills-lock.json) gắn các skill với `mattpocock/skills`, nhưng không lưu source commit/tag | Upstream hiện công bố MIT ([LICENSE](https://github.com/mattpocock/skills/blob/main/LICENSE)); bản copy trong repo không kèm toàn văn notice | Exclude `.agents/` và `.claude/` khỏi web artifact; đối chiếu với một revision có license và bổ sung notice riêng nếu tiếp tục phân phối các bản copy |
| CI actions | [Workflow](../../.github/workflows/ci.yml) gọi `actions/checkout@v4` và `jurplel/install-qt-action@v4` | Cả hai upstream công bố MIT ([checkout](https://github.com/actions/checkout/blob/main/LICENSE), [install-qt-action](https://github.com/jurplel/install-qt-action/blob/master/LICENSE)) | Đây là tooling được GitHub tải khi chạy CI, không phải runtime web quan sát hiện tại; vẫn ghi lại trong tooling inventory |

## Quyền với source hiện tại

### Dữ kiện nguồn

Repo public không đồng nghĩa với open source. GitHub nói rằng nếu không có license thì copyright mặc định áp dụng và người khác không mặc nhiên có quyền reproduce, distribute hoặc tạo derivative works; việc để repo public vẫn cho phép người dùng GitHub xem và fork nó thông qua dịch vụ ([GitHub Docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository), [GitHub ToS D.5](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#5-license-grant-to-other-users)). Terms of Service cũng đặt trách nhiệm lên người upload khi nội dung không do họ tạo ra ([GitHub ToS D.3](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#3-ownership-and-license-grants)).

Theo khung Hoa Kỳ, copyright vest ban đầu vào tác giả; tác giả của joint work là co-owner; work made for hire có quy tắc ownership riêng; và việc chuyển giao copyright ownership, ngoài một số trường hợp do luật, không hợp lệ nếu không có văn bản do chủ sở hữu quyền hoặc đại diện ký ([17 U.S.C. §§ 201, 204](https://www.copyright.gov/title17/92chap2.html#201)). Chưa có dữ liệu để kết luận khung Hoa Kỳ áp dụng cho DigitCode.

### Rủi ro

- Một tên/email duy nhất trong Git không xác nhận ai viết từng phần, code có được tạo trong phạm vi lao động/học tập/hợp đồng hay không, hay quyền đã được chuyển giao chưa.
- Ảnh trong DOCX, nội dung được copy, output từ công cụ AI và bộ skill bên ngoài có thể có chủ sở hữu quyền hoặc điều khoản khác với source DigitCode.
- Thêm một root `LICENSE` không làm chủ dự án trở thành chủ sở hữu quyền của third-party material và không hủy các license upstream.
- Repo đã public, nên provenance của nội dung đang được phân phối trên GitHub là việc cần xử lý ngay cả khi deploy web loại bỏ nó.

### Quyết định cần chốt

- **Chủ dự án:** lập danh sách tác giả, vai trò, quan hệ lao động/học tập/hợp đồng, assignment/permission và nguồn của từng asset hoặc bộ code bên ngoài.
- **Chủ dự án + luật sư:** xác định chủ thể pháp lý có quyền cấp license cho source first-party và jurisdiction áp dụng.
- **Chủ dự án:** chọn rõ repo sẽ all-rights-reserved hay dùng một open-source/proprietary source license. Nghiên cứu này không tự chọn MIT, GPL hay bất kỳ license nào thay chủ dự án.
- **Kỹ sư release:** đánh dấu scope first-party và third-party riêng; tạo `THIRD_PARTY_NOTICES`/license bundle từ exact artifact, không gộp chung mọi thứ dưới root license.

## Ranh giới Qt và native desktop

### Dữ kiện nguồn

Build native khai báo Qt Core, Gui, Qml, Quick, WebSockets và Network; các file UI dùng thêm Qt Quick Controls ([`CMakeLists.txt`](../../CMakeLists.txt), [`UI/Main.qml`](../../UI/Main.qml)). CI cài Qt `6.10.0` và module `qtwebsockets` ([`ci.yml`](../../.github/workflows/ci.yml)).

Tài liệu Qt 6.10 ghi Qt có commercial và open-source licensing, một số module chỉ có GPL, và Qt chứa third-party code theo license riêng ([Qt Licensing 6.10](https://doc.qt.io/qt-6.10/licensing.html)). Các trang module đang dùng ghi các lựa chọn commercial/LGPL-3.0/GPL cho [Core](https://doc.qt.io/qt-6.10/qtcore-index.html#licenses-and-attributions), [Gui](https://doc.qt.io/qt-6.10/qtgui-index.html#licenses-and-attributions), [Qml](https://doc.qt.io/qt-6.10/qtqml-index.html#licenses-and-attributions), [Quick](https://doc.qt.io/qt-6.10/qtquick-index.html#licenses-and-attributions), [Quick Controls](https://doc.qt.io/qt-6.10/qtquickcontrols-index.html#license-and-attributions), [WebSockets](https://doc.qt.io/qt-6.10/qtwebsockets-index.html#licenses) và [Network](https://doc.qt.io/qt-6.10/qtnetwork-index.html#licenses-and-attributions). License phải được đọc từ đúng package/edition đã nhận, không chỉ từ tên module.

Nếu phân phối một combined work theo LGPLv3, văn bản license và hướng dẫn Qt nêu các yêu cầu như notice/license copy, corresponding source của library, khả năng thay/relink library, reverse engineering để debug modification và installation information trong trường hợp áp dụng ([LGPLv3 §§ 3-4](https://www.gnu.org/licenses/lgpl-3.0.html), [Qt LGPL obligations](https://www.qt.io/licensing/open-source-lgpl-obligations)). Hướng dẫn Qt nói rõ danh sách của họ không đầy đủ.

Qt từ 6.8 có thể cung cấp SBOM theo exact installation/platform, bao gồm file, copyright, license, version và third-party package; Online Installer đặt chúng trong thư mục `sbom` ([Qt SBOM](https://doc.qt.io/qt-6.10/sbom.html)).

### Rủi ro

- Dùng Qt for WebAssembly, copy Qt JavaScript loader/plugin, đưa QML đã biên dịch vào browser, hoặc cho download native companion sẽ phá ranh giới "web không Qt".
- Chỉ nhìn các module top-level là chưa đủ: plugin platform, OpenSSL backend và third-party code trong exact Qt installation thay đổi theo build/platform.
- Việc browser nối WebSocket đến một backend không cho biết backend có được phân phối hay chỉ được operator chạy. Cần đánh giá artifact và người nhận, không suy từ protocol.

### Quyết định cần chốt

- **Kiến trúc sư + chủ dự án:** dùng web stack thuần browser/server không phụ thuộc Qt nếu mục tiêu là tách nghĩa vụ phân phối web khỏi Qt.
- **Kỹ sư release:** tạo danh sách file của browser artifact và chứng minh nó không chứa Qt binary, `.wasm`, Qt loader, plugin, QML bundle hay native installer.
- **Chủ dự án + luật sư:** nếu có phát hành native binary/Qt WASM, chọn commercial hay một open-source route và lập compliance plan riêng.
- **Kỹ sư release:** nếu phát hành native, lưu exact Qt SBOM, build/linking mode, license texts, notices, source offer/source archive và relinking/installation evidence theo route đã chọn.

## Ranh giới Arduino và firmware

Firmware chỉ khai báo tên thư viện và `ArduinoJson (7.x)` trong comment; repo không có lockfile hoặc exact board/library versions ([sketch](../../firmware/DigitCodeFirmware/DigitCodeFirmware.ino)). Bảng sau là snapshot upstream, không phải SBOM của một firmware binary cụ thể.

| Thành phần | Vai trò/provenance | License upstream quan sát | Dependency khai báo upstream |
|---|---|---|---|
| ESP32 Arduino core (`WiFi.h`, `Wire.h`) | `espressif/arduino-esp32` | LGPL-2.1 ([LICENSE](https://github.com/espressif/arduino-esp32/blob/master/LICENSE.md)) | Core và SDK còn có file/component riêng; cần scan exact board package |
| WebSocketsClient | `Links2004/arduinoWebSockets` | LGPL-2.1 ([LICENSE](https://github.com/Links2004/arduinoWebSockets/blob/master/LICENSE)) | Không khai báo dependency trong [`library.properties`](https://github.com/Links2004/arduinoWebSockets/blob/master/library.properties) |
| ArduinoJson | `bblanchon/ArduinoJson`, repo chỉ yêu cầu dòng 7.x | MIT ([LICENSE](https://github.com/bblanchon/ArduinoJson/blob/7.x/LICENSE.txt)) | Exact 7.x version chưa khóa |
| Adafruit PCF8574 | `adafruit/Adafruit_PCF8574` | BSD 3-clause text ([license.txt](https://github.com/adafruit/Adafruit_PCF8574/blob/main/license.txt)) | Adafruit BusIO ([`library.properties`](https://github.com/adafruit/Adafruit_PCF8574/blob/main/library.properties)) |
| LedControl | `wayoda/LedControl` | MIT text, copyright Eberhard Fahle ([LICENSE](https://github.com/wayoda/LedControl/blob/master/LICENSE)) | Không khai báo dependency ([`library.properties`](https://github.com/wayoda/LedControl/blob/master/library.properties)) |
| Adafruit GFX | `adafruit/Adafruit-GFX-Library` | BSD text với hai điều kiện redistribution ([license.txt](https://github.com/adafruit/Adafruit-GFX-Library/blob/master/license.txt)) | Adafruit BusIO ([`library.properties`](https://github.com/adafruit/Adafruit-GFX-Library/blob/master/library.properties)) |
| Adafruit SSD1306 | `adafruit/Adafruit_SSD1306` | BSD 3-clause text ([license.txt](https://github.com/adafruit/Adafruit_SSD1306/blob/master/license.txt)) | Adafruit GFX ([`library.properties`](https://github.com/adafruit/Adafruit_SSD1306/blob/master/library.properties)) |
| Adafruit BusIO | Transitive của PCF8574 và GFX | MIT ([LICENSE](https://github.com/adafruit/Adafruit_BusIO/blob/master/LICENSE)) | Exact version chưa khóa |

### Rủi ro

- Firmware binary thường gồm code đã link từ core/library; hai thành phần quan sát có LGPL-2.1. LGPL-2.1 §6 đặt điều kiện riêng khi phân phối executable đã link, gồm notice, license và một cơ chế để người nhận có thể sửa/relink library theo các phương án trong license ([arduinoWebSockets LICENSE, §6](https://github.com/Links2004/arduinoWebSockets/blob/master/LICENSE)).
- Repository-level license của ESP32 core không phải inventory đầy đủ cho SDK, binary blob và mọi file trong exact board package.
- Cài đặt thư viện mới nhất vào ngày build có thể thay đổi version, transitive tree, copyright và license mà không tạo diff trong repo.

### Quyết định cần chốt

- **Kỹ sư firmware:** pin ESP32 board package và mọi Arduino library; xuất direct/transitive inventory từ mỗi build release.
- **Chủ dự án:** quyết định public web release có cho tải firmware `.bin`, source bundle, native installer hay bán thiết bị đã flash hay không.
- **Kỹ sư release:** nếu câu trả lời là không, exclude toàn bộ firmware/core/library khỏi web deploy artifact và nói rõ firmware là release stream riêng.
- **Chủ dự án + luật sư:** nếu có phân phối firmware binary/thiết bị, đánh giá exact artifact theo LGPL-2.1 và mọi license per-file; chuẩn bị source, object/relinking mechanism, notices và license texts theo route đã phê duyệt.

## Dependency web chưa được chọn

### Dữ kiện nguồn

Tại snapshot không có web manifest hay lockfile, vì vậy không có cơ sở để liệt kê framework, runtime, bundler, server package, icon set hoặc transitive dependency. Một trường `license` trong package metadata cũng không tự chứng minh mọi file trong tarball hoặc mọi transitive dependency có cùng license; exact artifact vẫn phải được kiểm tra.

### Quy trình tối thiểu cho mỗi release

1. Tạo web package riêng và commit một lockfile duy nhất; build CI chỉ được dùng frozen/locked install.
2. Ghi cho mỗi direct và transitive package: tên, exact version, checksum, source URL, license expression, copyright holder, notice/license file và có được đưa vào artifact hay không.
3. Review license text của exact package tarball, không chỉ badge/README/registry label; đánh dấu `UNKNOWN`, custom license, dual license và package có file mang license khác nhau.
4. Tạo SBOM và `THIRD_PARTY_NOTICES` từ dependency tree đã khóa; giữ nguyên copyright, attribution và license text theo điều khoản của từng package.
5. Kiểm tra output sau bundling: JavaScript chunks, CSS, source maps, WASM, worker, icon, image, audio, font, vendor code và server/container image.
6. Fail CI khi manifest/lock thay đổi mà inventory/notices chưa cập nhật, hoặc khi có license chưa được policy owner phê duyệt.
7. Lưu inventory, notices, SBOM, artifact file list và kết quả review gắn với release commit/digest để có thể tái lập bằng chứng.

### Quyết định cần chốt

- **Chủ dự án:** chọn license policy cho dependency web, mục tiêu open-source hay proprietary của first-party source, và mức chấp nhận với copyleft/custom/unknown licenses.
- **Kỹ sư web:** chọn stack dựa trên khả năng khóa version, xuất full dependency graph, thu thập notice và scan build artifact; không chọn package chỉ dựa trên mức độ phổ biến.
- **Luật sư khi cần:** đọc custom/dual/copyright exceptions và quyết định tính tương thích với cách deploy cụ thể.

## Font, icon, ảnh và tài liệu

### Dữ kiện nguồn

QML hiện tại chỉ yêu cầu tên font hệ thống Menlo hoặc Courier New, không bundle font file ([ví dụ](../../UI/ScreenMenu.qml)). Audit file tracked không thấy loose webfont/image/vector asset; các badge trong [`README.md`](../../README.md) là URL từ xa, không phải asset browser app hiện tại. Tuy nhiên DOCX tracked có một ảnh JPEG nhúng và không có provenance sidecar ([`DigitCode_BaoCao_v6.docx`](../../DigitCode_BaoCao_v6.docx)).

### Rủi ro

- Font được phép cài trên máy không mặc nhiên đồng nghĩa với quyền copy font file lên CDN hoặc web-embed nó.
- Asset do designer, template, AI tool, stock service hay trang web tạo ra có thể kèm điều khoản về redistribution, attribution, trademark hoặc commercial use.
- Exclude một asset khỏi browser build không giải quyết việc asset đó vẫn đang nằm trong repo public.

### Quyết định cần chốt

- **Kỹ sư web:** ưu tiên system font stack nếu không cần brand font; nếu self-host, lưu font file gốc, license, copyright, source URL và bằng chứng web embedding/redistribution.
- **Chủ dự án:** xác minh nguồn/quyền của `image1.jpeg`; thay, xóa hoặc ghi attribution/permission đúng điều khoản trước khi tiếp tục phân phối.
- **Designer + kỹ sư release:** tạo asset register cho mọi font, icon, ảnh, audio và animation; không merge asset nếu thiếu owner/source/license/permission.

## `Decorum-inspired`: copyright và trademark

### Dữ kiện nguồn

Repo tự mô tả là `"Decorum"-inspired` trong [`README.md`](../../README.md), `kết hợp từ ý tưởng board game Decorum` trong [`PRJ_DigitCode_Master_Context.md`](../../PRJ_DigitCode_Master_Context.md), và `lấy cảm hứng` trong [`PROJECT_REPORT.md`](../../PROJECT_REPORT.md). Text search tại snapshot chỉ tìm thấy ba tham chiếu này.

Theo 17 U.S.C. §102(b), copyright không mở rộng đến idea, procedure, process, system, method of operation, concept, principle hay discovery, bất kể chúng được mô tả hoặc thể hiện như thế nào ([U.S. Copyright Office](https://www.copyright.gov/title17/92chap1.html#102)). Copyright Office cũng nói website text, artwork và photograph có thể được bảo hộ, còn facts, ideas, systems, methods và names/titles/short phrases thì không được copyright bảo hộ theo cách đó ([FAQ](https://www.copyright.gov/help/faq/faq-protect.html), [Circular 33](https://www.copyright.gov/circs/circ33.pdf)). Do đó cần tách `game mechanic/idea` khỏi `rule text, art, layout, story, audiovisual và code` thay vì dùng nhãn `inspired` để kết luận chung.

Floodgate Games hiện chào bán `Décorum: A game of passive aggressive cohabitation` trên kênh first-party ([product page](https://floodgate.games/products/decorum)). Trang này chỉ chứng minh việc sử dụng tên sản phẩm quan sát được, không tự nó chứng minh ai sở hữu mọi quyền trademark ở mọi quốc gia.

USPTO nói trademark nhận diện nguồn hàng hóa/dịch vụ; quyền không phải là quyền tuyệt đối với một từ trong mọi ngữ cảnh ([What is a trademark?](https://www.uspto.gov/trademarks/basics/what-trademark)). Đánh giá likelihood of confusion xem cả mức độ giống nhau của mark và mức độ liên quan của goods/services ([USPTO](https://www.uspto.gov/trademarks/search/likelihood-confusion)). USPTO khuyến nghị comprehensive clearance search bao gồm federal records, state/business registries, domain, international sources và common-law/internet use, không chỉ một truy vấn federal ([clearance guidance](https://www.uspto.gov/trademarks/search/comprehensive-clearance-search-similar-trademarks)). Nghiên cứu này **chưa thực hiện trademark clearance**.

### Rủi ro

- Cụm `Decorum-inspired` trên trang public có thể được đọc như một mô tả nguồn cảm hứng, so sánh sản phẩm, affiliation hoặc marketing; kết quả trademark phụ thuộc jurisdiction, cách trình bày, goods/services và bằng chứng thị trường.
- Dù mechanic không được copyright bảo hộ theo khung Hoa Kỳ, việc copy/translate rule text, hình ảnh, card/layout, character/story, audio, UI expression hoặc code vẫn là câu hỏi khác.
- Không thấy loose Decorum asset trong file tree không đủ để đánh giá substantial similarity của gameplay expression hoặc nguồn ảnh trong DOCX.

### Quyết định cần chốt

- **Product owner:** lập comparison record giữa DigitCode và Décorum cho rule text, terminology, visual layout, art, scenario/story, audiovisual và code; ghi rõ phần nào được tạo độc lập.
- **Product owner:** nếu không cần tham chiếu cho người dùng, lựa chọn kỹ thuật ít rủi ro hơn là bỏ `Decorum-inspired` khỏi UI, metadata, landing page và marketing public, trong khi giữ provenance note nội bộ. Đây là lựa chọn quản trị rủi ro, không phải kết luận rằng mọi tham chiếu đều bất hợp pháp.
- **Trademark/copyright counsel tại jurisdiction liên quan:** clearance tên/cụm từ và review bất kỳ expressive element nào có thể đến từ Décorum trước public launch.

## Định nghĩa ranh giới release

| Artifact/kênh | Điều kiện để coi là ngoài web artifact | Gate riêng nếu có phát hành |
|---|---|---|
| Browser static assets | Chỉ chứa first-party web code đã xác minh và web dependencies đã audit | Manifest/lock, SBOM, notices, file list, font/asset register |
| Web backend/container | Không mặc nhiên được coi là browser artifact; inventory image và package riêng | Nếu chứa Qt/native/other runtime thì audit theo exact image và người nhận |
| Qt desktop app | Không nằm trong static site, container download, CDN hay release attachment của web | Qt license route và compliance package riêng |
| Qt for WebAssembly | Không được sử dụng nếu mục tiêu là web không Qt | Nếu sử dụng, xem là Qt distribution và review lại toàn bộ ranh giới |
| Firmware/source/device | Không có `.bin`, board package, Arduino library, flashing bundle hay bundled device trong web offer | Firmware SBOM, exact licenses và LGPL-2.1 compliance plan riêng |
| GitHub repo | Deploy exclusion không xóa các file đang public trong Git | First-party license decision, skill notice/provenance, DOCX image review |

WebSocket/JSON chỉ là giao diện mạng. Compliance boundary phải được chứng minh bằng source lineage, dependency graph và file/artifact được chuyển cho từng nhóm người nhận.

## Checklist trước khi release

### Ownership và license first-party

- [ ] Xác định legal owner, jurisdiction và người có thẩm quyền phê duyệt release.
- [ ] Lưu contributor/employee/contractor/student agreements, assignments và permissions liên quan.
- [ ] Kiểm kê code/doc/asset từ bên ngoài và output từ công cụ có điều khoản riêng.
- [ ] Chốt bằng văn bản repo all-rights-reserved hay mang license nào; ghi rõ scope và exclusions.
- [ ] Không gắn third-party files vào root license nếu không có quyền sublicense như vậy.

### Ranh giới artifact

- [ ] Tạo web package, manifest và lockfile riêng.
- [ ] Chốt kiến trúc có hay không Qt WASM, native backend, desktop download, firmware download hoặc flashed hardware.
- [ ] Xuất file list của browser build và xác nhận không có Qt/QML/native/Arduino artifact nếu chọn clean boundary.
- [ ] Audit backend/container/native/firmware thành release stream riêng khi chúng tồn tại.

### Dependency và notices

- [ ] Pin exact version/checksum cho tất cả web dependencies và transitive dependencies.
- [ ] Pin exact Qt installation và Arduino board/library versions cho mọi artifact có phát hành.
- [ ] Review license text/per-file metadata của exact artifact, không chỉ repo-level badge.
- [ ] Tạo và review SBOM, `THIRD_PARTY_NOTICES`, license copies và copyright notices.
- [ ] Với LGPL artifact, lưu linking mode, corresponding source, relinking/object/installation evidence và notice theo route đã phê duyệt.
- [ ] Exclude agent skills/CI tooling khỏi product artifact; xử lý provenance/notice của bản copy vẫn ở repo.

### Font, asset và thương hiệu

- [ ] Lập asset register có source, owner, license/permission và attribution cho mọi font/icon/image/audio.
- [ ] Xác minh, thay hoặc xóa `word/media/image1.jpeg` trong DOCX.
- [ ] Không self-host Menlo/Courier New hoặc font khác nếu chưa có quyền web embedding/redistribution.
- [ ] So sánh DigitCode với Décorum ở mức expression, không chỉ mechanic.
- [ ] Thực hiện trademark clearance theo các thị trường release; chốt có giữ `Decorum-inspired` public hay không.

### Bằng chứng release

- [ ] Gắn SBOM, notice bundle, asset register, source offers và artifact digest với release commit.
- [ ] Có CI gate khi dependency, lockfile, asset hoặc notice thay đổi.
- [ ] Có người ký phê duyệt kỹ thuật và người ký phê duyệt ownership/legal cho checklist.
- [ ] Re-run audit cho mỗi release và mỗi kênh phân phối, không tái sử dụng vô thời hạn kết quả 2026-08-22.

## Câu hỏi mở và người chốt

| Câu hỏi | Người chốt |
|---|---|
| Ai là legal owner của code, document và thương hiệu DigitCode; dự án có được tạo trong lao động, hợp đồng hay chương trình học không? | Chủ dự án + luật sư |
| Có contributor, source copy, AI-generated output hoặc agreement nào không hiện trong Git history? | Chủ dự án |
| Repo sẽ all-rights-reserved hay cấp license nào, và license đó bao phủ file/thư mục nào? | Chủ dự án + luật sư |
| Web sẽ port logic sang stack mới hay dùng Qt for WebAssembly/native service? | Kiến trúc sư + chủ dự án |
| Public offer có kèm desktop app, firmware download hay thiết bị đã flash không? | Product owner |
| Exact web stack, registry, package manager, hosting/container và lock strategy là gì? | Kỹ sư web/platform |
| Nguồn và permission của ảnh nhúng trong DOCX là gì? | Tác giả tài liệu + chủ dự án |
| Các skill đã được import từ commit/tag nào, và MIT notice có áp dụng cho đúng revision đó không? | Repo maintainer |
| Có rule text, art, layout, terminology, scenario/story, audio hay code nào đến từ Décorum không? | Product owner + copyright counsel |
| Có tiếp tục dùng `Decorum-inspired` trong public marketing không, và clearance bao phủ những jurisdiction nào? | Product owner + trademark counsel |
| Web sẽ dùng system font hay self-host font/icon/asset nào? | Designer + kỹ sư web |

## Resolution đề xuất cho issue #5

Issue nghiên cứu có thể đóng khi tài liệu này được publish, vì nó đã xác định các dữ kiện hiện có, ranh giới release, gate và người ra quyết định. Việc đóng issue **không** có nghĩa public web release đã được legal-clear; các mục chưa check phải được đưa sang ticket implementation/release tương ứng trước launch.
