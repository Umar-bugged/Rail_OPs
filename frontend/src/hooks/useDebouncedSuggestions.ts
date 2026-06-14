import { useEffect, useState } from "react";

export function useDebouncedSuggestions<T>(
  query: string,
  loader: (query: string) => Promise<T[]>,
  minLength = 2,
  delayMs = 220
) {
  const [suggestions, setSuggestions] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < minLength) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    let active = true;
    const timeout = window.setTimeout(() => {
      setIsLoading(true);
      loader(trimmed)
        .then((items) => {
          if (active) {
            setSuggestions(items);
          }
        })
        .finally(() => {
          if (active) {
            setIsLoading(false);
          }
        });
    }, delayMs);

    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [query, loader, minLength, delayMs]);

  return { suggestions, isLoading, setSuggestions };
}
