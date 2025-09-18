[← Back to API Documentation index](index.md)

# Exporting to a file
To generate a static JSON document for deployment or tooling:
```
import json

with open("openapi.json", "w") as fh:
    json.dump(architect.api_spec.to_dict(), fh, indent=2)
```

