[← Back to API Documentation index](index.md)

# Customising the document
A number of configuration keys let you tailor the output:
- API_DOCUMENTATION_HEADERS <configuration.html#DOCUMENTATION_HEADERS> – HTML string inserted into the `<head>` of
    the docs page. Use for meta tags or custom scripts.
- API_TITLE <configuration.html#TITLE> – plain text displayed as the documentation title.
- API_VERSION <configuration.html#VERSION> – semantic version string such as `"1.0.0"`.
- API_DESCRIPTION <configuration.html#DESCRIPTION> – free text or a filepath to a README-style file rendered
    into the `info` section.
- API_LOGO_URL <configuration.html#LOGO_URL> – URL or static path to an image used as the logo.
- API_LOGO_BACKGROUND <configuration.html#LOGO_BACKGROUND> – CSS colour value behind the logo (e.g.
    `"#fff"` or `"transparent"`).
- API_CONTACT_NAME <configuration.html#CONTACT_NAME>, API_CONTACT_EMAIL <configuration.html#CONTACT_EMAIL>,
    API_CONTACT_URL <configuration.html#CONTACT_URL> – contact information shown in the spec.
- API_LICENCE_NAME <configuration.html#LICENCE_NAME>, API_LICENCE_URL <configuration.html#LICENCE_URL> – licence metadata.
- API_SERVER_URLS <configuration.html#SERVER_URLS> – list of server entries (`url` + `description`) for environments.
For example, to load a Markdown file into the specification's info section:
```
app.config["API_DESCRIPTION"] = "docs/README.md"
```
The contents of `docs/README.md` are rendered in the spec's `info` section.
See configuration for the full list of options.

