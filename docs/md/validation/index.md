# Validation

flarchitect ships with a suite of field validators that hook directly into
Marshmallow.  Validators can be attached to a model column via the SQLAlchemy
`info` mapping or inferred automatically from column names and formats.
For a runnable example demonstrating email and URL validation see the validators demo <[https://github.com/lewis-morris/flarchitect/tree/master/demo/validators](https://github.com/lewis-morris/flarchitect/tree/master/demo/validators)>.

## Sections

- [Basic usage](basic-usage.md)
- [Field validation](field-validation.md)
- [Available validators](available-validators.md)
