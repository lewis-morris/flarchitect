[← Back to WebSockets index](index.md)

# Subscription Model
Subscribe to a topic by connecting to the endpoint with an optional `topic`
query parameter. Without a topic, the server subscribes you to `all`.
Examples:
- All models: `ws://localhost:5000/ws`
- Specific model: `ws://localhost:5000/ws?topic=author`

