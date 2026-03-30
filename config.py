"""
config.py — Central configuration and resume placeholder.
Replace RESUME with your actual resume text before running.
"""

# ─────────────────────────────────────────────────────────
# RESUME PLACEHOLDER — paste your resume as plain text here
# ─────────────────────────────────────────────────────────
RESUME = """
Name: Suraj Pabba

Summary:
12+ year technical product and operations leader who thrives at the
intersection of enterprise sales engineering, AI/LLM product development,
and customer success. Proven record of landing Fortune 500 accounts,
building and shipping production AI applications, and scaling revenue from
zero to $1M/month. Equally comfortable in a startup board room, on a
customer onboarding call, or writing Python integrations late at night.

Experience:

- CNA Insurance | Data Consulting Leader | 2023–Present
  Architect AI agents and end-to-end data strategy on GCP/Snowflake/AWS.
  Built predictive pricing models and automated pipelines that cut analyst
  toil by 40%. Stakeholder-facing role bridging data engineering and
  business strategy for a $12B insurance carrier.

- InField AI (Antler NYC EIR) | Co-founder & CEO | 2022–2023
  Built an AI-powered field-operations platform; engaged 20+ Fortune 500
  clients across manufacturing, utilities, and logistics. Raised pre-seed
  via Antler's NYC cohort. Sole technical founder — designed architecture,
  ran pilots, and closed enterprise contracts.

- Treehouse | Head of Product & Engineering | 2020–2022
  Led LLM/AI field-service application from $300K to $1M/month MRR.
  Owned full product lifecycle: roadmap, API integrations (HubSpot,
  Zapier, Salesforce), mobile app, and customer onboarding for 150+
  field-service companies. Built FSM automation that replaced manual
  dispatch workflows.

- iManage | Solutions Engineer | 2018–2020
  Won SE of the Year. Delivered enterprise demos, POCs, and technical
  integrations for Am Law 100 firms, investment banks, and global
  accounting firms. Specialised in document-intelligence and knowledge-
  management platforms.

- Salesforce / MuleSoft | Solutions Engineer | 2015–2018
  Pre-sales SE for MuleSoft integration platform targeting Fortune 500.
  Led technical discovery, sandbox POCs, and RFP responses. Closed deals
  across financial services, healthcare, and retail verticals.

Skills:
Python, PyTorch, LLMs (OpenAI, Anthropic, Mistral), RAG pipelines,
REST API design and integration, SQL, Tableau, GCP, AWS, Azure,
Snowflake, dbt, Spark, CRM automation (HubSpot, Salesforce, Zapier),
technical pre-sales, enterprise customer onboarding, stakeholder
management, product roadmapping.

Education:
B.S. Computer Science — University of Texas at Austin
"""

# ─────────────────────────────────────────────────────────
# Search configuration
# ─────────────────────────────────────────────────────────
SEARCH_QUERY = "Forward Deployed Engineer"
SEARCH_QUERY_VARIANTS = [
    "Forward Deployed Engineer",
    "Forward Deployed Software Engineer",
    "Solutions Engineer",
    "Field Engineer",
    "Implementation Engineer",
]

# Job posted within this many days (used where supported)
MAX_AGE_DAYS = 1

# Recipient email
TO_EMAIL = "suraj.pabba89@gmail.com"
EMAIL_SUBJECT = "🚀 Daily Forward Deployed Engineer Job Digest"

# ─────────────────────────────────────────────────────────
# Company lists per ATS — add/remove slugs as needed
# These are public job-board API endpoints (no auth required)
# ─────────────────────────────────────────────────────────

# Greenhouse: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
GREENHOUSE_COMPANIES = [
    "palantir", "scale", "hex", "retool", "notion", "rippling",
    "stripe", "databricks", "snowflake", "dbtlabs", "sigmacomputing",
    "getmontecarlo", "fivetran", "airbyte", "census", "amplitude",
    "mixpanel", "braze", "klaviyo", "twilio", "segment", "airtable",
    "coda", "figma", "miro", "loom", "asana", "linear", "gitlab",
    "hashicorp", "datadog", "newrelic", "elastic", "splunk",
    "pagerduty", "launchdarkly", "statsig", "optimizely",
    "collibra", "atlan", "hightouch", "rudderstack", "starburst",
    "imply", "startree", "tecton", "featureform", "continual",
    "arize", "whylabs", "fiddler", "arthur", "weights-biases",
    "comet", "neptune", "clearml", "verta", "bentoml",
    "gretel", "trifacta", "alation", "datacoral", "secoda",
    "select-star", "castor", "metaphor", "stemma",
    "anduril", "primer", "c3-ai", "palantir",
    "samsara", "verkada", "vanta", "drata",
    "ironclad", "contractbook", "docusign", "pendo",
    "gainsight", "churnzero", "catalyst", "totango",
    "vitally", "planhat", "clientsuccess",
]

# Lever: https://api.lever.co/v0/postings/{slug}
LEVER_COMPANIES = [
    "palantir", "anduril", "scale-ai", "openai", "anthropic",
    "cohere", "mistral", "together-ai", "replicate", "modal",
    "fly-io", "render", "railway", "supabase", "planetscale",
    "neon", "turso", "xata", "convex", "ditto",
    "grafana-labs", "influxdata", "timescale", "questdb",
    "clickhouse", "duckdb", "motherduck", "tinybird",
    "rockset", "imply", "druid", "pinecone", "weaviate",
    "chroma", "qdrant", "milvus", "zilliz",
    "langchain", "llamaindex", "haystack", "deepset",
    "vapi", "bland", "retell",
    "glean", "guru", "tettra", "confluence",
    "shortcut", "height", "plane", "basecamp",
    "vercel", "netlify", "cloudflare",
    "snyk", "lacework", "orca", "wiz",
    "cribl", "mezmo", "coralogix", "honeycomb",
    "incident-io", "rootly", "firehydrant", "blameless",
    "getcortexapp", "port", "backstage",
]

# Ashby: https://api.ashbyhq.com/posting-api/job-board/{slug}
ASHBY_COMPANIES = [
    "anthropic", "openai", "cohere", "mistral",
    "langchain", "llamaindex", "fixie", "dust",
    "hex", "mode", "sigma", "preset", "lightdash",
    "evidence", "rill", "cube", "malloy",
    "dbt-labs", "datacoves", "dbt-core",
    "prefect", "dagster", "mage-ai", "orchest",
    "astronomer", "datafold", "recce", "piperider",
    "elementary-data", "re-data", "dbt-osmosis",
    "turntable", "y42", "etlbox",
    "stytch", "ory", "hanko", "workos", "clerk",
    "temporal", "inngest", "trigger",
    "baseten", "banana", "cerebrium", "lepton",
    "fireworks", "groq", "sambanova", "cerebras",
    "scale-ai", "labelbox", "v7labs", "encord",
    "snorkel", "aquarium", "cleanlab",
]
