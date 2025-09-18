[← Back to GraphQL index](index.md)

# Tips and trade-offs
GraphQL offers flexible queries and reduces the number of HTTP round-trips, but
it also introduces additional complexity. Responses are not cacheable by
standard HTTP mechanisms, and naïve schemas can allow very expensive queries.
Ensure resolvers validate user input and consider depth limiting or query cost
analysis for production deployments.
Further examples are available in demo.graphql.

