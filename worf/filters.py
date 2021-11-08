from urllib.parse import urlencode

from django.db.models.fields.related import ForeignObjectRel, RelatedField
from django.http import QueryDict

from url_filter.filtersets import ModelFilterSet
from url_filter.exceptions import SkipFilter


class AnnotatedModelFilterSet(ModelFilterSet):
    def get_filters(self):
        filters = super().get_filters()

        if self.queryset is not None:
            state = self._build_state()

            for name in self.queryset.query.annotations.keys():
                if name in self.Meta.exclude or name in filters:
                    continue

                try:
                    annotation_filter = self._build_annotation_filter(name, state)
                except SkipFilter:
                    continue

                if annotation_filter is not None:
                    filters[name] = annotation_filter

        return filters

    def _build_annotation_filter(self, name, state):
        field = self.queryset.query.annotations.get(name).output_field

        if isinstance(field, RelatedField):
            if not self.Meta.allow_related:
                raise SkipFilter
            return self._build_filterset_from_related_field(name, field)
        elif isinstance(field, ForeignObjectRel):
            if not self.Meta.allow_related_reverse:
                raise SkipFilter
            return self._build_filterset_from_reverse_field(name, field)

        return self._build_filter_from_field(name, field)


def generate_filterset(model, queryset):
    return type(
        f"{model.__name__}FilterSet",
        (AnnotatedModelFilterSet,),
        dict(Meta=type("Meta", (), dict(model=model, queryset=queryset))),
    )


def apply_filterset(filter_set, queryset, lookup_kwargs):
    data = QueryDict(urlencode(lookup_kwargs, True))

    return filter_set(data=data, queryset=queryset).filter()
