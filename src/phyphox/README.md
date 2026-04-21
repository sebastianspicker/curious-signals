# phyphox sources

The importable `experiments/*.phyphox` files are generated from `src/phyphox/*.phyphox.xml`.

The source files use **XInclude** to share common XML snippets (e.g. data container definitions and BLE channel mapping) stored in `src/phyphox/includes/`. The phyphox format does not support fragment includes for parts of elements (e.g. single graph attributes or translation strings), so repeated view/graph attributes and translations remain in each experiment file. Further deduplication would require a custom template or preprocessor; the current XInclude-based approach is the standard for this repo.

## Credits and licence

- Original authors: Gautier Creutzer and Frédéric Bouquet, La Physique Autrement, Laboratoire de Physique des Solides, Université Paris-Saclay. Other projects: www.physicsreimagined.com
- Changes in v1.1 & v1.2: Sebastian J. Spicker and Frédéric Bouquet (German translation, units/views/axis labeling, consistency with original phyphox experiments).
- Usage: English/French www.physicsreimagined.com (look for "nano"); German https://astro-lab.app/arduino-und-phyphox/
- Based on the phyphox Arduino library (phyphox team, RWTH Aachen University), GNU Lesser General Public Licence v3.0 (or newer). This work is released under the same licence.

## Rebuild

```sh
bash scripts/build-phyphox.sh
```

CI validates that the generated `experiments/*.phyphox` files match these sources.
