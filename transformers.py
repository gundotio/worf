def transform_to_dict(choices):
    """Convert various choices list of lists into json object."""
    # TODO this is copied from context_processors.
    transformed_choices = dict()
    for each in choices:
        transformed_choices[each[0]] = each[1]
    return transformed_choices
