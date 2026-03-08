# recon-config.json Schema & Examples

## Schema

```json
{
  "domain": "string — short domain label (e.g., 'tolkien-lore', 'ai-tools')",
  "description": "string — what this project is about, provides context for all searches",

  "sources": {
    "x": {
      "enabled": true,
      "queries": ["string — search queries for X/Twitter"],
      "handles": ["string — X handles to monitor (optional, max 10)"],
      "days": 7
    },
    "reddit": {
      "enabled": true,
      "subreddits": ["string — subreddit names without r/"],
      "sort": ["hot", "rising", "top"],
      "limit": 20,
      "deep_dive": 5
    },
    "web": {
      "enabled": true,
      "search_categories": {
        "category_name": {
          "queries": ["string — web search queries"],
          "focus": "string — what to look for in results"
        }
      }
    }
  },

  "synthesis": {
    "focus": "string — what to prioritize in synthesis (content_strategy, competitive_intelligence, community_engagement, trend_monitoring)"
  }
}
```

## Field Details

### Top Level

| Field | Required | Description |
|-------|----------|-------------|
| `domain` | Yes | Short label for the domain. Used in report headers and to contextualize searches. |
| `description` | Yes | 1-2 sentences describing what this project is about. Agents use this to make search queries domain-relevant. |

### sources.x

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Set `false` to skip X source |
| `queries` | — | List of search queries. Each becomes a separate Grok x_search call. |
| `handles` | `[]` | X accounts to filter results to (max 10) |
| `days` | `7` | How far back to search |

### sources.reddit

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Set `false` to skip Reddit source |
| `subreddits` | — | List of subreddit names (no r/ prefix) |
| `sort` | `["hot","rising","top"]` | Which sort methods to fetch |
| `limit` | `20` | Posts per subreddit per sort method |
| `deep_dive` | `5` | Fetch comments for top N posts by engagement |

### sources.web

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Set `false` to skip web source |
| `search_categories` | — | Named categories with queries and focus areas |

### synthesis

| Field | Default | Description |
|-------|---------|-------------|
| `focus` | `"content_strategy"` | Guides what the synthesis agent emphasizes |

---

## Examples

### Tolkien YouTube Channel

```json
{
  "domain": "tolkien-lore",
  "description": "YouTube channel creating deep-dive episodes about Tolkien's legendarium — Silmarillion, Lord of the Rings, and lesser-known lore.",

  "sources": {
    "x": {
      "enabled": true,
      "queries": [
        "What are the most discussed Tolkien and Middle-earth topics? What lore questions are fans debating?",
        "Rings of Power discussion and canonical accuracy debates"
      ],
      "handles": ["tolkiensociety", "praboringring", "TolkienBrasil"],
      "days": 7
    },
    "reddit": {
      "enabled": true,
      "subreddits": ["tolkienfans", "lotr", "TheSilmarillion", "RingsofPower"],
      "sort": ["hot", "rising", "top"],
      "limit": 20,
      "deep_dive": 5
    },
    "web": {
      "enabled": true,
      "search_categories": {
        "community_trends": {
          "queries": [
            "Tolkien trending topics 2026",
            "Lord of the Rings analysis latest",
            "Middle-earth lore questions fans ask"
          ],
          "focus": "Hot topics, renewed interest, fan questions"
        },
        "competitive_landscape": {
          "queries": [
            "best Tolkien lore YouTube channels",
            "popular Tolkien videos latest"
          ],
          "focus": "What other creators cover, content gaps"
        },
        "calendar": {
          "queries": [
            "Tolkien anniversaries upcoming",
            "Lord of the Rings events releases"
          ],
          "focus": "Time-sensitive content opportunities"
        }
      }
    }
  },

  "synthesis": {
    "focus": "content_strategy"
  }
}
```

### AI/Tech Industry Monitoring

```json
{
  "domain": "ai-tools",
  "description": "Tracking AI coding assistant landscape — new tools, developer sentiment, market shifts, and emerging capabilities.",

  "sources": {
    "x": {
      "enabled": true,
      "queries": [
        "AI coding assistant tools trends and developer reactions",
        "Claude vs GPT vs Gemini developer experience latest"
      ],
      "handles": ["AnthropicAI", "OpenAI", "GoogleDeepMind"],
      "days": 7
    },
    "reddit": {
      "enabled": true,
      "subreddits": ["LocalLLaMA", "ChatGPT", "ClaudeAI", "programming"],
      "sort": ["hot", "top"],
      "limit": 15,
      "deep_dive": 3
    },
    "web": {
      "enabled": true,
      "search_categories": {
        "product_launches": {
          "queries": [
            "AI coding tools new releases this week",
            "developer AI assistant announcements"
          ],
          "focus": "New products, features, pricing changes"
        },
        "developer_sentiment": {
          "queries": [
            "AI coding assistant developer reviews latest",
            "AI pair programming real world experience"
          ],
          "focus": "What developers actually think, pain points"
        }
      }
    }
  },

  "synthesis": {
    "focus": "competitive_intelligence"
  }
}
```

### SaaS Competitive Intelligence

```json
{
  "domain": "project-management-saas",
  "description": "Competitive intelligence for a project management SaaS product. Track competitor moves, user complaints, market gaps.",

  "sources": {
    "x": {
      "enabled": true,
      "queries": [
        "project management software complaints switching from",
        "best project management tool for teams latest"
      ],
      "handles": [],
      "days": 14
    },
    "reddit": {
      "enabled": true,
      "subreddits": ["projectmanagement", "SaaS", "startups", "Entrepreneur"],
      "sort": ["hot", "top"],
      "limit": 15,
      "deep_dive": 3
    },
    "web": {
      "enabled": true,
      "search_categories": {
        "competitor_moves": {
          "queries": [
            "Asana Monday Linear new features",
            "project management SaaS funding acquisitions"
          ],
          "focus": "Pricing changes, new features, strategic shifts"
        },
        "user_pain_points": {
          "queries": [
            "project management tool frustrations",
            "switching project management software why"
          ],
          "focus": "Complaints, unmet needs, switching triggers"
        }
      }
    }
  },

  "synthesis": {
    "focus": "competitive_intelligence"
  }
}
```

### Hobbyist Community Tracking

```json
{
  "domain": "mechanical-keyboards",
  "description": "Tracking mechanical keyboard community trends, group buys, popular switches, and emerging designs.",

  "sources": {
    "x": {
      "enabled": false
    },
    "reddit": {
      "enabled": true,
      "subreddits": ["MechanicalKeyboards", "CustomKeyboards", "keycaps"],
      "sort": ["hot", "rising", "top"],
      "limit": 25,
      "deep_dive": 5
    },
    "web": {
      "enabled": true,
      "search_categories": {
        "group_buys": {
          "queries": [
            "mechanical keyboard group buy live",
            "keycap group buy upcoming"
          ],
          "focus": "Active and upcoming group buys, IC interest checks"
        },
        "trends": {
          "queries": [
            "mechanical keyboard trends popular switches",
            "custom keyboard build trends"
          ],
          "focus": "What's popular, emerging preferences"
        }
      }
    }
  },

  "synthesis": {
    "focus": "community_engagement"
  }
}
```

---

## Tips

- **Start minimal**: You don't need every field. `domain`, `description`, and one source is enough to start.
- **Iterate**: Run `/recon`, see what's useful, refine queries based on results.
- **Disable sources**: Set `"enabled": false` to skip sources you don't need or can't use (e.g., no XAI_API_KEY → disable X).
- **Query quality matters**: Good search queries produce better results than more queries. Be specific.
- **Deep dive selectively**: `deep_dive` fetches full comment threads — useful but slow. Start with 3-5.
