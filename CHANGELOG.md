# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [0.5.0](https://github.com/gundotio/worf/compare/v0.4.9...v0.5.0) (2021-11-19)

- Serializer field validation for POST requests
- Method specific serialization

### [0.4.9](https://github.com/gundotio/worf/compare/v0.4.8...v0.4.9) (2021-11-17)

- Switch back to standard request dicts on POST; allows views to access `request.POST`/`request.FILES` later after bundle loading

### [0.4.8](https://github.com/gundotio/worf/compare/v0.4.7...v0.4.8) (2021-11-17)

- Support negated filters [django-url-filter#features](https://github.com/miki725/django-url-filter#features)

### [0.4.7](https://github.com/gundotio/worf/compare/v0.4.6...v0.4.7) (2021-11-17)

- Assign fk/m2m on create and support delete [#74](https://github.com/gundotio/worf/pull/74)
- Marshmallow serialization [#75](https://github.com/gundotio/worf/pull/75)
- File upload support [#76](https://github.com/gundotio/worf/pull/76)
- Switch out some `snake_to_camel` usage for a keymap [#72](https://github.com/gundotio/worf/pull/72)

### [0.4.6](https://github.com/gundotio/worf/compare/v0.4.5...v0.4.6) (2021-11-09)

- Support string list filters [#69](https://github.com/gundotio/worf/pull/69)
- Remove unused `get_instance_or_http404`
- Test for `get_version` shortcut

### [0.4.5](https://github.com/gundotio/worf/compare/v0.4.4...v0.4.5) (2021-11-08)

- Support annotation filters without the need for a custom filterset [#70](https://github.com/gundotio/worf/pull/70)

### [0.4.4](https://github.com/gundotio/worf/compare/v0.4.3...v0.4.4) (2021-11-08)

- Bugfix for empty queryset handling [#71](https://github.com/gundotio/worf/pull/71)

### [0.4.3](https://github.com/gundotio/worf/compare/v0.4.2...v0.4.3) (2021-11-05)

- Support annotation filters for more flexible query param filters [#66](https://github.com/gundotio/worf/pull/66)
- Support custom queryset on detail views [#68](https://github.com/gundotio/worf/pull/68)
- Switch search fields to `list` and deprecate `dict` syntax [#63](https://github.com/gundotio/worf/pull/63)
- Lint script [#65](https://github.com/gundotio/worf/pull/65)
- Reorganize tests [#67](https://github.com/gundotio/worf/pull/67)

### [0.4.2](https://github.com/gundotio/worf/compare/v0.4.1...v0.4.2) (2021-10-25)

- Adds support for `fields` query parameter
- Adds support for perPage query parameter
- All strings are stripped

### [0.4.1](https://github.com/gundotio/worf/compare/v0.4.0...v0.4.1) (2021-10-20)

- Fixes an issue where fields that support null will error when given a null value

## [0.4.0](https://github.com/gundotio/worf/compare/v0.3.6...v0.4.0) (2021-10-07)

- Introduces support for setting M2M through models
- Removes testing module

### [0.3.7](https://github.com/gundotio/worf/compare/v0.3.6...v0.3.7) (2021-09-16)

- Add create/update hooks into List/Detail views
- Strip `strip_tags` from bundle processing

### [0.3.6](https://github.com/gundotio/worf/compare/v0.3.5...v0.3.6) (2021-08-14)

- Support assigning null to foreign keys
- Adds tests

### [0.3.5](https://github.com/gundotio/worf/compare/v0.3.4...v0.3.5) (2021-08-13)

- Really do everything from 0.3.3-now :|

### [0.3.4](https://github.com/gundotio/worf/compare/v0.3.3...v0.3.4) (2021-08-13)

- Really restores support for filtering with querystring arrays
- Adds a PR tempalte
- Requires coverage
- Support Foreign Key Assignment

### [0.3.3](https://github.com/gundotio/worf/compare/v0.3.2...v0.3.3) (2021-08-12)

- Restores support for filtering with querystring arrays such as `?this=that&this=this`
- Adds automagic support for ManyToManyField assignemnts
- Adds support for UUID url paths

### [0.3.2](https://github.com/gundotio/worf/compare/v0.3.1...v0.3.2) (2021-07-29)

- Adds multisort support via passing multiple `sort` query parameters

### [0.3.1](https://github.com/gundotio/worf/compare/v0.3.0...v0.3.1) (2021-07-20)

- Adds `django-url-filters` as a dependency
- Adds support for filtering using `__` model syntax

## [0.3.0](https://github.com/gundotio/worf/compare/v0.2.10...v0.3.0) (2021-07-20)

- Adds verify_serializer_interface testing method for generating serializer tests

### Breaking Changes
- Removes generate_endpoint_tests test generator
- Relocates testing.deserialize method to serializers.deserialize

### [0.2.10](https://github.com/gundotio/worf/compare/v0.2.9...v0.2.10) (2021-07-20)

- Removes package dependencies from dev env Pipfile
- Improves codeowners, binstubs, pytest settings

### [0.2.9](https://github.com/gundotio/worf/compare/v0.2.8...v0.2.9) (2021-07-15)

- Adds HTTP409 exception

### [0.2.8](https://github.com/gundotio/worf/compare/v0.2.7...v0.2.8) (2021-07-14)

- Adds validation for datetime fields

### [0.2.7](https://github.com/gundotio/worf/compare/v0.2.6...v0.2.7) (2021-06-25)

- Trim string input unless the field is in `secure_fields`

### [0.2.6](https://github.com/gundotio/worf/compare/v0.2.5...v0.2.6) (2021-06-08)

- Adds `queryset` to ListAPI that allows setting a custom queryset
- Adds `filter_fields` querystring param allowlist to ListAPI
- Update deps for dev container

### [0.2.5](https://github.com/gundotio/worf/compare/v0.2.4...v0.2.5) (2021-05-28)

- Deprecates ChoicesAPI
- Adds override option to test factory

### [0.2.4](https://github.com/gundotio/worf/compare/v0.2.1...v0.2.4) (2021-05-14)

- Raises validation error on email = None

### [0.2.3](https://github.com/gundotio/worf/compare/v0.2.2...v0.2.3) (2021-05-07)

- Allows either `p` or `page` as param for pagination

### [0.2.2](https://github.com/gundotio/worf/compare/v0.2.1...v0.2.2) (2021-05-06)

- Removes `update_fields` from the `save()` method called by detail API.

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
