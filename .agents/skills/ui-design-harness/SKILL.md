---
name: ui-design-harness
description: Use when generating or implementing HTML, CSS, Tailwind, or React UI for academic, app, or game domains and the result must be domain-specific, visually coherent, and free of generic AI templates.
---

# UI Design Harness

UIを「それらしいテンプレート」ではなく、対象ドメインに固有の視覚言語として実装するためのルール。プロジェクト固有のブランド、既存デザインシステム、ユーザーの明示指定はこのハーネスより優先する。

## Activation and design lock

1. UI実装の冒頭で `DOMAIN` を `ACADEMIC | APP | GAME` から1つ選ぶ。要件から明らかな場合は推定し、曖昧さが結果を大きく変える場合だけ確認する。
2. 最初のUIコードに、フォント・色・境界・角丸・余白をまとめた単一のDesign Token層を作る。CSS変数、Tailwind theme、またはReact theme objectのいずれか1つを使う。
3. 同一プロダクト内の画面・状態・コンポーネントは、そのToken層を参照する。画面ごとにフォントやカラーテーマを変えない。変化は情報設計とレイアウトで表現する。
4. UI部品（Button、Input、Tableなど）は再利用してよいが、画面全体のテンプレートを別画面へ機械的に複製しない。再利用するのは部品と原則であり、レイアウトの意味ではない。
5. 日本語を含む場合は、選択したフォントの日本語グリフ対応を確認し、同じ印象を保つ明示的な日本語fallbackを1つのstackに固定する。画面ごとに別のfallbackを足さない。

## Typography lock

プロダクト全体で、本文/UI用の主フォントを1系統、数値・コード用のMonoを1系統に固定する。見出し用の別フォントがドメイン上必要な場合も、製品開始時に1つ選び、画面単位で切り替えない。フォントを追加する場合は、ブランドまたは可読性の具体的な理由をコード変更と同じ場所に残す。

### ACADEMIC

- 見出し・本文: `STIX Two Text`, `Latin Modern Roman`, `Computer Modern`, `Newsreader` のいずれか。日本語は `Noto Serif JP` など同系統のserif fallback。
- 数式・記号: KaTeX / MathJaxのフォントスタックに合わせる。
- データ・コード・数値: `JuliaMono`, `IBM Plex Mono` のいずれか。
- 本文のline-heightは1.6〜1.7、段落間隔は明確に取る。

### APP

- メインUI: `Geist Sans`, `Plus Jakarta Sans`, `Inter Display` のいずれか。日本語は `Noto Sans JP` など同系統のsans fallback。
- メタデータ・数値・タイムスタンプ: `Geist Mono`, `JetBrains Mono` のいずれか。
- 見出しは `tracking-tight font-medium`、小ラベルは `text-xs uppercase tracking-wider text-neutral-400 font-semibold` を基本にする。

### GAME

- 世界観を最初にSci-Fi/CyberまたはFantasy/Epicのどちらかへ固定する。
- Sci-Fi/Cyber: `Orbitron`, `Rajdhani`, `Chakra Petch` のいずれか。
- Fantasy/Epic: `Cinzel Decorative`, `Cinzel` のいずれか。
- HUD数値・ステータス: `Share Tech Mono`, `VT323`, `Chakra Petch` のいずれか。
- Latin文字は原則uppercase、文字間は`tracking-widest`。日本語表示では可読性を優先し、無理なuppercase変換をしない。

## Domain visual grammar

### ACADEMIC — paper / technical report

- Background `#FDFCFA`, Surface `#FFFFFF`, Border `#E5E2DC`, Text `#1A1A1A`, Secondary `#595959`, Accent `#800000` または `#003366`。
- 伝統的な2段組を基本にし、図表番号付きキャプション（`Fig 1.`, `Table 2.`）を厳格に配置する。
- ドロップシャドウ、過度なホバー演出、角丸を使わない。カードは原則`rounded-none`。
- 表は上下の太線、ヘッダー下の中線、行間の罫線なしのBooktabs形式にする。
- チャートは色だけに頼らず、破線・点線・ハッチング・記号を併用する。

### APP — dense / fast product UI

- Background `#090A0F`, Surface `#12141A`, Border `rgba(255, 255, 255, 0.08)`, Text `#EDEDED`, Secondary `#8A8F98`。Accentは`#3B82F6`または`#F59E0B`の1色を単一機能へ限定する。
- 左240pxのサイドバー＋メイン領域、またはツールバー＋高密度グリッドを基本にする。
- 外側の大きな影を使わず、必要なら上端のインナーハイライト（`shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]`）で面を分離する。
- 角丸は`rounded-md`（6〜8px）で統一する。操作には`⌘K`、`Esc`などのKbd表記と高速なフィードバックを用いる。

### GAME — immersive HUD

- Background `#050508`。HUD PrimaryはSci-Fiなら`#00F0FF`、Fantasyなら`#E5A93C`。Criticalは`#FF003C`、Overlay/Glassは`rgba(10, 15, 25, 0.75)`。
- HUD要素は画面端の四隅配置を基本にし、`vw`/`vh`とアスペクト比に追従させる。
- 通常の四角形だけにせず、必要な箇所へ`clip-path: polygon(...)`などのカット形状を使う。
- ネオングロー、走査線、グリッドは世界観を補強する範囲に限定し、常時発光するだけの装飾にしない。
- HP/MPゲージ、目盛り、セグメント型リソースなど、状態が即時に読めるインジケータを優先する。

## Mutually exclusive visual presets

提示された共通テーマは混ぜず、次のプリセットとして扱う。

- `TECH_MINIMAL`: APPの既定。`#0B0C0E` / `#14161A` / `#23262D` / `#F1F3F7` / `#7E8695`、Geist系、`rounded-lg`、インナーシャドウ。
- `EDITORIAL_LIGHT`: 学術・読み物寄りの明るい既定。`#F9F8F6` / `#FFFFFF` / `#EAE8E3` / `#1E1E1E` / `#736E65`、Playfair Display / Newsreader / Cormorant Garamond系、広い余白、最小限の角丸。
- `GAME_WORLD`: GAMEのドメイン規約を優先する。

明示的なブランド指定がなければ、`DOMAIN` の規約を優先し、プリセットを補助的に選ぶ。暗いAPPトークンと明るいEDITORIALトークンを同じ画面へ混在させない。

## Absolute constraints

1. 紫〜ピンクのグラデーション、`shadow-2xl`級の巨大な外向き影、`rounded-3xl`級の過剰な角丸、意味のないglassmorphism、カードを並べただけの汎用ダッシュボードを使わない。
2. テキストへ純黒`#000000`や純白`#FFFFFF`をベタ塗りしない。Surfaceとしての白は、ドメイン規約が要求する場合のみ使う。
3. 画面ごとのフォント変更、複数の無関係なCDNフォント読み込み、絵文字をアイコン代わりにしたUIを避ける。
4. セマンティックHTML、キーボード操作、focus-visible、十分なコントラスト、レスポンシブな幅を実装する。色だけで状態を伝えない。
5. loading、empty、error、successなど主要状態を、同じTokenとコンポーネント規約で表現する。
6. 出力はHTML/CSS、Tailwind、またはReactとしてそのまま動かせる完成コードを優先し、長いデザイン解説を出さない。

## Proportionate UI validation

UI変更の検証は、まず代表的な1画面または1ルートをデスクトップ・モバイル各1状態で確認する。既存のvisual regression基盤やユーザー要件がない限り、画面ごとのsnapshotテストや新規テストファイルを増やさない。問題がなければ、見た目の不安だけを理由に検証を追加しない。
