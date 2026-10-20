const SORTER = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

/** Prepare exact saved suggestions and derived search text once per supplied vocabulary. */
export function prepareWorkMediumSuggestions(values) {
  return values.map(value => ({ value, search: value.toLocaleLowerCase("en") }))
    .sort((left, right) => SORTER.compare(left.value, right.value)
      || (left.value < right.value ? -1 : left.value > right.value ? 1 : 0));
}

/** Match locally after two query characters without changing authored suggestion text. */
export function matchingWorkMediumSuggestions(suggestions, query) {
  const search = query.trim().toLocaleLowerCase("en");
  return search.length < 2 ? [] : suggestions.filter(suggestion => suggestion.search.includes(search));
}
