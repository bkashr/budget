# Personal Budget Program

## Overview

A comprehensive budget management application designed to handle all aspects of personal finances - going beyond standard budgeting apps by incorporating:

- Current 401k standing
- Outstanding debt tracking
- Savings accounts
- Credit card debt
- And more financial data points

## How It Works

When you receive a paycheck, you input the amount into the program and it automatically allocates funds based on user-defined percentages (with potential preset recommendations for common budget categories).

**Example:** You receive a $2,000 paycheck after taxes:
- 50% → Savings & Debt
- 15% → Groceries & Food
- 10% → Entertainment
- 5% → Clothing
- 20% → Other categories

The dashboard displays:
- Current percentage allocations for each category
- Actual dollar amounts available in each budget area
- Current savings balance
- Debt overview
- Retirement account status

## Features (Planned)

- **Category & Subcategory System:** Organize spending with main categories and subcategories
  - Example: Entertainment → Video Games, Movies, Concerts
  - Example: Food → Restaurants, Fast Food, Groceries
- **Automatic Allocation:** Input earnings and watch the budget distribute funds instantly
- **Financial Overview:** Track all accounts and debts in one place
- **Customizable Percentages:** Set your own budget rules

## Financial Data Points Tracked

### Debt/Liabilities
- **Loans**: Auto loans, personal loans, student loans, mortgages
  - Current balance, interest rate, monthly payment, due date
- **Credit Cards**: Multiple cards with different rates
  - Card name, current balance, interest rate, minimum payment, due date
- **Other Debt**: Medical bills, payday loans, family loans
  - Amount, interest rate, payment schedule

### Liquid Assets (Cash/Readily Available)
- **Checking Account**: Primary checking with current balance
- **Savings Account**: Traditional savings account balance
- **High-Yield Savings Account (HYSA)**: Better interest rates and current balance
- **Cash**: Physical cash on hand
- **Money Market Accounts**: Similar to savings but with different terms

### Investment Accounts
- **401(k)**: Employer-sponsored retirement accounts
  - Account balance, current contribution amount, employer match
- **IRA**: Traditional or Roth IRA accounts
  - Current value, contribution amounts, account type
- **Brokerage Accounts**: Individual investment accounts
  - Total value, account type, contribution schedule
- **529 Plans**: Education savings accounts
- **HSA**: Health Savings Account balance and contributions
- **CDs**: Certificates of Deposit with maturity dates

### Account Information Captured
For each account/asset, the system tracks:
- **Name/Description**: "Chase Checking", "Capital One 360 HYSA"
- **Current Balance**: The amount as of entry date
- **Interest Rate**: If applicable (loans, savings accounts)
- **Minimum Payment**: For debts only
- **Due Date**: When payments are due
- **Account Type**: Checking, Savings, Investment, etc.
- **Institution**: Bank or financial company name

## Technologies

- Python 3.x
- tkinter (GUI framework)
- SQLite (Database for financial data storage)

## Next Steps

1. Finalize the background/window design
2. Gather necessary budget sections (groceries, clothes, video games, etc.) and create subsection structure
3. Add functionality to input current finances (credit card debt, overall debt, savings, retirement, etc.)
4. Create functionality for user to input money earned at any point and immediately spread it out when user submits/confirms
5. Make the labels, font sizes, etc. all proportionate to any monitor size/window 

## Current Status

🚧 In Development - Currently creating database structure for storing comprehensive financial information (loans, credit cards, bank accounts, investments, etc.)
