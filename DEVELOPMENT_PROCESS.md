# Development Process - News Analysis Pipeline

## Problem Statement
Build a dual-LLM validation pipeline that fetches recent news about Indian politics, analyzes each article for gist/sentiment/tone using one LLM, then validates the analysis with a second LLM.

## Breaking Down the Problem (20 minutes)

### Initial Analysis
I identified the core workflow:
1. **Fetch** news articles from NewsAPI
2. **Analyze** each article with LLM#1 (Groq GPT OSS 120B)
3. **Validate** analysis with LLM#2 (Groq GPT OSS 20B)
4. **Report** results in JSON and Markdown formats

### Task Dependencies
```
Fetch News → Analyze (LLM#1) → Validate (LLM#2) → Generate Report
     ↓              ↓                ↓                  ↓
Raw Articles → Analysis Results → Validated Results → Final Report
```

### Detailed Task Breakdown
1. **News Fetching** (Input: API key, query params → Output: JSON list of articles)
   - Handle API rate limits
   - Normalize/clean article data
   - Error handling for timeouts
   
2. **LLM Analysis** (Input: Article text → Output: Gist, sentiment, tone)
   - Structure prompt for consistent JSON output
   - Parse LLM response
   - Handle malformed responses
   
3. **LLM Validation** (Input: Article + Analysis → Output: Validation result)
   - Cross-check analysis against original text
   - Identify discrepancies
   - Provide justification
   
4. **Report Generation** (Input: All results → Output: MD + JSON)
   - Aggregate sentiment statistics
   - Format human-readable output
   - Save structured data

## AI Prompt Planning (15 minutes)

### Prompts That Worked Well

**For news_fetcher.py:**
```
"Write a Python class called NewsFetcher that:
- Fetches news from NewsAPI using the 'everything' endpoint
- Handles rate limiting (429 errors) by waiting 60 seconds
- Has timeout handling (10 seconds)
- Takes API key from environment variable
- Returns cleaned, normalized articles as dictionaries
- Include comprehensive error handling"
```

**For llm_analyzer.py:**
```
"Create a class LLMAnalyzer using Groq that:
- Takes an article dictionary with title, description, content
- Sends a structured prompt asking for JSON output with gist, sentiment, tone
- Handles JSON parsing errors with retry logic (3 attempts)
- Cleans markdown code blocks from response
- Returns default values on failure
- Uses openai/gpt-oss-120b model"
```

**For llm_validator.py:**
```
"Build a LLMValidator class using Groq's GPT OSS model that:
- Compares the original article with LLM#1's analysis
- Validates if gist is accurate, sentiment justified, tone correct
- Returns JSON with is_valid (boolean) and notes (explanation)
- Handles API errors and rate limits
- Uses retry logic similar to analyzer"
```

### Prompts That Needed Refinement

**Initial prompt for main.py:**
❌ "Build the main pipeline that connects everything"
- Too vague, didn't specify error handling flow

**Refined prompt:**
✅ "Create main.py that orchestrates the pipeline with:
- Step-by-step execution with progress indicators
- Save intermediate results after each step
- Generate final markdown report with statistics
- Handle errors gracefully at each step
- Print clear status messages"

## Development Execution (3 hours)

### Step 1: Environment Setup (15 min)
- Created project structure
- Set up .gitignore for API keys
- Created .env.template as reference
- Installed required packages

### Step 2: News Fetcher (30 min)
**AI Generated:** Basic NewsAPI wrapper
**My Review:**
- ✅ Good: Clean API call structure
- ❌ Issue: No rate limit handling
- ❌ Issue: Didn't filter articles without content

**Refinement:**
- Added rate limit detection (429 status)
- Added article cleaning (skip if no title/description)
- Improved error messages

### Step 3: LLM Analyzer (45 min)
**AI Generated:** Groq integration with JSON parsing
**My Review:**
- ✅ Good: Structured prompt for JSON output
- ❌ Issue: Didn't handle markdown code blocks in response
- ❌ Issue: No retry logic for transient failures

**Refinement:**
- Added code block cleaning (```json removal)
- Implemented 3-attempt retry with exponential backoff
- Added field validation before returning

### Step 4: LLM Validator (45 min)
**AI Generated:** Groq Llama API integration
**My Review:**
- ✅ Good: Clear validation criteria
- ❌ Issue: Didn't specify temperature parameter
- ❌ Issue: Error handling too generic

**Refinement:**
- Set temperature=0.3 for consistency
- Added specific error types (timeout, rate limit, JSON parse)
- Improved validation prompt clarity

### Step 5: Main Orchestration (30 min)
**AI Generated:** Pipeline connector
**My Review:**
- ✅ Good: Step-by-step execution
- ❌ Issue: No progress indicators
- ❌ Issue: Didn't save intermediate results

**Refinement:**
- Added progress messages (✓ symbols)
- Save JSON after each major step
- Added summary statistics to report

### Step 6: Testing (45 min)
**AI Generated:** Basic pytest structure
**My Review:**
- ✅ Good: Mocked external APIs
- ❌ Issue: Only happy path tests

**Refinement:**
- Added error case tests (timeout, invalid JSON, missing API keys)
- Added data structure validation tests
- Ensured 100% mock coverage (no real API calls in tests)

## Key Decisions & Trade-offs

### 1. **Groq for Both LLMs**
- **Decision:** Used Groq for both analyzer and validator
- **Reason:** Free tier with 14,400 requests/day, fast inference, multiple model choices
- **Trade-off:** Using different models (Qwen vs Llama) for diversity in validation

### 2. **Model Selection**
- **Decision:** GPT OSS 120B for analysis, GPT OSS 20B for validation
- **Reason:** Flagship open-weight model for main analysis, smaller efficient model for validation
- **Trade-off:** Both on same provider (Groq)

### 3. **Sequential vs Parallel Processing**
- **Decision:** Sequential (one article at a time)
- **Reason:** Easier error tracking, respects rate limits
- **Trade-off:** Slower for large batches (could parallelize in future)

### 4. **Retry Strategy**
- **Decision:** 3 attempts with 2-second delays
- **Reason:** Balance between reliability and speed
- **Trade-off:** Could timeout on persistent failures (acceptable for this use case)

## What I Learned

### About AI-Assisted Development
1. **Specificity Matters:** Vague prompts like "build a scraper" produce generic code. Specific prompts with edge cases, error handling, and return types yield production-ready code.

2. **Iterative Refinement:** AI generated ~70% correct code on first attempt. The remaining 30% (error handling, edge cases, cleanup logic) required manual refinement.

3. **Trust but Verify:** AI suggested `response.raise_for_status()` but didn't handle specific HTTP codes. I added explicit 429 handling.

### About the Problem Domain
1. **LLM Response Variability:** Even with structured prompts, LLMs occasionally return markdown-wrapped JSON. Cleanup logic is essential.

2. **API Rate Limits:** NewsAPI has strict limits. Caching and retry logic are critical for production use.

3. **Validation is Hard:** LLM#2 sometimes agrees with incorrect analysis if the error is subtle. Human review still needed for critical applications.

## How I'd Do It Differently Next Time

### Improvements
1. **Add Caching:** Cache article fetches to avoid re-hitting NewsAPI during development
2. **Parallel Processing:** Use `asyncio` to analyze multiple articles simultaneously
3. **Better Validation:** Give LLM#2 access to fact-checking tools or knowledge base
4. **Metrics:** Track API latency, token usage, validation accuracy
5. **Config File:** Move settings (model names, retry counts) to `config.yaml`

### Architecture Changes
1. **Database:** Store results in SQLite instead of JSON files for better querying
2. **Streaming:** Process articles as they arrive rather than batch processing
3. **Monitoring:** Add logging framework (e.g., `loguru`) for production debugging

## Testing the Pipeline

### Running Tests
```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/test_analyzer.py -v

# Expected: 10 tests passed
```

### Running the Full Pipeline
```bash
# Set up environment
cp .env.template .env
# Edit .env with your API keys

# Run pipeline
python main.py

# Check outputs
ls output/
# Should see: raw_articles.json, analysis_results.json, 
#             validated_results.json, final_report.md
```

## Final Thoughts

This project reinforced the **"You Break Down; AI Executes"** philosophy:
- I controlled the architecture (fetcher → analyzer → validator → reporter)
- AI accelerated implementation (API wrappers, error handling boilerplate)
- I ensured quality (added edge cases, improved prompts, wrote tests)

The dual-LLM approach works surprisingly well for catching obvious errors (wrong sentiment, off-topic gist), but subtle biases still slip through. For production fact-checking, I'd add a third layer: human review of flagged discrepancies.

**Time Breakdown:**
- Planning: 35 min
- AI-generated code: 1.5 hours
- Refinement & debugging: 1 hour  
- Testing: 45 min
- Documentation: 30 min
**Total: ~4 hours**
