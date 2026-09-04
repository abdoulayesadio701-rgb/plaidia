/**
 * Tabs — onglets simples sur les classes .tabs-list/.tab/.tab-active de
 * globals.css. Contrôlé par le parent (pas de state interne) pour que
 * RapportCompletPage puisse, par exemple, présélectionner un onglet.
 */

interface TabDef {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: TabDef[];
  actif: string;
  onChange: (id: string) => void;
}

export default function Tabs({ tabs, actif, onChange }: TabsProps) {
  return (
    <div className="tabs-list" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={actif === tab.id}
          className={actif === tab.id ? "tab-active" : "tab"}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
