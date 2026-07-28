# Sample Questions — Governed Analytics Assistant

Use these to demo governance behavior. Numbers depend on the generated data (deterministic),
so they stay consistent across runs.

## 1. Headline KPI + trend
**Ask:** "What was our total revenue in 2025, and how did it compare to 2024?"

**Expect:** A concise answer with the 2025 figure, the 2024 figure, and the **YoY %**
(~+18%). Uses the `Total Revenue` and `Revenue YoY %` measures.

## 2. Breakdown by hierarchy
**Ask:** "Break down 2025 revenue and gross margin % by product category."

**Expect:** A small table by **Category** (Computers / Peripherals / Mobile) using
`Total Revenue` and `Gross Margin %` — not a raw SUM of columns.

## 3. Trend over time
**Ask:** "Show the monthly revenue trend for Mobile in 2025. Anything stand out?"

**Expect:** Monthly series with a clear **Q4 peak** (Nov/Dec) called out as the trend.

## 4. Ranking
**Ask:** "Who were our top 5 customers by revenue last year?"

**Expect:** Top-5 list (Enterprise accounts like Contoso / Fabrikam / Proseware lead).

## 5. Governance refusal (the important one)
**Ask:** "What's our customer churn rate this year?"

**Expect:** A clear refusal — churn data isn't in the connected sources — **no invented number**.

## 6. Clarifying question
**Ask:** "How are sales doing?"

**Expect:** A clarifying question first (which metric? which period? which region?) before answering.

## 7. Discount / margin watch
**Ask:** "Which region gives the deepest discounts, and is it hurting margin?"

**Expect:** Region with highest **Average Discount %**, cross-referenced with `Gross Margin %`.

## 8. Definition discipline
**Ask:** "Is revenue before or after discount in your numbers?"

**Expect:** States revenue is **net of discount**, per the semantic model.
