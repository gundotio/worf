from urllib.parse import urlencode

from django.http import QueryDict

from url_filter.filtersets import ModelFilterSet


def generate_filterset(model):
    return type(
        f"{model.__name__}FilterSet",
        (ModelFilterSet,),
        dict(Meta=type("Meta", (), dict(model=model))),
    )


def apply_filterset(filter_set, queryset, lookup_kwargs):
    data = QueryDict(urlencode(lookup_kwargs))

    return filter_set(data=data, queryset=queryset).filter()
