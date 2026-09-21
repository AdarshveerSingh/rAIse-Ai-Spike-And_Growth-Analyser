# rAIse — AI Growth & Spike Analyser

> **Understand what caused growth. Discover what could happen next.**

rAIse is an AI-powered growth analysis platform designed to investigate the growth patterns of creators, companies, products, and other entities.

The project currently uses **YouTube growth analysis as its MVP**, where users can provide a YouTube channel and receive an analysis of its historical growth, identify significant spikes, investigate what may have caused those spikes, and generate research-backed insights.

The long-term goal is to turn rAIse into a broader **growth intelligence platform** capable of analysing the growth of companies, products, creators, and financial assets.

---

## What Does rAIse Do?

rAIse takes an entity and attempts to answer questions such as:

- When did its growth accelerate?
- What happened around major growth spikes?
- Which events, releases, or pieces of content may have contributed?
- What patterns can be identified from its history?
- What can be learned from those periods of growth?
- How could those insights be used to understand future growth opportunities?

For the current MVP, the entity is a **YouTube channel**.

The system analyses the channel's historical videos and metrics, identifies unusual growth events, and provides additional research around those events.

---

## YouTube Analysis — MVP

The current implementation focuses on **YouTube channels as a proof of concept**.

Given a YouTube channel, rAIse can:

1. Retrieve channel information using the YouTube Data API.
2. Retrieve historical videos and their metrics.
3. Analyse views and engagement over time.
4. Establish a baseline for normal channel performance.
5. Detect significant deviations from that baseline.
6. Identify potential **growth spikes**.
7. Compare videos before and after major events.
8. Display important growth events on a timeline.
9. Allow users to inspect individual videos.
10. Perform additional AI-powered research around selected growth events.
11. Generate explanations and hypotheses for why a spike may have occurred.

The goal is not simply to identify that a channel grew.

The goal is to investigate **why the growth happened**.

### Example

A channel may normally receive around 10,000 views per video, but one video receives 300,000 views.

rAIse can identify this as an unusual event and investigate factors surrounding it, such as:

- The video's topic
- Title and content
- Timing
- Previous channel performance
- Related events
- Changes in content strategy
- External developments
- Patterns in subsequent videos

The resulting analysis distinguishes between observed data and hypotheses where appropriate.

---

## Why YouTube?

YouTube provides a useful environment for developing and testing the underlying growth-analysis system because it contains:

- Historical data
- Time-series performance
- Individual content events
- Public engagement metrics
- Clearly identifiable growth spikes
- Large differences between normal and exceptional performance

This makes YouTube a practical **MVP environment** for validating the core idea behind rAIse.

However, YouTube is only the beginning.

---

# Future Scope

The long-term vision for rAIse is to move beyond creator analytics and become a general-purpose **growth intelligence platform**.

## 1. Product Growth Tracking

rAIse could analyse the growth of individual products.

For example:

- New product launches
- App downloads
- User growth
- Search interest
- Reviews
- Social media activity
- Product updates
- Pricing changes

The system could identify periods of unusually rapid adoption and investigate what happened around them.

### Example

A product suddenly experiences a large increase in users.

rAIse could investigate:

```text
Product Growth
      ↓
Growth Spike
      ↓
What changed?
      ↓
Launch / Update / Marketing / Trend / External Event
      ↓
Potential Growth Drivers

2. Company Growth Analysis
The same approach could be applied to companies.
Potential data points could include:
- Revenue
- User growth
- Funding
- Product launches
- Hiring
- Market expansion
- Marketing campaigns
- Partnerships
- Public announcements
- Social presence
- Search trends
rAIse could build a timeline of major company events and compare them with periods of accelerated growth.
3. Stock & Market Analysis
A future version could also analyse publicly traded companies and their stocks.
Potential capabilities include:
- Historical price movements
- Trading volume
- Earnings announcements
- Product launches
- Company announcements
- Acquisitions
- Partnerships
- Market events
- News events
The system could identify unusual price movements and investigate the events surrounding them.
For example:
Stock Movement
      ↓
Unusual Price Spike
      ↓
Identify Time Window
      ↓
Search Relevant Events
      ↓
Company News
Earnings
Product Launch
Market Event
      ↓
Generate Analysis
This would extend the project's core concept from "What caused this YouTube spike?" to:
"What happened around this growth event, and what evidence connects the two?"

4. Cross-Platform Analysis
Another major area of future development is combining multiple sources.
For example:
YouTube
   +
Reddit
   +
Google Trends
   +
News
   +
Social Media
   +
Company Data
   ↓
Unified Growth Timeline
This could allow rAIse to investigate whether an observed growth event was isolated to one platform or part of a larger trend.
5. Automated Growth Case Studies
rAIse could eventually generate complete case studies automatically.
For example:
How did Company X grow from 10,000 users to 1 million users?

The system could reconstruct the company's timeline and identify:
- Important milestones
- Major product changes
- Marketing campaigns
- External events
- Growth periods
- Changes in strategy
- Possible growth drivers
The result would be a structured growth story rather than just a collection of statistics.
Architecture
The current project is split into a frontend and backend.
                    ┌─────────────────────┐
                    │      User           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Next.js Frontend  │
                    │                     │
                    │  rAIse Dashboard    │
                    └──────────┬──────────┘
                               │
                         REST API
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │                     │
                    │ Analysis Pipeline   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        YouTube API       AI Research      Data Analysis
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Growth Analysis   │
                    │                     │
                    │  Spikes / Events    │
                    │  Patterns / Trends  │
                    └─────────────────────┘
Tech Stack
Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
The frontend provides the interactive analysis dashboard, including:
- Channel overview
- Growth timeline
- Growth events
- Video analysis
- Interactive charts
- AI research results
Backend
- Python
- FastAPI
- YouTube Data API
- Requests
- Data analysis and custom growth-detection logic
The backend handles:
- YouTube data retrieval
- Data processing
- Growth analysis
- Spike detection
- Research requests
- API responses
AI
AI is used to assist with the research and interpretation of identified growth events.
Rather than relying entirely on the model to discover numerical anomalies, the system first performs structured analysis on the available data and then uses AI where contextual research and interpretation are useful.
Core Concept
The core idea behind rAIse is:
Detect the event first. Investigate the cause second.

Instead of asking an AI model to blindly analyse a large amount of data, rAIse attempts to narrow the problem down into meaningful events.
Raw Data
   ↓
Historical Analysis
   ↓
Baseline
   ↓
Anomaly / Spike Detection
   ↓
Growth Event
   ↓
Contextual Research
   ↓
AI Analysis
   ↓
Growth Insights
This approach can eventually be generalized to many different types of growth data.
Project Status
Current Status: MVP
The YouTube Growth & Spike Analyzer is the current MVP of rAIse.
The MVP demonstrates the core concept:
Can we identify unusual growth and investigate what happened around it?

Future versions are intended to expand the same methodology to:
- YouTube creators
- Products
- Companies
- Startups
- Apps
- Stocks
- Markets
- Other measurable growth signals
Future Vision
The long-term vision is for rAIse to become an AI-powered growth intelligence system.
Instead of only answering:
"What happened?"

rAIse aims to eventually answer:
"What changed, what happened around it, what evidence supports the possible causes, and what can we learn from the growth pattern?"

This could make rAIse useful for:
- Creators
- Founders
- Product teams
- Marketers
- Researchers
- Investors
- Businesses
