Worf
====

[![build-status-image]][build-status]
[![pypi-version]][pypi]

Worf is a small Django API framework for building out REST APIs simply using
class-based views and serializers.

[![Worf](https://i.kym-cdn.com/photos/images/newsfeed/001/231/196/e18.jpg)][worf-docs]

Full documentation for the project is available at [https://memory-alpha.fandom.com/wiki/Worf][worf-docs].

[worf-docs]: https://memory-alpha.fandom.com/wiki/Worf


Table of contents
-----------------

  - [Installation](#installation)
  - [Requirements](#requirements)
  - [Roadmap](#roadmap)
  - [Usage](#usage)
  - [Serializers](#serializers)
  - [Permissions](#permissions)
  - [Validators](#validators)
  - [Views](#views)
    - [ListAPI](#listapi)
    - [DetailAPI](#detailapi)
    - [CreateAPI](#createapi)
    - [UpdateAPI](#updateapi)
  - [Browsable API](#browsable-api)
  - [Bundle loading](#bundle-loading)
  - [Field casing](#field-casing)
  - [File uploads](#file-uploads)
  - [Internal naming](#internal-naming)
  - [Credits](#credits)


Installation
------------

Install using pip:

```sh
pip install worf
```

Add `worf` to your `INSTALLED_APPS` setting:

```py
INSTALLED_APPS = [
    ...
    "worf",
]
```


Requirements
------------

- Python (3.7, 3.8, 3.9)
- Django (3.0, 3.1, 3.2)


Roadmap
-------

- [x] Abstracting serializers away from model methods
- [x] Browsable API
- [x] Declarative marshmallow-based serialization
- [x] File upload support
- [x] Support for PATCH/PUT methods
- [ ] Better test coverage
- [ ] Documentation generation
- [ ] Support for user-generated validators


Usage
-----

The following examples provides you with an API that does the following:

- Only allows authenticated users to access the endpoints
- Provides a list of books, with `POST` support to create a new book
- Provides an endpoint for each book's detail endpoint, with `PATCH` support

A more complete example will demonstrate the additional built-in capabilities,
including search, pagination, ordering, and the other things Worf can do.

```py
# models.py
class Book(models.Model):
    title = models.CharField(max_length=128)
    author_name = models.CharField(max_length=128)
    published_at = models.DateField()
```

```py
# serializers.py
from worf.serializers import Serializer

class BookSerializer(Serializer):
    class Meta:
        fields = [
            "id",
            "title",
            "author_name",
            "published_at",
        ]
```

```py
# views.py
from worf.permissions import Authenticated
from worf.views import DetailAPI, ListAPI, UpdateAPI

class BookList(CreateAPI, ListAPI):
  model = Book
  serializer = BookSerializer
  permissions = [Authenticated]

class BookDetail(UpdateAPI, DetailAPI):
  model = Book
  serializer = BookSerializer
  permissions = [Authenticated]
```

```py
# urls.py
path("api/", include([
    path("books/", BookList.as_view()),
    path("books/<int:id>/", BookDetail.as_view()),
])),
```

Serializers
-----------

Worf serializers are basically [marshmallow schemas](https://marshmallow.readthedocs.io/)
with some tweaks to improve support for Django models, and supply extra defaults.

```py
from worf.serializers import fields, Serializer

class BookSerializer(Serializer):
    author = fields.Nested(AuthorSerializer)
    tags = fields.Nested(TagSerializer, many=True)

    class Meta:
        fields = [
            "id",
            "title",
            "content",
            "image",
            "url",
            "author",
            "tags",
        ]
```

Worf serializers build on top of marshmallow to make them a little easier to use
in Django, primarily, we add support for using the `Nested` field with related
managers, and setting default serializer options via settings:

```py
WORF_SERIALIZER_DEFAULT_OPTIONS = {
    "dump_only": [
        "id",
        "created_at",
        "deleted_at",
        "updated_at",
    ]
}
```

Permissions
-----------

Permissions functions can be found in `worf.permissions`.

These functions extend the API View, so they require `self` to be defined as a
parameter. This is done in order to allow access to `self.request` during
permission testing.

If permissions should be granted, functions should return `int(200)`.

If permissions fail, they should return an `HTTPException`


Validators
-----------

Validation handling can be found in `worf.validators`.

The basics come from `ValidationMixin` which `AbstractBaseAPI` inherits from, it
performs some coercion on `self.bundle`, potentially resulting in a different
bundle than what was originally passed to the view.


Views
-----

### AbstractBaseAPI

Provides the basic functionality of both List and Detail APIs.
It is not recommended to use this abstract view directly.

| Name | Type | Default | Description |
| -- | -- | -- | -- |
| model       | class | None | An uninstantiated `django.db.models.model` class. |
| permissions | list  | []   | Pass a list of permissions classes. |


### ListAPI

| Name | Type | Default | Description |
| -- | -- | -- | -- |
| filters           | dict | {}                  | Pass key/value pairs that you wish to further filter the queryset beyond the `lookup_url_kwarg` |
| lookup_field      | str  | None                | Use these two settings in tandem in order to filter `get_queryset` based on a URL field. `lookup_url_kwarg` is required if this is set. |
| lookup_url_kwarg  | str  | None                | Use these two settings in tandem in order to filter `get_queryset` based on a URL field. `lookup_field` is required if this is set. |
| payload_key       | str  | verbose_name_plural | Use in order to rename the key for the results array |
| ordering          | list | []                  | Pass a list of fields to default the queryset order by. |
| filter_fields     | list | []                  | Pass a list of fields to support filtering via query params. |
| search_fields     | list | []                  | Pass a list of fields to full text search via the `q` query param. |
| sort_fields       | list | []                  | Pass a list of fields to support sorting via the `sort` query param. |
| per_page          | int  | 25                  | Sets the number of results returned for each page. |
| max_per_page      | int  | per_page            | Sets the max number of results to allow when passing the `perPage` query param. |

The `get_queryset` method will use `lookup_url_kwarg` and `lookup_field` to filter results.
You _should_ not need to override get_queryset. Instead, set the optional variables
listed above to configure the queryset.

#### Filtering

Parameters in the URL must be camelCase and exactly match the snake_case model field.

To allow full text search, set to a list of fields for django filter lookups.

For a full list of supported lookups see https://django-url-filter.readthedocs.io.

#### Pagination

All ListAPI views are paginated and include a `pagination` json object.

Use `per_page` to set custom limit for pagination. Default 25.

### DetailAPI

| Name | Type | Default | Description |
| -- | -- | -- | -- |
| lookup_field     | str | id  | Override with the lookup field used to filter the _model_. Defaults to `id`|
| lookup_url_kwarg | str | id  | Override with the name of the parameter passed to the view by the URL route. Defaults to `id`  |

This `get_instance()` method uses `lookup_field` and `lookup_url_kwargs` to return a model instance.

You _may_ prefer to override this method, for example in a case when you are using
`request.user` to return an instance.

### CreateAPI

Adds a `post` method to handle creation, mix this into a `ListAPI` view:

```py
class BookListAPI(CreateAPI, ListAPI):
    model = Book
    serializer = BookSerializer
```

Validation of creates is kind of sketchy right now, but the idea is that you'd
use the same serializer as you would for an update, unless you have `create-only`
fields, in which case, you may want to create a `BookCreateSerializer`.

### UpdateAPI

Adds `patch` and `put` methods to handle updates, mix this into a `DetailAPI`.

```py
class BookDetailAPI(UpdateAPI, DetailAPI):
    model = Book
    serializer = BookSerializer
```

Validation of update fields is delegated to the serializer, any fields that are
writeable should be within the `fields` definition of the serializer, and not
marked as `dump_only` (read-only).


Browsable API
-------------

Similar to other popular REST frameworks; Worf exposes a browsable API which adds
syntax highlighting, linkified URLs and supports Django Debug Toolbar.

### Format

To override the default browser behaviour pass `?format=json`.

### Theme

The theme is built with [Tailwind](https://tailwindcss.com/), making it easy to customize the look-and-feel.

For quick and easy branding, there are a couple of Django settings that tweak the navbar:

| Name          | Default  |
| ------------- | -------- |
| WORF_API_NAME | Worf API |
| WORF_API_ROOT | /api/    |

To customize the markup create a template called `worf/api.html` that extends from `worf/base.html`:

```django
# templates/worf/api.html
{% extends "worf/base.html" %}

{% block branding %}
    {{ block.super }}
    <div>A warrior's drink!</div>
{% endblock %}
```

All of the blocks available in the base template can be used in your `api.html`.

| Name     | Description                     |
| -------- | ------------------------------- |
| body     | The entire html `<body>`.       |
| branding | Branding section of the navbar. |
| script   | JavaScript files for the page.  |
| style    | CSS stylesheets for the page.   |
| title    | Title of the page.              |

For more advanced customization you can choose not to have `api.html` extend `base.html`.


Bundle loading
--------------

The `dispatch` method is run by Django when the view is called. In our version
of dispatch, we interpret any `request.body` as JSON, and convert all values
from camel to snake case at that time. You'll always be able to access bundle
attributes by their snake case variable name, and these attributes will exactly
match the model fields.

`self.bundle` is set on a class level, it is available to all methods inside
the view. We perform type coercion during validation, so `self.bundle` will
be changed during processing. You may also append or remove attributes to the
bundle before saving the object via `post`, `patch`, or other methods.


Field casing
------------

Worf expects all your model fields to be defined in snake case 🐍, and JSON
objects to be camel case 🐪 and that conversion is handled in `worf.casing`.

We interpret camelCase, _strictly_, based on the database model. This means that
inappropriate naming of database fields will result in confusion.

A quick example:

```py
freelance_fulltime = models.CharField(...)
freelancer_id = models.UUIDField(...)
API_strict = ...
```

This will be strictly translated by the API, and acronyms are not considered:

- `freelance_fulltime == freelanceFulltime`
- `freelancer_id == freelancerId`
- `API_strict == apiStrict`


File uploads
------------

File uploads are supported via `multipart/form-data` requests.


Internal naming
---------------

We refer to the json object that is sent and received by the API differently in
this codebase for clarity:

- `bundle` is what we send to the backend.
- `payload` is what the backend returns.


Credits
-------

~Wanted dead or alive~ Made with 🥃 at [Gun.io][gun.io]

<a href="https://github.com/gundotio/worf/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=gundotio/worf" alt="Contributors"/>
</a>

[build-status-image]: https://github.com/gundotio/worf/actions/workflows/ci.yml/badge.svg
[build-status]: https://github.com/gundotio/worf/actions/workflows/ci.yml
[gun.io]: https://www.gun.io
[pypi-version]: https://img.shields.io/pypi/v/worf.svg?color=blue
[pypi]: https://pypi.org/project/worf/
