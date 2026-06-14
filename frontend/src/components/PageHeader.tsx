export function PageHeader({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <header className="page-header">
      <span>{eyebrow}</span>
      <h1>{title}</h1>
    </header>
  );
}
