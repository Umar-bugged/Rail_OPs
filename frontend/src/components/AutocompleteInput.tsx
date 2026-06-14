import { ReactNode, useState } from "react";

export type AutocompleteOption = {
  id: string;
  value: string;
  title: string;
  meta?: string;
  detail?: string;
};

export function AutocompleteInput({
  label,
  value,
  onChange,
  options,
  onSelect,
  placeholder,
  inputMode,
  maxLength,
  isLoading = false,
  emptyText = "No matches",
  aside
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: AutocompleteOption[];
  onSelect: (option: AutocompleteOption) => void;
  placeholder?: string;
  inputMode?: "text" | "numeric" | "decimal";
  maxLength?: number;
  isLoading?: boolean;
  emptyText?: string;
  aside?: ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const showSuggestions = isOpen && value.trim().length >= 2;

  return (
    <label className="autocomplete-field">
      <span className="field-label">
        {label}
        {aside}
      </span>
      <input
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => window.setTimeout(() => setIsOpen(false), 140)}
        placeholder={placeholder}
        inputMode={inputMode}
        maxLength={maxLength}
        autoComplete="off"
      />
      {showSuggestions && (
        <div className="suggestion-menu" role="listbox">
          {isLoading && <div className="suggestion-status">Searching</div>}
          {!isLoading && options.length === 0 && <div className="suggestion-status">{emptyText}</div>}
          {!isLoading &&
            options.map((option) => (
              <button
                className="suggestion-option"
                key={option.id}
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onSelect(option);
                  setIsOpen(false);
                }}
              >
                <strong>{option.title}</strong>
                {option.meta && <span>{option.meta}</span>}
                {option.detail && <em>{option.detail}</em>}
              </button>
            ))}
        </div>
      )}
    </label>
  );
}
