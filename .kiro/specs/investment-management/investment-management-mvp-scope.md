# Investment Management MVP - Simplified Scope

## Decision: Defer Tax Jurisdictions to Future Plugin

After review, we've decided to **simplify the MVP** by removing international tax jurisdiction support. This will be developed as a **separate plugin later**.

---

## MVP Scope (What's Included)

### Core Investment Tracking
✅ **Portfolio Management**
- Create multiple portfolios (TAXABLE, RETIREMENT, BUSINESS)
- Track portfolio names and types
- Multi-portfolio support per tenant

✅ **Holdings Management**
- Track stocks, bonds, ETFs, mutual funds, cash
- Record quantity, cost basis, current price
- Support for multiple holdings per portfolio

✅ **Transaction Recording**
- Buy, sell, dividend, interest, fee, transfer, contribution
- Complete transaction history
- Automatic holding updates

✅ **Performance Analytics**
- Total return calculations (inception-to-date only in MVP)
- Unrealized and realized gains
- Portfolio value tracking

✅ **Asset Allocation**
- Breakdown by asset class (stocks, bonds, cash, real estate, commodities)
- Percentage calculations
- Visual allocation data

✅ **Dividend Tracking**
- Dividend payment history
- Income aggregation
- Date range filtering

✅ **Basic Tax Data**
- Realized capital gains (raw data)
- Dividend income (raw data)
- Transaction export for accountants
- **No jurisdiction-specific rules or classifications**

✅ **AI Integration**
- MCP assistant queries
- Natural language investment questions
- Portfolio summaries and insights

✅ **Multi-Tenant & Security**
- Tenant isolation
- Commercial license requirement
- Role-based access control

---

## What's Deferred (Future Plugin)

### Tax Jurisdiction Plugin (Phase 2)

❌ **Not in MVP:**
- Country-specific tax rules (US, Canada, UK, Australia, etc.)
- Short-term vs long-term capital gains classification
- Jurisdiction-specific dividend classifications
- Country-specific portfolio types (IRA, 401k, RRSP, TFSA, ISA, etc.)
- Tax report formatting by jurisdiction
- Inclusion rate calculations (50% for Canada, etc.)
- Holding period rules (365 days US, 12 months Australia, etc.)
- FIFO cost basis tracking (MVP uses simple average cost)
- Multi-period performance (1W, 1M, 1Y) - requires price history

**Why Defer:**
1. **Faster MVP launch** - Get core tracking working first
2. **Simpler implementation** - Less code, fewer edge cases
3. **Better product strategy** - Validate core value before adding complexity
4. **Cleaner architecture** - Tax rules as separate plugin is more modular
5. **Reduced risk** - Tax rules are complex and change frequently
6. **Market validation** - Learn which countries users actually need

---

## Simplified Data Models

### Portfolio (MVP)
```python
class Portfolio:
    id: UUID
    tenant_id: UUID
    name: str
    portfolio_type: PortfolioType  # TAXABLE, RETIREMENT, BUSINESS
    created_at: datetime
    updated_at: datetime
    is_archived: bool
```

**Removed fields:**
- ~~tax_jurisdiction~~
- ~~custom_portfolio_type~~

### Portfolio Types (MVP)
```python
class PortfolioType(Enum):
    TAXABLE = "taxable"
    RETIREMENT = "retirement"  # Generic retirement account
    BUSINESS = "business"
```

**Removed types:**
- ~~TRADITIONAL_IRA, ROTH_IRA, 401K, SEP_IRA, SOLO_401K~~ (US-specific)
- ~~RRSP, TFSA, RRIF, RESP~~ (Canada-specific)
- ~~ISA, SIPP~~ (UK-specific)
- ~~SUPERANNUATION~~ (Australia-specific)

### Dividend Types (MVP)
```python
class DividendType(Enum):
    ORDINARY = "ordinary"  # MVP uses single type
```

**Removed types:**
- ~~QUALIFIED, NON_QUALIFIED~~ (US-specific, deferred to Phase 2)
- ~~ELIGIBLE, NON_ELIGIBLE~~ (Canada-specific, deferred to Phase 2)

---

## What Users Can Do (MVP)

### Track Investments
- Create portfolios for different purposes (taxable, retirement, business)
- Add holdings with purchase price and quantity
- Record all transactions (buy, sell, dividend, etc.)
- Update current prices manually

### Analyze Performance
- See total portfolio value
- Calculate gains and losses
- View asset allocation
- Track dividend income
- View inception-to-date return

### Prepare for Taxes
- Export transaction history (CSV/JSON)
- See realized capital gains (raw amounts)
- See dividend income (raw amounts)
- Provide data to accountant/tax software
- **Users handle tax classification themselves**

### AI Assistance
- "What's my portfolio performance?"
- "Show me my dividend income"
- "What are my largest holdings?"
- "How is my asset allocation?"

---

## Future: Tax Jurisdiction Plugin

When ready, we'll create a **separate plugin**:

### Plugin Name
`investment-tax-jurisdictions`

### Features
- Implements tax rules for multiple countries
- Adds jurisdiction field to portfolios
- Adds country-specific portfolio types
- Classifies capital gains (short/long-term)
- Classifies dividends (qualified/eligible/etc.)
- Generates jurisdiction-specific tax reports
- Applies inclusion rates
- Formats for local tax forms

### Jurisdictions (Phase 2)
- United States (US)
- Canada (CA)
- United Kingdom (GB)
- Australia (AU)
- More as needed

### Benefits of Separate Plugin
- **Optional feature** - Users only install if needed
- **Independent development** - Can be built/tested separately
- **Community contributions** - Others can add jurisdictions
- **Licensing flexibility** - Could be premium add-on
- **Easier maintenance** - Tax rule changes don't affect core
- **Reduced complexity** - Core stays simple

---

## Migration Path

### For MVP Users
1. Use generic portfolio types (TAXABLE, RETIREMENT, BUSINESS)
2. Track all transactions
3. Export data for tax preparation
4. Work with accountant for tax classification

### When Tax Plugin Available
1. Install tax jurisdiction plugin
2. Select country for each portfolio
3. System applies jurisdiction-specific rules
4. Get formatted tax reports

### Data Compatibility
- All MVP data remains valid
- No data migration needed
- Tax plugin adds classification layer
- Existing transactions get classified retroactively

---

## Implementation Benefits

### Faster Time to Market
- **MVP**: ~15-18 tasks (vs 21 with tax jurisdictions)
- **Complexity**: Significantly reduced
- **Testing**: Fewer edge cases
- **Launch**: Weeks sooner

### Cleaner Code
- No tax jurisdiction registry
- No country-specific logic
- Simpler enumerations
- Easier to understand

### Better UX
- Simpler portfolio creation
- Less overwhelming for users
- Focus on core value (tracking)
- Tax complexity added only when needed

### Reduced Risk
- No risk of incorrect tax calculations
- No legal liability for tax advice
- Users work with their own tax professionals
- System provides data, not tax guidance

---

## User Communication

### MVP Messaging
"Track your investment portfolios, analyze performance, and export data for tax preparation. YourFinanceWORKS provides the tracking - you handle the tax classification with your accountant."

### Future Plugin Messaging
"Upgrade to Tax Jurisdiction Plugin for automatic tax classification, country-specific rules, and formatted tax reports for US, Canada, UK, Australia, and more."

---

## Technical Debt: None

This is **not technical debt** - it's a **strategic product decision**:
- ✅ Architecture supports future plugin
- ✅ Database schema extensible
- ✅ No refactoring needed later
- ✅ Clean separation of concerns

---

## Conclusion

By deferring tax jurisdictions to a future plugin, we:
1. **Ship faster** - Get MVP to users sooner
2. **Reduce complexity** - Simpler code, fewer bugs
3. **Validate market** - Learn what users actually need
4. **Stay flexible** - Add jurisdictions based on demand
5. **Maintain quality** - Focus on core features first

The investment management MVP will provide **real value** for users who want to track portfolios and analyze performance, while keeping the door open for sophisticated tax features later.

**Next Step**: Begin implementing the simplified MVP spec! 🚀
