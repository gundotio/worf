# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.2.1](https://github.com/gundotio/worf/compare/v0.2.0...v0.2.1) (2021-04-29)

- Makes Serializers model-agnostic
- Adds LegacySerializer for backwards compatibility 
- Adds official support for python 3.7

## [0.2.0](https://github.com/gundotio/worf/compare/v0.1.6...v0.2.0) (2021-04-26)

- Removes implicit `GET` method from all APIViews
- Adds optional `serializer` to each API, which will supercede the
`api_method` 

### [0.1.6](https://github.com/gundotio/worf/compare/v0.1.5...v0.1.6) (2021-04-20)

- Adds PublicEndpoint permission, for use in silencing warnings

### [0.1.5](https://github.com/gundotio/worf/compare/v0.1.4...v0.1.5) (2021-04-08)

- Fix pagination related 500 errors on bad requests
- Adds Django 3.2 to test suite

### [0.1.4](https://github.com/gundotio/worf/compare/v0.1.3...v0.1.4) (2021-04-01)

- Improves setup for pypi
- Improves tetst coverage
- Adds get_instance_or_http404 to replace djago's get_object_or_404, 
to return javascript error instead of 404 page

### [0.1.3](https://github.com/gundotio/worf/compare/v0.1.2...v0.1.3) (2021-03-30)

- Adds docker container, scripts to rule them all, binstubs, gitignore
- Setups github actions and runs matrixed supported python + django versions
- Fixes test for validate_bundle

### [0.1.2](https://github.com/gundotio/worf/compare/v0.1.1...v0.1.2) (2021-03-30)

- Adds documentation in README
- Setups pytest
- Fixes validation error
- Adds custom field validation
- Adds overrides to bundle factory

### 0.1.1 (2021-02-01)

Initial Release
