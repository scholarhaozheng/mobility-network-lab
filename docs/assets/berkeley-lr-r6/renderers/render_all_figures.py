"""Reproduce the five selected Berkeley LR figure families from packaged inputs."""
from pathlib import Path
import render_lr_diagnostics as diagnostics
import render_lr_flow

def main():
    here = Path(__file__).resolve().parent
    root = here.parent if here.name == 'renderers' else here
    data = diagnostics.normalize_input(root / 'inputs/lr_diagnostic.json')
    output = root / 'regenerated'
    records = diagnostics.render_all(data, output)
    records.append(render_lr_flow.render(data, root / 'inputs/physical_flows.csv',
                                        root / 'inputs/physical_geometry.csv', output))
    print(f'Reproduced {len(records)} figure families in {output}')

if __name__ == '__main__':
    main()
