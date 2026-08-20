# PROJECT SUMMARY & QUICK START GUIDE

## 📋 What You Have

A complete **Swedish Social Services Vocabulary Builder** system that:
1. **Scrapes** legislation from 3 authoritative Swedish sources
2. **Extracts** unique terminology with frequency analysis
3. **Organizes** vocabulary for professional study
4. **Tracks** meanings across Swedish → English → Italian + etymologies

---

## 🎯 The Workflow

### Phase 1: Scrape Legislation (you are here)
```
python run_multi_scraper.py
```

**What it does:**
- Downloads text from:
  - **Lagen.nu** (consolidated law with interpretations)
  - **Lagar.se** (legislative database)
  - **Infolex.se** (expert social services commentary) ⭐
- Saves to: `data/raw/web_text/`
- Creates organized sections by § (legal sections)

**Output structure:**
```
data/raw/web_text/
├── lagen_nu/
│   ├── lagen_nu_full_20260820_120000.txt
│   ├── sections/
│   │   ├── section_001.txt  (§1)
│   │   ├── section_002.txt  (§2)
│   │   └── ...
│   └── chunks/
├── lagar_se/
│   └── (same structure)
└── infolex/
    └── (same structure with expert commentary)
```

---

### Phase 2: Extract Terms
```
python run_term_extractor.py
```

**What it does:**
- Analyzes all scraped text
- Finds all unique words and phrases
- Counts how many times each appears
- Filters out Swedish stopwords (och, eller, det, etc.)
- Exports to CSV for your review

**Output:**
```
data/processed/term_analysis/
└── terms_extracted.csv
```

**CSV columns:**
| Column | Purpose |
|--------|---------|
| source | Where term came from (lagen_nu/lagar_se/infolex) |
| term | The Swedish word/phrase |
| frequency | How many times it appears |
| type | word/phrase |
| english | *You fill this in* |
| italian | *You fill this in* |
| etymology | *Latin/Greek root* |
| category | Child welfare / Abuse prevention / etc. |
| notes | Your personal notes |
| status | uncurated / keep / discard |

---

### Phase 3: Look Up Grammar (Coming Next)
```
python run_svenska_lookup.py
```

**What it will do:**
- Query svenska.se for each term
- Get pronunciation
- Get all grammar forms:
  - Singular indefinite: `ett adoptivbarn`
  - Singular definite: `adoptivbarnet`
  - Plural indefinite: `adoptivbarn`
  - Plural definite: `adoptivbarnen`
  - Plus genitives: `adoptivbarnets`, `adoptivbarnens`

---

### Phase 4: Find Etymology (Coming Next)
```
python run_etymology_finder.py
```

**What it will do:**
- Find Latin roots (e.g., "adoption" ← adoptare)
- Find Greek roots
- Link to Italian translations (from Latin roots)
- Create etymology chains

**Example:**
```
Swedish: adoptivbarn
English: adoptive child
Italian: bambino adottivo (from Latin adoptivus)
Etymology: Latin "adoptare" → adoptivus → Swedish "adoptiv"
Related: adoptiv, barn, fosterbarn, adoption
```

---

### Phase 5: Build Your Vocabulary Database (Coming Next)
```
python run_vocabulary_manager.py
```

**What it will do:**
- Create SQLite database with all information
- Allow you to curate your vocabulary
- Export to JSON/Excel/CSV
- Track your learning progress

---

## 📊 Example Output

### After Phase 1 (Web Scraping):
Raw legislation text from 3 sources, organized by legal sections.

### After Phase 2 (Term Extraction):
**Top 20 Most Frequent Terms:**

| Frequency | Term | Source |
|-----------|------|--------|
| 145 | barn | all sources |
| 98 | föräldrar | all sources |
| 87 | socialtjänst | all sources |
| 76 | vårdnad | lagen_nu, lagar_se |
| 65 | missbruk | all sources |
| 54 | misshandling | infolex, lagen_nu |
| 52 | övergrepp | all sources |
| 48 | adoptiv | lagen_nu, lagar_se |
| 42 | ekonomisk | all sources |
| 39 | svårighet | lagen_nu |
| ... | ... | ... |

### After Phase 3 (Swedish Grammar):
```
Term: adoptivbarn
Pronunciation: adoptiˋvbarn
Word class: Substantiv (noun)

Grammar forms:
- Singular indefinite: ett adoptivbarn
- Singular definite: adoptivbarnet
- Plural indefinite: adoptivbarn
- Plural definite: adoptivbarnen

Genitive forms:
- Singular indefinite genitive: ett adoptivbarns
- Singular definite genitive: adoptivbarnets
- Plural indefinite genitive: adoptivbarns
- Plural definite genitive: adoptivbarnens
```

### After Phase 4 (Etymology):
```
Term: adoptivbarn
Etymology root: Latin "adoptare" (to adopt)
Etymology path: adoptare (L) → adoptivus (L) → adoptiv (Sv)
Italian translation: bambino adottivo
Related terms: adoptiv, barn, fosterbarn, adoption
Greek connection: None found
```

### After Phase 5 (Database):
Full vocabulary entry:
```json
{
  "id": "adoptivbarn_001",
  "swedish": {
    "term": "adoptivbarn",
    "pronunciation": "adoptiˋvbarn",
    "wordClass": "substantiv",
    "grammar": {
      "singularIndefinite": "ett adoptivbarn",
      "singularDefinite": "adoptivbarnet",
      "pluralIndefinite": "adoptivbarn",
      "pluralDefinite": "adoptivbarnen"
    }
  },
  "english": {
    "translation": "adoptive child",
    "definition": "A child who has been legally adopted by parents other than biological parents"
  },
  "italian": {
    "translation": "bambino adottivo"
  },
  "etymology": {
    "language": "Latin",
    "root": "adoptivus",
    "origin": "from adoptare - to adopt",
    "path": "adoptare (L) → adoptivus (L) → adoptiv (Sv)"
  },
  "frequency": {
    "totalOccurrences": 28,
    "bySource": {
      "lagen_nu": 12,
      "lagar_se": 9,
      "infolex": 7
    }
  },
  "contexts": [
    {
      "sentence": "Adoptivbarn ska ha rätt till kontakt...",
      "section": "3 kap. 1 §",
      "source": "lagen_nu"
    }
  ],
  "category": ["child_welfare", "family_law"],
  "status": "curated",
  "notes": "Critical term in adoption procedures. Infolex commentary emphasizes importance of contact with biological parents."
}
```

---

## 🚀 How to Run

### Quick Start (Do This First):
```bash
# 1. Open terminal in your project folder
cd social-services-lexicon

# 2. Install dependencies (one time only)
pip install -r requirements.txt

# 3. Run the multi-source scraper
python run_multi_scraper.py
```

**This will:**
- Take 5-10 minutes
- Show progress as it scrapes each site
- Create `data/raw/web_text/` with organized text files
- Save results automatically

### Second Step:
```bash
# 4. Run the term extractor
python run_term_extractor.py
```

**This will:**
- Analyze all the text
- Extract ~500-1000 unique terms with frequencies
- Create CSV file in `data/processed/term_analysis/`

### Then:
- Open the CSV file in Excel/Google Sheets
- Review the extracted terms
- Mark which ones are important for your vocabulary
- Add notes about their usage

---

## 📁 Project Structure

```
social-services-lexicon/
├── README.md                           (Main documentation)
├── run_multi_scraper.py               ⭐ Run this first!
├── run_term_extractor.py              ⭐ Run this second!
├── run_svenska_lookup.py              (Coming next)
├── run_etymology_finder.py            (Coming next)
├── run_vocabulary_manager.py          (Coming next)
│
├── src/
│   ├── multi_source_scraper.py        (Scrapes 3 websites)
│   ├── term_extractor.py              (Analyzes vocabulary)
│   ├── svenska_lookup.py              (Grammar lookup - coming)
│   ├── etymology_finder.py            (Etymology lookup - coming)
│   ├── vocabulary_manager.py          (Database curation - coming)
│   ├── database.py                    (SQLite management)
│   ├── pdf_scraper.py                 (PDF support)
│   ├── chunked_downloader.py          (Large file handling)
│   └── web_text_scraper.py            (Basic web scraper)
│
├── data/
│   ├── raw/
│   │   └── web_text/                  (Scraped text)
│   │       ├── lagen_nu/
│   │       ├── lagar_se/
│   │       └── infolex/
│   │
│   └── processed/
│       ├── term_analysis/             (Extracted terms)
│       │   └── terms_extracted.csv
│       │
│       └── lexicon.db                 (Your vocabulary database)
│
└── requirements.txt                   (Python dependencies)
```

---

## ✨ Key Features

✅ **Multi-source scraping** - Get text from 3 authoritative databases
✅ **Automatic organization** - Text split by legal sections (§)
✅ **Frequency analysis** - See which terms matter most
✅ **CSV export** - Easy to review in Excel/Sheets
✅ **Professional curation** - Mark terms as keep/discard
✅ **Grammar lookup** - Full Swedish grammar (singular/plural/genitive)
✅ **Etymology tracking** - Find Latin & Greek roots
✅ **Italian translations** - Bridge to Romance language roots
✅ **Database storage** - Permanent vocabulary collection
✅ **Context examples** - See how terms are used in law

---

## 🎓 When You're Done

You'll have a professional **Social Services Vocabulary Database** with:

- **1,000+ curated Swedish terms** from social services legislation
- **Complete Swedish grammar** for each term
- **English definitions** for professional reference
- **Italian translations** (especially useful if learning Italian)
- **Latin/Greek etymologies** to understand word relationships
- **Usage context** from official legislation and expert commentary
- **Frequency data** showing which terms matter most
- **Professional categorization** (child welfare, abuse prevention, etc.)

---

## 🤔 Questions?

The system is designed to work step-by-step. Each phase builds on the previous one:

1. **Scrape** → Get raw text ✓
2. **Extract** → Find important terms ✓
3. **Lookup** → Get grammar info (coming)
4. **Etymology** → Find roots (coming)
5. **Curate** → Build your vocabulary (coming)

---

## 🎯 Ready to Start?

Run this command to begin:
```bash
python run_multi_scraper.py
```

It will scrape from all three sources and save the text. Let me know when it's done!
