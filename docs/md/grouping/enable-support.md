[← Back to Grouping & Aggregation index](index.md)

# Enable support
Two configuration values control the feature set:
```
class Config:
    API_ALLOW_GROUPBY = True
    API_ALLOW_AGGREGATION = True
```
Both flags can be applied globally on the Flask config (`API_` prefix) or
per model via the `Meta` class (lowercase without the prefix). Aggregation
builds on grouping, so enable both together when you expect to run
summaries from the same endpoint. See configuration for the
configuration hierarchy.

