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


Skene هي مجموعة أدوات لتحليل قاعدة الشيفرة البرمجية للنمو القائم على المنتج. تقوم بفحص قاعدة الشيفرة الخاصة بك، واكتشاف فرص النمو، وإنشاء خطط تنفيذ قابلة للتطبيق.

## البدء السريع

قم بالتثبيت وتشغيل واجهة المستخدم التفاعلية في الطرفية:

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

يرشدك المعالج خلال اختيار المزوّد، والمصادقة، والتحليل — لا حاجة لأي إعداد مسبق.

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## ماذا يفعل

- **اكتشاف المكدس التقني** -- يحدد أطر العمل وقواعد البيانات والمصادقة والنشر
- **اكتشاف ميزات النمو** -- يعثر على تدفقات التسجيل الحالية والمشاركة والدعوات والفوترة
- **سجل الميزات** -- يتتبع الميزات عبر عمليات التحليل ويربطها بحلقات النمو
- **تحليل تسرب الإيرادات** -- يكتشف فرص تحقيق الدخل المفقودة ومستويات التسعير الضعيفة
- **إنشاء خطة النمو** -- ينتج حلقات نمو مرتبة حسب الأولوية مع خرائط طريق التنفيذ
- **موجهات التنفيذ** -- يبني موجهات جاهزة للاستخدام لـ Cursor أو Claude أو أدوات الذكاء الاصطناعي الأخرى
- **نشر القياس عن بُعد** -- ينشئ عمليات ترحيل Supabase ويدفعها إلى المستودع الرئيسي
- **التحقق من الحلقات** -- يتحقق من تنفيذ متطلبات حلقة النمو
- **الدردشة التفاعلية** -- اطرح أسئلة حول قاعدة الشيفرة الخاصة بك في الطرفية

يدعم OpenAI وGemini وClaude وLM Studio وOllama وأي نقطة نهاية متوافقة مع OpenAI. تدقيق محلي مجاني متاح بدون الحاجة إلى مفتاح API.

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## التثبيت

### واجهة المستخدم في الطرفية (موصى بها)

واجهة TUI هي معالج تفاعلي يرشدك خلال سير العمل بالكامل. لا متطلبات مسبقة — يتولى المثبّت كل شيء.

```bash
# تثبيت واجهة TUI
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# تشغيلها
skene
```

### Python CLI

إذا كنت تفضل سطر الأوامر، يمكنك تشغيل Skene مباشرة باستخدام `uvx` (لا حاجة للتثبيت) أو تثبيته بشكل عام:

```bash
# تثبيت uv (إذا لم يكن لديك)
curl -LsSf https://astral.sh/uv/install.sh | sh

# تشغيل مباشر (لا حاجة للتثبيت)
uvx skene

# أو التثبيت بشكل عام
pip install skene
```

لتفاصيل استخدام CLI، راجع [الوثائق](https://www.skene.ai/resources/docs/skene).

## هيكل المستودع الأحادي

| الدليل | الوصف | اللغة | التوزيع |
|-----------|-------------|----------|-------------|
| `src/skene/` | CLI + محرك التحليل | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | معالج واجهة المستخدم التفاعلية في الطرفية | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | إضافة Cursor IDE | — | — |

واجهة TUI (`tui/`) هي تطبيق Bubble Tea يوفر تجربة معالج تفاعلية وينسّق Python CLI عبر `uvx`. كل حزمة لها خطوط CI/CD مستقلة.

## المساهمة

المساهمات مرحب بها. يرجى [فتح مشكلة](https://github.com/SkeneTechnologies/skene/issues) أو تقديم [طلب سحب](https://github.com/SkeneTechnologies/skene/pulls).

## الرخصة

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
