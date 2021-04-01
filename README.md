Worf
=========================

![CI](https://github.com/gundotio/worf/workflows/CI/badge.svg)

**A more Djangonic approach to Django REST APIs.**

[![Worf](https://i.kym-cdn.com/photos/images/newsfeed/001/231/196/e18.jpg)][worf-docs]

Full documentation for the project is available at [https://memory-alpha.fandom.com/wiki/Worf][worf-docs].

[worf-docs]: https://memory-alpha.fandom.com/wiki/Worf


### Overview

Worf is a small Django API framework that lets you quickly build out an api using
simple model methods. Contributions welcome.

This project is stable but will change drastically.

### Roadmap

- Abstracting serializers away from model methods
- More support for different HTTP methods
- Support for user-generated validators
- Better file upload support
- Better test coverage
- Browsable API docs

#### API Method

Views execute the `api_method` in order to return data.

Example API Method:

```py
def api(self):
  return [
    'camelCaseField': self.camel_case_field,
    ...
  ]
```
#### Serializer

Views append `_update_fields` to the `api_method` property. This model method will
be executed on `PATCH` requests. `PATCH` requests are supported in `DetailUpdateAPI`.
If you do not want to support `PATCH` on a particular endpoint, use `DetailAPI`.

Only fields included in the serializer method will be used to `PATCH` models.

If a `PATCH` request is made with fields that are not in the serializer, the
response will be `HTTP 400`.

Example Serializer:

```py
def api_update_fields(self):
  return [
    'field_for_update_1',
    'field_for_update_2'
    ...
  ]
```

### Example

The following example provides you with an api that does the following:

- Only allows authenticated users to access the endpoints
- Provides a list of books, with `POST` support to create a new book
- Provides an endpoint for each book's detail endpoint, with `PATCH` support

A more complete example will demonstrate the additional built-in capabilities,
including search, pagination, ordering, and the other things Worf can do.

#### Model Example

```py
class Book(models.Model):
    title = models.CharField(max_length=128)
    author_name = models.CharField(max_length=128)
    published_at = models.DateField()

    def api_update_fields(self):
        return [
            "title",
            "author_name",
        ]

    def api(self):
        return dict(
            title=self.title,
            authorName=self.author_name,
            published_at=self.published_at,
        )
```

#### View Book Example

```py
from worf.views import ListAPI, DetailPatchAPI

class BookList(ListCreateAPI):
  permissions = [Authenticated]
  model = Book

class BookDetail(DetailPatchAPI):
  permissions = [Authenticated]
  model = Book
```

### URLs

```py
...
path("api/v1/", include([
      path("books/", BookList.as_view()),
      path("books/<int:id>/", BookDetail.as_view()),
  ])
),
...
```

## View Reference

### `worf.permissions`

Permissions functions. These functions extend the API View, so they require
`self` to be defined as a parameter. This is done in order to allow access to
`self.request` during permission testing.

If permissions should be granted, functions should return `int(200)`.

If permissions fail, they should return an `HTTPExcption`

### `worf.validators`

Provides `ValidationMixin` which `AbstractBaseAPI` inherits from. Will perform
some coercion on `self.bundle`, potentially resulting in a different bundle than
what was originally passed to the view.

### `worf.views`

#### `AbstractBaseAPI`

Provides the basic functionality of both BaseList and BaseDetail APIs. It is not
recommended to use this abstract view directly.

Class Attributes

|name | required | type | description |
| -- | -- | -- | -- |
|`bundle_name` | no | `str` | _Default:_ `None` If set, the returned data will use this name. I.e., {`bundle_name`: return_data}|
|`model`| yes | `class` | An uninstantiated `django.db.models.model` class.  |
|`permissions`| yes | `list` of permissions classes | Will return appropriate HTTP status code based on the definition of the permission class.
|   |   |   |   |

##### HTTP Methods
- GET is always supported.


#### `ListAPI`

|name | required | type | description |
| -- | -- | -- | -- |
|`api_method`   | no | `str`  | _Default:_ `api`. Must refer to a `model` method. This method is used to return data for `GET` requests. |
|`payload_key`   | no  | `str`  | _Default:_ `model._meta.verbose_name_plural`. Use in order to rename the key for the results array |
|`filters`      | no  | `dict` | _Default:_ `{}`. Pass key/value pairs that you wish to further filter the queryset beyond the `lookup_url_kwarg` |
|`lookup_field` | no | `str` | Use these two settings in tandem in order to filter `get_queryset` based on a URL field. `lookup_url_kwarg` is required if this is set. |
|`lookup_url_kwarg`| no | `str` | Use these two settings in tandem in order to filter `get_queryset` based on a URL field. `lookup_field` is required if this is set.  |
|`ordering`     | no | `list` | _Default_: `[]`. Pass a list of valid fields to order the queryset by.  |
|`search_fields`   | no | `dict` or `bool` | _Default_: `False`.  |
|`results_per_page`  | no  | `int` | _Default_: 25. Sets the number of results returned for each page. |
|   |   |   |   |

##### Search
Setting `search_fields` to `True` will enable search based on url parameters.
Parameters in the URL must be camelCase and exactly match the snake_case model
field.

To allow full text search, set to a dictionary of two lists: 'or' & 'and'. Each
list will be assembled using either `Q.OR` or `Q.AND`. Fields in each list
must be composed of django filter lookup argument names.

##### Pagination

All ListAPI views are paginated and include a `pagination` json object.

Use `results_per_page` to set custom limit for pagination. Default 25.

##### `get_queryset()` method
This method will use `lookup_url_kwarg` and `lookup_field` to filter results.
You _should_ not need to override get_queryset. Instead, set the optional variables
listed above to configure the queryset.

##### Return
1. A list of the `ListAPI.{model}.{instance}.api()` method by default.
2. If `lookup_field` and `lookup_url_kwarg` fields are set, it will return a filtered list.

```py
{
  model_verbose_name: [
    instance1.api(),
    ...
  ]
}
```

#### `ListCreateAPI`

Adds `post` method to handle creation. Otherwise identical to `ListAPI`. In most
cases, you will need to override the post method in order to create objects
properly. Do this by performing whatever logic you need to do, then update the
`self.bundle` with whatever properties you need to set on the object. Then call
`return super().post(request, *args, **kwargs)`.

#### `DetailAPI`

|name | default | type | description |
| -- | -- | -- | -- |
|`api_method` | `api` | `str`  | Must refer to a `model` method. This method is used to return data for `GET` requests. Additionally, `{api_method}_update_fields` will be called to execute `PATCH` requests.|
|`lookup_field`| `id` | `str` | Override with the lookup field used to filter the _model_. Defaults to `id`|
|`lookup_url_kwarg`| `id` | `str` | Override with the name of the parameter passed to the view by the URL route. Defaults to `id`  |
|   |   |   |   |

##### `get_instance()` method
This method uses `lookup_field` and `lookup_url_kwargs` to return a model instance.

You _may_ prefer to override this method, for example in a case when you are using
request.user to return an instance.

#### `DetailUpdateAPI`

Adds `patch` method to handle updates. Otherwise identical to `DetailAPI`. Runs
validators automatically. You _should_ not need to override update. If the
`api_update_fields` model method returns an empty list, HTTP 422 will be raised.


### Additional Information

#### Converting 🐍 & 🐪
Worf expects all your model fields to be defined in snake case, and your api's json objects to be camel case. This conversion is handled in `worf.casing`.

**Limitations With Casing***
We interpret camelCase, _strictly_, based on the database model. This means that
inappropriate naming of database fields will result in confusion. A quick example:

```py
# profiles.models.freelancers.Freelancer
freelance_fulltime = models.CharField(...)
freelancer_id = UUIDField(...)
API_strict = ...
```
This will be strictly translated by the API. Acronyms are not considered:

- `freelance_fulltime == freelaneFulltime`
- `freelancer_id == freelancerId`
- `API_strict == apiStrict`

At this time, we still manually define the `camelCase` names in the model `api()`
method. This will eventually be removed in favor of automated case conversion,
but it has and will continue to present an opportunity for error, for now.

#### `self.bundle` is loaded from json

The `dispatch` method is run by Django when the view is called. In our version
of dispatch, we interpret any `request.body` as JSON, and convert all values
from camel to snake case at that time. You'll always be able to access bundle
attributes by their snake case variable name, and these attributes will exactly
match the model fields.

`self.bundle` is set on a class level, it is available to all methods inside
the view. We perform type coercion during validation, so `self.bundle` will
be changed during processing. You may also append or remove attributes to the
bundle before saving the object via `post`, `patch`, or other methods.

#### Naming Things

We refer to the json object that is sent and received by the api differently in this codebase for clarity:

- `bundle` is what we send to the backend.
- `payload` is what the backend returns.
