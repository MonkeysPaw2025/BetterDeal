# BetterDeal - Property Investment Analyzer

BetterDeal helps you find better real estate deals. It's an MCP server and web app that analyzes property investments from Zillow and Realtor.com links, powered by the RentCast API for property data, valuations, and market statistics.

## Features

### MCP Server
- Claude Desktop integration via Model Context Protocol (MCP)
- Property data, valuations, and market statistics from the RentCast API

### Web App
- **Web-based property analysis tool**
- Paste Zillow or Realtor.com URLs to analyze properties
- Multiple investment strategies: Rental, Flip, BRRRR, House Hack, Long-term Appreciation
- Support for different loan types: Conventional, FHA, VA, USDA
- Comprehensive financial analysis including:
  - Cash flow calculations
  - Cash-on-cash return
  - Cap rate
  - Rental yield
  - Debt service coverage ratio (DSCR)
  - Investment scores and recommendations

## Requirements

* Python 3.12 or higher
* Model Context Protocol (MCP) Python SDK
* httpx
* python-dotenv
* fastapi (for web app)
* uvicorn (for web app)
* pydantic (for web app)

## Setup

### 1. Install uv (recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone this repository

```bash
git clone https://github.com/yourusername/betterdeal.git
cd betterdeal
```

### 3. Create and activate a virtual environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
# Option 1: Using uv (recommended)
uv sync

# Option 2: Using pip with requirements.txt
pip install -r requirements.txt

# Option 3: Install as editable package
uv pip install -e .
```

### 5. Set up environment variables

Create a `.env` file in the project root with your RentCast API key:

```bash
RENTCAST_API_KEY=your_api_key_here
```

## Usage

### 1. Configure Claude Desktop

First, install the MCP CLI globally:

```bash
uv tool install "mcp[cli]"
```

Then add this server to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "BetterDeal": {
      "command": "/Users/<USERNAME>/.local/share/uv/tools/mcp/bin/mcp",
      "args": ["run", "/full/path/to/betterdeal/src/betterdeal/server.py"]
    }
  }
}
```

**Important**: Replace `/full/path/to/` with the actual absolute path to your `betterdeal` directory.

Restart Claude Desktop after saving the configuration.

### 2. Use the MCP server with Claude

Once configured, Claude Desktop will have access to these tools:

* **`get_property_data`**: Get detailed property data for a specific property ID
* **`get_property_valuation`**: Get property value estimates
* **`get_rent_estimate`**: Get rent estimates for a property
* **`get_market_statistics`**: Get market statistics for a ZIP code area
* **`get_property_listings`**: Get active property listings in a ZIP code area

**Example queries to try with Claude:**
- "Get market statistics for ZIP code 90210"
- "Show property listings in ZIP code 10001"
- "What are the market trends in ZIP code 02101?"

## Development and testing

Install development dependencies and run the test suite with:

```bash
uv sync --all-extras
pytest -v tests
```

### Running the server locally

To start the server manually (useful when developing or testing), run:

```bash
betterdeal
```

Alternatively, you can run it directly with:

```bash
uv run python src/betterdeal/server.py
```

### Installing MCP CLI globally

If you want to use `mcp run` commands, install the MCP CLI globally:

```bash
uv tool install "mcp[cli]"
```

Then you can run:

```bash
mcp run src/betterdeal/server.py
```

## Property Investment Analyzer Web App

### Quick Start

Run the web application:

```bash
# Option 1: Using the run script
python run_analyzer.py

# Option 2: Using uvicorn directly
uvicorn src.betterdeal.web_app:app --reload --host 0.0.0.0 --port 8000

# Option 3: Using the installed command
betterdeal-analyzer
```

Then open your browser to **http://localhost:8000**

### How to Use

1. **Paste a Property URL**: Enter a Zillow or Realtor.com property listing URL
2. **Select Investment Strategy**: Choose from:
   - **Rental**: Buy and hold for rental income
   - **Flip**: Buy, renovate, and sell quickly
   - **BRRRR**: Buy, Rehab, Rent, Refinance, Repeat
   - **House Hack**: Live in one unit, rent others
   - **Long-term Appreciation**: Focus on property appreciation
3. **Configure Loan Details**: 
   - Select loan type (Conventional, FHA, VA, USDA)
   - Set interest rate, loan term, down payment
   - Adjust optional parameters (HOA, maintenance, vacancy rate, etc.)
4. **Analyze**: Click "Analyze Property" to get comprehensive investment analysis

### What You'll Get

The analysis includes:
- **Property Information**: Address and source
- **Loan Details**: Down payment, monthly payment (PITI), loan terms
- **Investment Metrics**: 
  - Monthly and annual cash flow
  - Cash-on-cash return
  - Cap rate
  - Rental yield
  - Debt service coverage ratio
- **Investment Scores**: Overall score based on your strategy
- **Recommendations**: Actionable insights and warnings

### Example URLs

- Zillow: `https://www.zillow.com/homedetails/123-Main-St-City-ST-12345/12345678_zpid/`
- Realtor.com: `https://www.realtor.com/realestateandhomes-detail/123-Main-St_City_ST_12345_M12345_12345`

### API Endpoint

You can also use the API directly:

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "property_url": "https://www.zillow.com/homedetails/...",
    "strategy": "rental",
    "loan_type": "conventional",
    "interest_rate": 0.065,
    "loan_term_years": 30
  }'
```

## License

MIT
