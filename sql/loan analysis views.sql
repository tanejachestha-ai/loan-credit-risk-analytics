-- ============================================================
-- LOAN CREDIT RISK ANALYTICS
-- SQL ANALYTICAL VIEWS
-- ============================================================


-- ============================================================
-- 1. Overall Portfolio Summary
-- ============================================================

CREATE VIEW dbo.vw_overall_portfolio_summary AS

SELECT
    COUNT(*) AS Total_Applications,
    SUM(CAST(loan_amount AS BIGINT)) AS Total_Loan_Amount,
    AVG(CAST(loan_amount AS FLOAT)) AS AVG_Loan_Amount

FROM dbo.loan_cleaned_data;


-- ============================================================
-- 2. Loan Status Breakdown
-- ============================================================

CREATE VIEW dbo.vw_loan_status_breakdown AS

SELECT
    loan_status,
    COUNT(*) AS Total_Applications,
    SUM(CAST(loan_amount AS BIGINT)) AS Total_loan_amount

FROM dbo.loan_cleaned_data

GROUP BY loan_status;


-- ============================================================
-- 3. Credit Risk Exposure
-- ============================================================

CREATE VIEW dbo.vw_credit_risk_exposure AS

SELECT
    credit_risk_band,
    COUNT(*) AS total_applications,

    SUM(
        CASE
            WHEN loan_status = 'Approved' THEN 1
            ELSE 0
        END
    ) AS approved_count,

    SUM(CAST(loan_amount AS BIGINT)) AS total_loan_amount,

    ROUND(
        AVG(CAST(cibil_score AS FLOAT)),
        2
    ) AS Avg_cibil_score

FROM dbo.loan_cleaned_data

GROUP BY credit_risk_band;


-- ============================================================
-- 4. High Income + High CIBIL Borrowers
-- ============================================================

CREATE VIEW dbo.vw_Avg_income_High_Cibil AS

SELECT
    loan_id,
    income_annum,
    loan_amount,
    cibil_score,
    loan_status

FROM dbo.loan_cleaned_data

WHERE income_annum > (
    SELECT AVG(CAST(income_annum AS FLOAT))
    FROM dbo.loan_cleaned_data
)

AND cibil_score >= 700;


-- ============================================================
-- 5. Education Status Analysis
-- ============================================================

CREATE VIEW dbo.vw_education_status_analysis AS

SELECT
    education,
    loan_status,
    COUNT(*) AS Total_applications,
    SUM(CAST(loan_amount AS BIGINT)) AS Total_loan_Amount

FROM dbo.loan_cleaned_data

GROUP BY education, loan_status;


-- ============================================================
-- 6. Wealth Segmentation
-- ============================================================

CREATE VIEW dbo.vw_wealth_segmentation AS

WITH PortfolioAverages AS (

    SELECT
        AVG(CAST(residential_assets_value AS FLOAT)) AS avg_res_asset,
        AVG(CAST(commercial_assets_value AS FLOAT)) AS avg_com_asset,
        AVG(CAST(luxury_assets_value AS FLOAT)) AS avg_lux_asset,
        AVG(CAST(bank_asset_value AS FLOAT)) AS avg_bank_asset

    FROM dbo.loan_cleaned_data
)

SELECT
    l.loan_id,
    l.loan_amount,
    l.residential_assets_value,
    p.avg_res_asset,

    CASE
        WHEN l.residential_assets_value > p.avg_res_asset
            THEN 'Above Average Wealth'
        ELSE 'Below Average Wealth'
    END AS wealth_status

FROM dbo.loan_cleaned_data l

CROSS JOIN PortfolioAverages p

WHERE l.loan_status = 'Approved';


-- ============================================================
-- 7. Loan Running Total & Moving Average
-- ============================================================

CREATE VIEW dbo.vw_loan_running_totals AS

SELECT
    loan_id,
    cibil_score,
    loan_amount,

    SUM(
        CAST(loan_amount AS BIGINT)
    ) OVER (
        ORDER BY cibil_score
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total_loan,

    AVG(
        CAST(loan_amount AS FLOAT)
    ) OVER (
        ORDER BY cibil_score
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    ) AS moving_avg_loan

FROM dbo.loan_cleaned_data;


-- ============================================================
-- 8. Top 10 Loans
-- ============================================================

CREATE VIEW dbo.vw_top_10_loans AS

SELECT TOP 10 *

FROM dbo.loan_cleaned_data;


-- ============================================================
-- 9. Top Ranked Loans by Education
-- ============================================================

CREATE VIEW dbo.vw_top_ranked_loans_by_education AS

SELECT *

FROM (

    SELECT
        loan_id,
        education,
        self_employed,
        income_annum,
        loan_amount,
        loan_status,

        DENSE_RANK() OVER (
            PARTITION BY education
            ORDER BY loan_amount DESC
        ) AS loan_rank

    FROM dbo.loan_cleaned_data

) AS RankedLoans

WHERE loan_rank <= 5;


-- ============================================================
-- 10. Loan Analysis - Top 10
-- ============================================================

CREATE VIEW dbo.loan_analysis AS

SELECT TOP 10 *

FROM dbo.loan_cleaned_data;
