/**
 * DureeSlider — curseur 1-180 min pour le temps de parole (PlanPage,
 * RapportCompletPage). Le dégradé de remplissage suit la valeur via une
 * variable CSS calculée en JS, pas de librairie de slider.
 */

interface DureeSliderProps {
  valeur: number;
  onChange: (valeur: number) => void;
  min?: number;
  max?: number;
  id?: string;
}

export default function DureeSlider({ valeur, onChange, min = 1, max = 180, id = "duree-slider" }: DureeSliderProps) {
  const pourcentage = ((valeur - min) / (max - min)) * 100;

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <label htmlFor={id} className="text-sm text-warmgray">
          Temps de parole imparti
        </label>
        <span className="font-mono text-lg font-semibold text-amethyst-400">{valeur} min</span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        value={valeur}
        onChange={(e) => onChange(Number(e.target.value))}
        className="range-slider"
        style={{
          background: `linear-gradient(to right, rgb(var(--color-amethyst-400)) ${pourcentage}%, rgb(var(--color-surface-3)) ${pourcentage}%)`,
        }}
      />
      <div className="mt-1 flex justify-between text-xs text-muted">
        <span>{min} min</span>
        <span>{max} min</span>
      </div>
    </div>
  );
}
