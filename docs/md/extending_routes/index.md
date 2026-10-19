# Extend the generated API

Keep the generated routes and change only the behaviour your application needs.
Use a hook for a small adjustment, an action for a business operation, an override
for a replacement implementation, or a managed route for an unrelated endpoint.
Existing `Meta` configuration, callbacks, plugins and `schema_constructor`
remain supported.

## Sections

- [Register before initialisation](register-before-initialisation.md)
- [Choose the smallest extension](choose-the-smallest-extension.md)
- [Hooks: keep the generated implementation](hooks-keep-the-generated-implementation.md)
- [Actions: add business logic](actions-add-business-logic.md)
- [Overrides: replace one operation](overrides-replace-one-operation.md)
- [Transaction ownership](transaction-ownership.md)
- [One context everywhere](one-context-everywhere.md)
- [Managed routes: one decorator](managed-routes-one-decorator.md)
- [Runnable example](runnable-example.md)
