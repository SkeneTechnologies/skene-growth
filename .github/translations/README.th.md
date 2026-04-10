<p align="center">
  <a href="../../README.md">English</a> |
  <a href="README.zh.md">简体中文</a> |
  <a href="README.zht.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.it.md">Italiano</a> |
  <a href="README.da.md">Dansk</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.pl.md">Polski</a> |
  <a href="README.ru.md">Русский</a> |
  <a href="README.bs.md">Bosanski</a> |
  <a href="README.ar.md">العربية</a> |
  <a href="README.no.md">Norsk</a> |
  <a href="README.br.md">Português (Brasil)</a> |
  <a href="README.th.md">ไทย</a> |
  <a href="README.tr.md">Türkçe</a> |
  <a href="README.uk.md">Українська</a> |
  <a href="README.bn.md">বাংলা</a> |
  <a href="README.gr.md">Ελληνικά</a> |
  <a href="README.vi.md">Tiếng Việt</a> |
  <a href="README.fi.md">Suomi</a> |
  <a href="README.sv.md">Svenska</a>
</p>

<p align="center">
  <img width="4000" height="800" alt="Skene_git" src="https://github.com/user-attachments/assets/2be11c04-6b98-4e26-8905-bf3250c4addb" />
  <a href="https://www.skene.ai"><img width="120" height="42" alt="website" src="https://github.com/user-attachments/assets/8ae8c68f-eeb5-411f-832f-6b6818bd2c34"></a>
  <a href="https://www.skene.ai/resources/docs/skene"><img width="120" height="42" alt="docs" src="https://github.com/user-attachments/assets/f847af52-0f6f-4570-9a48-1b7c8f4f0d7a"></a>
  <a href="https://www.skene.ai/resources/blog"><img width="100" height="42" alt="blog" src="https://github.com/user-attachments/assets/8c62e3b8-39a8-43f6-bb0b-f00b118aff82"></a>
  <a href="https://www.reddit.com/r/plgbuilders/"><img width="153" height="42" alt="reddit" src="https://github.com/user-attachments/assets/b420ea50-26e3-40fe-ab34-ac179f748357"></a>
</p>


Skene เป็นชุดเครื่องมือวิเคราะห์โค้ดเบสสำหรับการเติบโตที่นำโดยผลิตภัณฑ์ มันสแกนโค้ดเบสของคุณ ตรวจจับโอกาสในการเติบโต และสร้างแผนการดำเนินงานที่นำไปปฏิบัติได้จริง

## เริ่มต้นอย่างรวดเร็ว

ติดตั้งและเปิดใช้งานอินเทอร์เฟซเทอร์มินัลแบบโต้ตอบ:

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

ตัวช่วยจะนำคุณผ่านการเลือกผู้ให้บริการ การยืนยันตัวตน และการวิเคราะห์ -- ไม่จำเป็นต้องตั้งค่าล่วงหน้า

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## สิ่งที่มันทำ

- **ตรวจจับ Tech Stack** -- ระบุเฟรมเวิร์ก ฐานข้อมูล การยืนยันตัวตน การปรับใช้งาน
- **ค้นพบฟีเจอร์การเติบโต** -- ค้นหาโฟลว์การสมัครสมาชิก การแชร์ การเชิญ การเรียกเก็บเงินที่มีอยู่
- **ทะเบียนฟีเจอร์** -- ติดตามฟีเจอร์ข้ามการวิเคราะห์แต่ละครั้ง เชื่อมโยงกับลูปการเติบโต
- **วิเคราะห์การรั่วไหลของรายได้** -- ตรวจพบการสร้างรายได้ที่ขาดหายไปและระดับราคาที่อ่อนแอ
- **สร้างแผนการเติบโต** -- สร้างลูปการเติบโตที่จัดลำดับความสำคัญพร้อมแผนงานการดำเนินการ
- **พรอมต์สำหรับการดำเนินการ** -- สร้างพรอมต์พร้อมใช้งานสำหรับ Cursor, Claude หรือเครื่องมือ AI อื่น ๆ
- **ปรับใช้เทเลเมทรี** -- สร้างการย้ายข้อมูล Supabase และพุชไปยังอัปสตรีม
- **ตรวจสอบลูป** -- ยืนยันว่าข้อกำหนดของลูปการเติบโตได้รับการดำเนินการแล้ว
- **แชทแบบโต้ตอบ** -- ถามคำถามเกี่ยวกับโค้ดเบสของคุณในเทอร์มินัล

รองรับ OpenAI, Gemini, Claude, LM Studio, Ollama และเอนด์พอยต์ที่เข้ากันได้กับ OpenAI ทุกประเภท มีการตรวจสอบในเครื่องฟรีโดยไม่ต้องใช้คีย์ API

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## การติดตั้ง

### อินเทอร์เฟซเทอร์มินัล (แนะนำ)

TUI เป็นตัวช่วยแบบโต้ตอบที่นำคุณผ่านขั้นตอนการทำงานทั้งหมด ไม่มีข้อกำหนดเบื้องต้น -- ตัวติดตั้งจัดการทุกอย่าง

```bash
# ติดตั้ง TUI
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# เปิดใช้งาน
skene
```

### Python CLI

หากคุณต้องการใช้บรรทัดคำสั่ง คุณสามารถเรียกใช้ Skene โดยตรงด้วย `uvx` (ไม่ต้องติดตั้ง) หรือติดตั้งแบบทั่วไป:

```bash
# ติดตั้ง uv (หากคุณยังไม่มี)
curl -LsSf https://astral.sh/uv/install.sh | sh

# เรียกใช้โดยตรง (ไม่ต้องติดตั้ง)
uvx skene

# หรือติดตั้งแบบทั่วไป
pip install skene
```

สำหรับรายละเอียดการใช้งาน CLI ดู[เอกสารประกอบ](https://www.skene.ai/resources/docs/skene)

## โครงสร้าง Monorepo

| ไดเรกทอรี | คำอธิบาย | ภาษา | การแจกจ่าย |
|-----------|-------------|----------|-------------|
| `src/skene/` | CLI + เอนจินวิเคราะห์ | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | ตัวช่วยอินเทอร์เฟซเทอร์มินัลแบบโต้ตอบ | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | ปลั๊กอิน Cursor IDE | — | — |

TUI (`tui/`) เป็นแอป Bubble Tea ที่มอบประสบการณ์ตัวช่วยแบบโต้ตอบและจัดการ Python CLI ผ่าน `uvx` แต่ละแพ็กเกจมีไปป์ไลน์ CI/CD อิสระ

## การมีส่วนร่วม

ยินดีรับการมีส่วนร่วม กรุณา[เปิด issue](https://github.com/SkeneTechnologies/skene/issues) หรือส่ง [pull request](https://github.com/SkeneTechnologies/skene/pulls)

## สัญญาอนุญาต

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
