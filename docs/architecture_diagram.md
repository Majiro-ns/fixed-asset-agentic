# Architecture Diagrams - Image Generation Guide

> **Purpose**: Convert Mermaid diagrams to images for presentations, Zenn articles, and documentation
> **Version**: 1.0.0
> **Last Updated**: 2026-01-30

---

## Table of Contents

1. [Image Generation Methods](#1-image-generation-methods)
2. [System Architecture Diagram](#2-system-architecture-diagram)
3. [Data Flow Diagram](#3-data-flow-diagram)
4. [Agentic 5-Step Process Diagram](#4-agentic-5-step-process-diagram)
5. [Workflow Integration Diagram](#5-workflow-integration-diagram)
6. [Recommended Formats](#6-recommended-formats)
7. [Zenn Article Embedding](#7-zenn-article-embedding)

---

## 1. Image Generation Methods

### Method 1: Mermaid Live Editor (Recommended for Quick Export)

**URL**: https://mermaid.live/

**Steps**:
1. Open https://mermaid.live/ in browser
2. Paste Mermaid code into the editor
3. Click "Actions" menu (top right)
4. Select "PNG" or "SVG" to download

**Pros**: No installation required, instant preview
**Cons**: Manual process for each diagram

### Method 2: mermaid-cli (Recommended for Automation)

**Installation**:
```bash
npm install -g @mermaid-js/mermaid-cli
```

**Usage**:
```bash
# Single file conversion
mmdc -i diagram.mmd -o diagram.png -b transparent

# With custom theme
mmdc -i diagram.mmd -o diagram.svg -t dark

# Batch conversion
for f in *.mmd; do mmdc -i "$f" -o "${f%.mmd}.png"; done
```

**Options**:
| Flag | Description | Example |
|------|-------------|---------|
| `-i` | Input file | `-i arch.mmd` |
| `-o` | Output file | `-o arch.png` |
| `-t` | Theme (default/dark/forest/neutral) | `-t dark` |
| `-b` | Background color | `-b transparent` |
| `-w` | Width in pixels | `-w 1200` |
| `-H` | Height in pixels | `-H 800` |

### Method 3: draw.io (For Custom Designs)

**URL**: https://app.diagrams.net/ or Desktop app

**Steps**:
1. Open draw.io
2. Create new diagram
3. Use shapes from "Software" or "GCP" libraries
4. Export as PNG/SVG (File > Export as)

**Pros**: Full design control, GCP official icons available
**Cons**: Manual drawing required

### Method 4: VS Code Extension

**Extension**: "Markdown Preview Mermaid Support" or "Mermaid Markdown Syntax Highlighting"

**Export**: Use "Markdown PDF" extension to export with rendered diagrams

---

## 2. System Architecture Diagram

### 2.1 Full System Architecture (README.md)

```mermaid
graph TB
    A[見積書PDF] -->|Opal OCR| B[Opal JSON]
    B -->|Streamlit UI| C[ユーザー入力]
    C -->|POST /classify| D[Cloud Run<br/>FastAPI]
    D -->|Adapter| E[正規化スキーマ]
    E -->|Classifier| F{判定結果}
    F -->|CAPITAL_LIKE<br/>EXPENSE_LIKE| G[判定完了]
    F -->|GUIDANCE| H[不足情報提示]
    H -->|Vertex AI Search<br/>flagged| I[法令エビデンス]
    I -->|Citations| D
    H -->|ユーザー回答| J[再実行]
    J -->|answers| D
    D -->|diff表示| K[Before → After<br/>Decision/Confidence/Trace]
    K -->|Evidence| L[Streamlit UI<br/>結果表示]
    G --> L

    style D fill:#4285f4,stroke:#1a73e8,color:#fff
    style I fill:#ea4335,stroke:#c5221f,color:#fff
    style F fill:#fbbc04,stroke:#f9ab00,color:#000
    style K fill:#34a853,stroke:#137333,color:#fff
```

**Export filename**: `architecture_full.png` or `architecture_full.svg`

### 2.2 Layered Architecture (technical_explanation.md)

```mermaid
graph TB
    subgraph Input["入力層"]
        A[見積書PDF]
        B[Opal JSON]
    end

    subgraph Core["コア処理層"]
        C[PDF Extract<br/>pdf_extract.py]
        D[Adapter<br/>adapter.py]
        E[Classifier<br/>classifier.py]
        F[Policy<br/>policy.py]
    end

    subgraph Output["出力層"]
        G{判定結果}
        H[CAPITAL_LIKE<br/>資産寄り]
        I[EXPENSE_LIKE<br/>費用寄り]
        J[GUIDANCE<br/>要確認]
    end

    subgraph GCP["Google Cloud"]
        K[Document AI]
        L[Vertex AI Search]
        M[Cloud Run]
    end

    A -->|USE_DOCAI=1| K
    K --> C
    A -->|PyMuPDF/pdfplumber| C
    B --> D
    C --> D
    D --> E
    F --> E
    E --> G
    G --> H
    G --> I
    G --> J
    J -->|法令検索| L

    style J fill:#fbbc04,stroke:#f9ab00,color:#000
    style K fill:#4285f4,stroke:#1a73e8,color:#fff
    style L fill:#ea4335,stroke:#c5221f,color:#fff
    style M fill:#34a853,stroke:#137333,color:#fff
```

**Export filename**: `architecture_layered.png` or `architecture_layered.svg`

---

## 3. Data Flow Diagram

### 3.1 Processing Pipeline

```mermaid
flowchart LR
    subgraph Input["入力"]
        PDF[PDF File]
        JSON[Opal JSON]
    end

    subgraph Extract["抽出"]
        DocAI[Document AI]
        PyMuPDF[PyMuPDF]
    end

    subgraph Transform["変換"]
        Adapter[Adapter<br/>正規化]
        Policy[Policy<br/>適用]
    end

    subgraph Classify["判定"]
        Classifier[Classifier<br/>3値判定]
    end

    subgraph Output["出力"]
        CAPITAL[CAPITAL_LIKE]
        EXPENSE[EXPENSE_LIKE]
        GUIDANCE[GUIDANCE]
    end

    PDF -->|USE_DOCAI=1| DocAI
    PDF -->|fallback| PyMuPDF
    DocAI --> Adapter
    PyMuPDF --> Adapter
    JSON --> Adapter
    Adapter --> Classifier
    Policy --> Classifier
    Classifier --> CAPITAL
    Classifier --> EXPENSE
    Classifier --> GUIDANCE

    style GUIDANCE fill:#fbbc04,stroke:#f9ab00,color:#000
    style DocAI fill:#4285f4,stroke:#1a73e8,color:#fff
```

**Export filename**: `dataflow_pipeline.png`

### 3.2 API Request/Response Flow

```mermaid
sequenceDiagram
    participant U as User/UI
    participant API as Cloud Run API
    participant C as Classifier
    participant V as Vertex AI Search

    U->>API: POST /classify (Opal JSON)
    API->>C: classify_document()

    alt Clear Case
        C-->>API: CAPITAL_LIKE or EXPENSE_LIKE
        API-->>U: Response (decision, evidence)
    else Ambiguous Case
        C-->>API: GUIDANCE
        API->>V: search_citations(query)
        V-->>API: citations[]
        API-->>U: Response (GUIDANCE, missing_fields, why_missing_matters)
        U->>API: POST /classify (with answers)
        API->>C: classify_document(answers)
        C-->>API: CAPITAL_LIKE or EXPENSE_LIKE
        API-->>U: Response (decision, diff)
    end
```

**Export filename**: `dataflow_sequence.png`

---

## 4. Agentic 5-Step Process Diagram

### 4.1 Flowchart Version

```mermaid
flowchart TD
    START([明細入力]) --> STEP1

    subgraph STEP1["Step 1: 止まる（GUIDANCE）"]
        A1{判断が<br/>割れる?}
    end

    subgraph STEP2["Step 2: 根拠提示"]
        A2[Evidence表示<br/>Missing Fields提示]
    end

    subgraph STEP3["Step 3: 質問"]
        A3[Why Missing Matters<br/>Quick-pick / Form]
    end

    subgraph STEP4["Step 4: 再実行"]
        A4[answers付きで<br/>再分類]
    end

    subgraph STEP5["Step 5: 差分保存"]
        A5[DIFF Card表示<br/>Before → After]
    end

    A1 -->|Yes| A2
    A1 -->|No| RESULT1([CAPITAL_LIKE<br/>or EXPENSE_LIKE])
    A2 --> A3
    A3 --> A4
    A4 --> A5
    A5 --> RESULT2([最終判定])

    style A1 fill:#fbbc04,stroke:#f9ab00,color:#000
    style A2 fill:#e8f0fe,stroke:#4285f4,color:#000
    style A3 fill:#fce8e6,stroke:#ea4335,color:#000
    style A4 fill:#e6f4ea,stroke:#34a853,color:#000
    style A5 fill:#f3e8fd,stroke:#9334e6,color:#000
```

**Export filename**: `agentic_5step_flow.png`

### 4.2 Timeline Version

```mermaid
timeline
    title Agentic 5-Step Process
    section Step 1
        止まる : 判断が割れる可能性を検出
               : GUIDANCE として停止
    section Step 2
        根拠提示 : Evidence パネル表示
                : Missing Fields リスト
    section Step 3
        質問 : Why Missing Matters 説明
            : ユーザーに確認を促す
    section Step 4
        再実行 : answers を受け取り
               : 再分類を実行
    section Step 5
        差分保存 : Decision/Confidence/Trace
                 : Before → After 比較
```

**Export filename**: `agentic_5step_timeline.png`

---

## 5. Workflow Integration Diagram

### 5.1 Business Process Integration

```mermaid
graph LR
    A[見積受領] --> B[Asset Agentic判定]
    B --> C{GUIDANCE?}
    C -->|Yes| D[人間確認]
    C -->|No| E[承認ワークフロー]
    D --> E
    E --> F[会計システム連携]
    F --> G[固定資産台帳]

    style C fill:#fbbc04,stroke:#f9ab00,color:#000
    style D fill:#e8f0fe,stroke:#4285f4,color:#000
```

**Export filename**: `workflow_integration.png`

### 5.2 Multi-Agent Future Vision

```mermaid
graph TB
    subgraph Agents["自律エージェント"]
        A1[DocumentAgent<br/>帳票受領・分類]
        A2[ClassificationAgent<br/>3値判定]
        A3[EvidenceAgent<br/>根拠検索]
        A4[ApprovalAgent<br/>承認フロー]
        A5[AuditAgent<br/>監査証跡]
    end

    subgraph Platform["Agentic Decision Support Platform"]
        P1[Stop-first Engine]
        P2[Evidence Store]
        P3[Audit Trail]
    end

    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
    A1 --> P1
    A2 --> P1
    A3 --> P2
    A5 --> P3

    style P1 fill:#4285f4,stroke:#1a73e8,color:#fff
```

**Export filename**: `workflow_multiagent.png`

---

## 6. Recommended Formats

### 6.1 Format Comparison

| Format | Use Case | Pros | Cons |
|--------|----------|------|------|
| **PNG** | Presentation, Web | Universal support, raster quality | No scaling |
| **SVG** | Web, High-DPI | Scalable, small file size | IE11 issues |
| **PDF** | Print, Documentation | High quality print | Not web-friendly |

### 6.2 Recommended Settings

**For Presentations (PowerPoint/Google Slides)**:
- Format: PNG
- Width: 1920px (Full HD)
- Background: White or Transparent
- DPI: 150

**For Web/Zenn Articles**:
- Format: SVG (preferred) or PNG
- Width: 800-1200px
- Background: Transparent
- Optimize: Use SVGO for SVG, TinyPNG for PNG

**For Print/PDF**:
- Format: SVG or PDF
- DPI: 300
- Background: White

### 6.3 Export Commands (mermaid-cli)

```bash
# Presentation quality (PNG)
mmdc -i diagram.mmd -o diagram.png -w 1920 -b white

# Web quality (SVG)
mmdc -i diagram.mmd -o diagram.svg -b transparent

# High-DPI (PNG 2x)
mmdc -i diagram.mmd -o diagram@2x.png -w 2400 -b transparent
```

---

## 7. Zenn Article Embedding

### 7.1 Method A: Direct Mermaid (Recommended)

Zenn natively supports Mermaid. Use fenced code blocks:

~~~markdown
```mermaid
graph LR
    A[入力] --> B[処理] --> C[出力]
```
~~~

**Pros**: No image hosting needed, always up-to-date
**Cons**: Limited styling control

### 7.2 Method B: Image Embedding

Upload images to Zenn or external hosting:

```markdown
![System Architecture](/images/architecture_full.png)
*Figure 1: System Architecture Overview*
```

**Zenn Image Upload**:
1. Drag & drop image in Zenn editor
2. Image is hosted on Zenn CDN
3. URL format: `https://storage.googleapis.com/zenn-user-upload/...`

### 7.3 Method C: GitHub Raw URL

Host images in GitHub repository:

```markdown
![Architecture](https://raw.githubusercontent.com/user/repo/main/docs/images/architecture.png)
```

### 7.4 Best Practices for Zenn

1. **Use Mermaid directly** for simple diagrams
2. **Use images** for complex diagrams or custom styling
3. **Add alt text** for accessibility
4. **Include figure captions** for context
5. **Keep image width under 800px** for mobile readability

### 7.5 Example Zenn Article Structure

```markdown
# Fixed Asset Agentic System

## システム構成

Asset Agenticは以下の構成で動作します。

```mermaid
graph TB
    A[PDF] --> B[API] --> C{判定}
    C --> D[CAPITAL_LIKE]
    C --> E[EXPENSE_LIKE]
    C --> F[GUIDANCE]
```

## Agentic 5-Step Process

![Agentic 5-Step](/images/agentic_5step_flow.png)
*Figure 2: GUIDANCE発生時の5ステップ処理フロー*

詳細は以下の通りです...
```

---

## Appendix: File Naming Convention

| Diagram Type | Filename Pattern | Example |
|--------------|------------------|---------|
| Architecture | `architecture_{variant}.{ext}` | `architecture_full.svg` |
| Data Flow | `dataflow_{type}.{ext}` | `dataflow_pipeline.png` |
| Agentic Process | `agentic_{variant}.{ext}` | `agentic_5step_flow.png` |
| Workflow | `workflow_{context}.{ext}` | `workflow_integration.svg` |

**Recommended directory structure**:
```
docs/
├── images/
│   ├── architecture_full.svg
│   ├── architecture_layered.png
│   ├── dataflow_pipeline.png
│   ├── agentic_5step_flow.png
│   └── workflow_integration.svg
└── architecture_diagram.md  (this file)
```

---

*Generated for: 第4回 Agentic AI Hackathon with Google Cloud*
